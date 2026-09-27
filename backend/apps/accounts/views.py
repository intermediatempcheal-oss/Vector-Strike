"""Vector Strike Phase 7 API views — onboarding, accounts, identity and auth.

Authentication is token-based: short-lived JWT access tokens (Bearer header)
plus longer-lived rotating refresh tokens stored in an HttpOnly cookie and
blacklisted on logout/rotation. Django sessions remain as a convenience for
admin tooling and are never required by the app.
"""

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts import authservices, services
from apps.accounts.constants import (
    AGE_RANGES,
    ConsentMethod,
    ConsentStatus,
    GuardianStatus,
    OneTimeTokenPurpose,
    UploadStatus,
    VerificationProvider,
    VerificationStatus,
)
from apps.accounts.models import (
    GuardianRelationship,
    IdentityDocumentUpload,
    OnboardingProgress,
    User,
    Verification,
)
from apps.accounts.recommendations import first_experience_recommendations
from apps.accounts.serializers import (
    AgeCheckSerializer,
    EmailVerifySerializer,
    GuardianSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PhoneConfirmSerializer,
    PhoneRequestSerializer,
    RegisterSerializer,
    UserIdentitySerializer,
    UsernameCheckSerializer,
    login_allowed_error,
)
from apps.profiles.models import Interest, PlayStyle, Profile, UserInterest, UserPlayStyle
from apps.profiles.serializers import InterestSerializer, PlayStyleSerializer

ALLOWED_DOCUMENT_TYPES = {
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
    "pdf": b"%PDF",
}


def _region_config_payload():
    config = settings.AGE_VERIFICATION_REGION_CONFIG
    return {
        region: {
            "required": bool(cfg.get("required", False)) and bool(cfg.get("min_age")),
            "min_age": cfg.get("min_age", settings.VERIFICATION_AGE_THRESHOLD),
            "methods": cfg.get("methods", []),
        }
        for region, cfg in config.items()
    }


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def _user_identity_payload(user):
    serializer = UserIdentitySerializer(user, context={"request": None})
    return serializer.data


def _apply_throttle(request, scope):
    throttle = ScopedRateThrottle()
    throttle.scope = scope
    throttle.allow_request(request, None)


# ---------------------------------------------------------------------------
# JWT helpers — access in response body, refresh in HttpOnly cookie.
# ---------------------------------------------------------------------------
def _refresh_cookie_kwargs():
    lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
    return {
        "httponly": True,
        "secure": not settings.DEBUG,
        "samesite": "Lax",
        "path": settings.JWT_REFRESH_COOKIE_PATH,
        "max_age": int(lifetime.total_seconds()),
    }


def _issue_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def _attach_refresh_cookie(response, user):
    access, refresh = _issue_tokens_for_user(user)
    response.set_cookie(settings.JWT_REFRESH_COOKIE, refresh, **_refresh_cookie_kwargs())
    return access


def _detach_refresh_cookie(response):
    response.delete_cookie(settings.JWT_REFRESH_COOKIE, path=settings.JWT_REFRESH_COOKIE_PATH)


def _resolve_user_by_identifier(identifier):
    if not identifier:
        return None
    upper = str(identifier).strip().upper()
    if "@" in identifier:
        return User.objects.filter(email__iexact=identifier.strip().lower()).first()
    if upper.startswith("VS-"):
        return User.objects.filter(vector_id__iexact=upper).first()
    return User.objects.filter(username__iexact=identifier.strip()).first()


def _issue_email_verification(user):
    """Issue + deliver a verification token, never failing the caller.

    E-mail transport problems must not brick registration or login.
    """
    try:
        raw, _token = authservices.issue_one_time_token(
            user, OneTimeTokenPurpose.EMAIL_VERIFICATION
        )
        authservices.send_email_verification(user, raw)
    except Exception:  # pragma: no cover - transport failures are environmental
        import logging

        logging.getLogger("vector_strike.security").exception(
            "Failed to send email verification for %s", user.email
        )


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def csrf_view(request):
    return Response({"csrfToken": get_token(request)})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def session_view(request):
    user = request.user
    if user.is_authenticated:
        return Response(
            {
                "authenticated": True,
                "onboarding_complete": bool(user.onboarding_completed),
                "user": _user_identity_payload(user),
            }
        )
    return Response({"authenticated": False, "onboarding_complete": False, "user": None})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def login_view(request):
    _apply_throttle(request, "login")
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]

    # Django session stays available for admin/dev tooling.
    login(request, user)
    user.last_login = timezone.now()
    user.save(update_fields=["last_login", "updated_at"])

    response = Response(
        {
            "authenticated": True,
            "onboarding_complete": bool(user.onboarding_completed),
            "user": _user_identity_payload(user),
        }
    )
    response.data["access"] = _attach_refresh_cookie(response, user)
    return response


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def token_refresh_view(request):
    """Rotate the refresh token and return a fresh access token.

    The previous refresh token is blacklisted (when rotation is enabled), so a
    stolen token can only be used once. Accepts the token from the HttpOnly
    cookie or from a JSON ``refresh`` field for API clients without cookies.
    """
    body = request.data if isinstance(request.data, dict) else {}
    raw = body.get("refresh") or request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
    if not raw:
        raise AuthenticationFailed("Your session has expired. Please sign in again.")

    try:
        refresh = RefreshToken(raw)
        refresh.verify()
        refresh.check_blacklist()
    except TokenError:
        raise AuthenticationFailed("Your session has expired. Please sign in again.")

    user = User.objects.filter(pk=refresh.payload.get("user_id")).first()
    if user is None or not user.is_active:
        raise AuthenticationFailed("Your session has expired. Please sign in again.")

    gating_error = login_allowed_error(user)
    if gating_error:
        raise AuthenticationFailed(gating_error)

    if settings.SIMPLE_JWT.get("BLACKLIST_AFTER_ROTATION"):
        try:
            refresh.blacklist()
        except TokenError:
            pass  # token was already revoked

    response = Response({})
    response.data["access"] = _attach_refresh_cookie(response, user)
    return response


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@csrf_exempt
def logout_view(request):
    raw = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
    if raw:
        try:
            refresh = RefreshToken(raw)
            refresh.verify()
            refresh.blacklist()
        except TokenError:
            pass  # already revoked / unrecognised
    logout(request)
    response = Response({"authenticated": False})
    _detach_refresh_cookie(response)
    return response


# ---------------------------------------------------------------------------
# Onboarding configuration / checks
# ---------------------------------------------------------------------------
def onboarding_config_dict():
    interests = InterestSerializer(
        Interest.objects.filter(is_active=True).order_by("sort_order"), many=True
    ).data
    play_styles = PlayStyleSerializer(
        PlayStyle.objects.filter(is_active=True).order_by("sort_order"), many=True
    ).data
    return {
        "age_ranges": [{"value": r["value"], "label": r["label"]} for r in AGE_RANGES],
        "min_interests": settings.MINIMUM_ONBOARDING_INTERESTS,
        "min_age": settings.MINIMUM_ACCOUNT_AGE,
        "guardian_age_threshold": settings.GUARDIAN_AGE_THRESHOLD,
        "verification_age_threshold": settings.VERIFICATION_AGE_THRESHOLD,
        "requires_age_verification": settings.REQUIRE_AGE_VERIFICATION,
        "region_verification": _region_config_payload(),
        "interests": interests,
        "play_styles": play_styles,
    }


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def onboarding_config_view(request):
    return Response(onboarding_config_dict())


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def age_check_view(request):
    _apply_throttle(request, "anon")
    serializer = AgeCheckSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    dob = serializer.validated_data["date_of_birth"]
    region = serializer.validated_data.get("region") or ""
    branch_info = services.choose_onboarding_branch(dob, region=region or None)
    branch_info["date_of_birth"] = dob.isoformat()
    return Response(branch_info)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def username_check_view(request):
    _apply_throttle(request, "username")
    serializer = UsernameCheckSerializer(data=request.data)
    if not serializer.is_valid():
        first = next(iter(serializer.errors.values()), ["Invalid username"])[0]
        return Response({"available": False, "valid": False, "message": str(first)})
    username = serializer.validated_data["username"]
    available = User.objects.username_available(username)
    return Response(
        {
            "available": available,
            "valid": True,
            "message": None if available else "This username is already taken.",
        }
    )


# ---------------------------------------------------------------------------
# Account registration (transactional)
# ---------------------------------------------------------------------------
def _resolve_verification_upload(token):
    try:
        upload = IdentityDocumentUpload.objects.select_for_update().get(token=token)
    except IdentityDocumentUpload.DoesNotExist:
        raise ValidationError(
            {"verification_token": ["Verification document could not be found."]}
        )
    if not upload.is_valid():
        raise ValidationError(
            {
                "verification_token": [
                    "That verification upload has expired. Please upload again."
                ]
            }
        )
    return upload


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def register_view(request):
    _apply_throttle(request, "register")

    serializer = RegisterSerializer(data=request.data, context={"user_model": User})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    branch_info = data["_branch_info"]

    verification_upload = None
    if branch_info["branch"] == "verification":
        verification_upload = _resolve_verification_upload(data["verification_token"])

    with transaction.atomic():
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            username=data["username"],
            phone=data.get("phone"),
            full_name=data["full_name"],
            date_of_birth=data["date_of_birth"],
            region=data.get("region") or "",
            age_group=data.get("age_group") or "",
        )
        user.allocate_vector_id()
        user.calibrate_from_dob()
        user.onboarding_completed = True
        user.account_status = "active"
        user.save(
            update_fields=[
                "vector_id",
                "age_group",
                "onboarding_completed",
                "account_status",
                "updated_at",
            ]
        )

        Profile.objects.create(
            user=user,
            display_name=data["full_name"],
            country=data.get("region") or "",
        )

        interests_by_slug = {
            i.slug: i
            for i in Interest.objects.filter(slug__in=data["interests"], is_active=True)
        }
        play_styles_by_slug = {
            p.slug: p
            for p in PlayStyle.objects.filter(slug__in=data["play_styles"], is_active=True)
        }

        UserInterest.objects.bulk_create(
            [
                UserInterest(user=user, interest=interests_by_slug[slug])
                for slug in data["interests"]
                if slug in interests_by_slug
            ]
        )
        UserPlayStyle.objects.bulk_create(
            [
                UserPlayStyle(user=user, play_style=play_styles_by_slug[slug])
                for slug in data["play_styles"]
                if slug in play_styles_by_slug
            ]
        )

        if branch_info["branch"] == "guardian":
            GuardianRelationship.objects.create(
                student_user=user,
                guardian_email=data["guardian_email"],
                guardian_name=data.get("guardian_name") or "",
                guardian_phone=data.get("guardian_phone") or "",
                relationship_type=data.get("guardian_relationship_type") or "",
                status=GuardianStatus.PENDING,
                consent_status=ConsentStatus.PENDING,
                consent_method=ConsentMethod.EMAIL,
            )

        if branch_info["branch"] == "verification" and verification_upload is not None:
            verification_upload.status = UploadStatus.CONSUMED
            verification_upload.save(update_fields=["status"])
            Verification.objects.create(
                user=user,
                status=VerificationStatus.PENDING,
                provider=VerificationProvider.DOCUMENT,
                region=user.region or "",
                document_type=verification_upload.document_type,
                document=verification_upload.document.name,
                uploaded=verification_upload,
                submitted_at=timezone.now(),
            )
            user.verification_status = VerificationStatus.PENDING
            user.save(update_fields=["verification_status", "updated_at"])
        else:
            user.verification_status = VerificationStatus.NOT_REQUIRED
            user.age_verified = True
            user.save(update_fields=["verification_status", "age_verified", "updated_at"])

        OnboardingProgress.objects.create(
            user=user, current_step="complete", completed_steps=["complete"]
        )

        login(
            request,
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )

    user.last_login = timezone.now()
    user.save(update_fields=["last_login", "updated_at"])

    payload = onboarding_success_payload(user)
    response = Response(payload, status=status.HTTP_201_CREATED)
    response.data["access"] = _attach_refresh_cookie(response, user)

    # "Create account → verification request → email sent" for real addresses.
    _issue_email_verification(user)
    return response


def onboarding_success_payload(user):
    interests = list(
        user.user_interests.select_related("interest").values_list(
            "interest__slug", flat=True
        )
    )
    play_styles = list(
        user.user_play_styles.select_related("play_style").values_list(
            "play_style__slug", flat=True
        )
    )
    games = first_experience_recommendations(interests, play_styles, limit=3)
    return {
        "created": True,
        "onboarding_complete": user.onboarding_completed,
        "user": _user_identity_payload(user),
        "interests": interests,
        "play_styles": play_styles,
        "recommendations": games,
        "next": "/home",
    }


# ---------------------------------------------------------------------------
# Authenticated profile / identity endpoints
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def me_view(request):
    return Response(_user_identity_payload(request.user))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def first_experience_view(request):
    interests = list(
        request.user.user_interests.select_related("interest").values_list(
            "interest__slug", flat=True
        )
    )
    play_styles = list(
        request.user.user_play_styles.select_related("play_style").values_list(
            "play_style__slug", flat=True
        )
    )
    games = first_experience_recommendations(interests, play_styles, limit=3)
    return Response(
        {
            "interests": interests,
            "play_styles": play_styles,
            "recommendations": games,
        }
    )


@api_view(["GET", "PUT", "PATCH"])
@permission_classes([permissions.IsAuthenticated])
def onboarding_progress_view(request):
    progress, _ = OnboardingProgress.objects.get_or_create(user=request.user)
    if request.method == "GET":
        return Response(
            {
                "current_step": progress.current_step,
                "completed_steps": progress.completed_steps,
            }
        )
    payload = request.data or {}
    step = (payload.get("current_step") or "").strip()
    completed = progress.completed_steps or []
    if step and step not in completed:
        completed.append(step)
    progress.current_step = step
    progress.completed_steps = completed
    progress.save()
    return Response(
        {
            "current_step": progress.current_step,
            "completed_steps": progress.completed_steps,
        }
    )


# ---------------------------------------------------------------------------
# Identity document upload (pre-account) + verification status
# ---------------------------------------------------------------------------
def _document_error(message):
    return Response(
        {
            "error": {
                "code": "validation_failed",
                "message": message,
                "fields": {"document": [message]},
            }
        },
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def verification_upload_view(request):
    _apply_throttle(request, "upload")
    document = request.FILES.get("document")
    region = (request.POST.get("region") or "").strip()[:8]

    if document is None:
        return _document_error("Please choose a document to upload.")

    ext = os.path.splitext(document.name)[1].lstrip(".").lower()
    if ext not in ALLOWED_DOCUMENT_TYPES:
        return _document_error("Only JPG, PNG or PDF documents are allowed.")

    head = document.read(16)
    document.seek(0)
    signature = ALLOWED_DOCUMENT_TYPES["jpg"] if ext == "jpeg" else ALLOWED_DOCUMENT_TYPES[ext]
    if not head.startswith(signature):
        return _document_error("That file doesn't look like the selected format.")

    if document.size > settings.VERIFICATION_UPLOAD_MAX_BYTES:
        return _document_error("The document must be 5 MB or smaller.")

    upload = IdentityDocumentUpload.objects.create(
        document=document, document_type=ext, region=region
    )
    return Response(
        {
            "uploaded": True,
            "verification_token": str(upload.token),
            "document_type": ext,
            "status": upload.status,
            "expires_in_hours": settings.VERIFICATION_UPLOAD_EXPIRY_DAYS * 24,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def verification_status_view(request):
    verification = getattr(request.user, "verification", None)
    if verification is None:
        return Response(
            {
                "required": False,
                "status": VerificationStatus.NOT_REQUIRED,
                "provider": None,
                "verified_at": None,
            }
        )
    return Response(
        {
            "required": request.user.verification_status != VerificationStatus.NOT_REQUIRED,
            "status": verification.status,
            "provider": verification.provider,
            "region": verification.region,
            "document_type": verification.document_type,
            "submitted_at": (
                verification.submitted_at.isoformat() if verification.submitted_at else None
            ),
            "verified_at": (
                verification.verified_at.isoformat() if verification.verified_at else None
            ),
        }
    )


# ---------------------------------------------------------------------------
# Guardian relationship
# ---------------------------------------------------------------------------
@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def guardian_view(request):
    relationship = getattr(request.user, "guardian_relationship", None)

    if request.method == "GET":
        if relationship is None:
            return Response({"connected": False})
        return Response(
            {
                "connected": True,
                "student_user": request.user.display_identity,
                "guardian_email": relationship.guardian_email,
                "guardian_name": relationship.guardian_name,
                "guardian_phone": relationship.guardian_phone,
                "status": relationship.status,
                "consent_status": relationship.consent_status,
                "consent_method": relationship.consent_method,
            }
        )

    serializer = GuardianSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if relationship is None:
        relationship = GuardianRelationship(student_user=request.user)
    relationship.guardian_email = data["guardian_email"]
    relationship.guardian_name = data.get("guardian_name") or ""
    relationship.guardian_phone = data.get("guardian_phone") or ""
    relationship.relationship_type = data.get("relationship_type") or ""
    relationship.status = GuardianStatus.PENDING
    relationship.consent_status = ConsentStatus.PENDING
    relationship.consent_method = ConsentMethod.EMAIL
    relationship.save()
    return Response(
        {
            "connected": True,
            "guardian_email": relationship.guardian_email,
            "status": relationship.status,
            "consent_status": relationship.consent_status,
        },
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# E-mail verification (single-use, expiring, hashed tokens)
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def email_verify_request_view(request):
    """Send (or resend) an e-mail verification link for the current user.

    Authenticated users are verified directly; unauthenticated callers may
    pass an ``identifier`` so the account owner can re-request from the mail
    client. The response is intentionally identical either way.
    """
    _apply_throttle(request, "email_resend")
    payload = request.data or {}
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    if user is None:
        identifier = (payload.get("identifier") or "").strip()
        user = _resolve_user_by_identifier(identifier)

    if user is not None and user.email_verified:
        pass  # idempotent — a verified address needs no new link
    elif user is not None:
        _issue_email_verification(user)

    return Response({"sent": True})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def email_verify_confirm_view(request):
    _apply_throttle(request, "email_verify")
    serializer = EmailVerifySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user = authservices.consume_one_time_token(
            serializer.validated_data["token"], OneTimeTokenPurpose.EMAIL_VERIFICATION
        )
    except ValueError as exc:
        raise ValidationError({"token": [str(exc)]})
    if not user.email_verified:
        user.email_verified = True
        user.save(update_fields=["email_verified", "updated_at"])
    return Response({"verified": True, "email": user.email})


# ---------------------------------------------------------------------------
# Password reset (single-use, expiring, hashed tokens)
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset_request_view(request):
    _apply_throttle(request, "password_reset")
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = _resolve_user_by_identifier(serializer.validated_data["identifier"])
    if user is not None:
        try:
            raw, _token = authservices.issue_one_time_token(
                user, OneTimeTokenPurpose.PASSWORD_RESET
            )
            authservices.send_password_reset(user, raw)
        except Exception:  # pragma: no cover - transport failures are environmental
            import logging

            logging.getLogger("vector_strike.security").exception(
                "Failed to send password reset for %s", user.email
            )
    # Generic response — never reveal whether the account exists.
    return Response({"sent": True})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@throttle_classes([ScopedRateThrottle])
def password_reset_confirm_view(request):
    _apply_throttle(request, "password_reset")
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user = authservices.consume_one_time_token(
            serializer.validated_data["token"], OneTimeTokenPurpose.PASSWORD_RESET
        )
    except ValueError as exc:
        raise ValidationError({"token": [str(exc)]})

    from django.contrib.auth.password_validation import validate_password

    try:
        validate_password(serializer.validated_data["new_password"], user=user)
    except Exception as exc:
        messages = [str(m) for m in getattr(exc, "messages", [str(exc)])]
        raise ValidationError({"new_password": messages})

    user.set_password(serializer.validated_data["new_password"])
    user.save(update_fields=["password", "updated_at"])
    return Response({"reset": True})


# ---------------------------------------------------------------------------
# Phone verification — provider abstraction (dev console vs production)
# ---------------------------------------------------------------------------
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def phone_verify_request_view(request):
    _apply_throttle(request, "phone")
    serializer = PhoneRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data["phone"]

    if User.objects.phone_available(phone, exclude_id=request.user.pk) is False:
        raise ValidationError({"phone": ["That phone number is already in use."]})

    service = authservices.PhoneVerificationService()
    record, code = service.issue(request.user, phone)
    return Response(
        {
            "sent": True,
            "otp_expires_in_minutes": settings.PHONE_OTP_LIFETIME_MINUTES,
            "development": service.is_development(),
            # Development-only helper: the console provider logs the code, and
            # exposing it here keeps the e2e UX testable without faking success.
            "dev_code": code if service.is_development() else None,
        }
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([ScopedRateThrottle])
def phone_verify_confirm_view(request):
    _apply_throttle(request, "phone")
    serializer = PhoneConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    from apps.accounts.models import PhoneVerification

    record = (
        PhoneVerification.objects.filter(
            user=request.user, verified=False
        )
        .order_by("-created_at")
        .first()
    )
    if record is None:
        raise ValidationError(
            {"code": ["Request a verification code before confirming."]}
        )

    service = authservices.PhoneVerificationService()
    try:
        service.verify(record, serializer.validated_data["code"])
    except ValueError as exc:
        raise ValidationError({"code": [str(exc)]})

    request.user.phone = record.phone
    request.user.phone_verified = True
    request.user.save(update_fields=["phone", "phone_verified", "updated_at"])
    return Response({"verified": True, "phone": record.phone})


# ---------------------------------------------------------------------------
# Interests / play-styles lists (also served by onboarding config)
# ---------------------------------------------------------------------------
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def interests_view(request):
    interests = Interest.objects.filter(is_active=True).order_by("sort_order")
    return Response(
        {
            "count": interests.count(),
            "results": InterestSerializer(interests, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def play_styles_view(request):
    styles = PlayStyle.objects.filter(is_active=True).order_by("sort_order")
    return Response(
        {
            "count": styles.count(),
            "results": PlayStyleSerializer(styles, many=True).data,
        }
    )