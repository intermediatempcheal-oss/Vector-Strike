"""Serializers for account creation, auth and onboarding domain objects."""

from datetime import date

from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers

from apps.accounts import services
from apps.accounts.validators import (
    ValidationErrorMessages as Msg,
    is_valid_email,
    is_valid_phone,
    is_valid_username,
)
from apps.profiles.models import Interest, PlayStyle


class UsernameCheckSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)

    def validate_username(self, value):
        value = value.strip()
        if not is_valid_username(value):
            raise serializers.ValidationError(Msg.USERNAME_INVALID)
        return value


class AgeCheckSerializer(serializers.Serializer):
    date_of_birth = serializers.DateField(input_formats=["%Y-%m-%d"])
    region = serializers.CharField(max_length=8, required=False, allow_blank=True)

    def validate_date_of_birth(self, value):
        value = validate_date_of_birth_value(value)
        return value


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=120)
    username = serializers.CharField(max_length=30)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    date_of_birth = serializers.DateField(input_formats=["%Y-%m-%d"])
    password = serializers.CharField(
        max_length=128, min_length=8, trim_whitespace=False
    )
    region = serializers.CharField(max_length=8, required=False, allow_blank=True)
    age_group = serializers.CharField(max_length=16, required=False, allow_blank=True)
    interests = serializers.ListField(
        child=serializers.CharField(max_length=40), allow_empty=False
    )
    play_styles = serializers.ListField(
        child=serializers.CharField(max_length=50), allow_empty=True
    )
    terms_accepted = serializers.BooleanField()
    guardian_email = serializers.EmailField(required=False, allow_blank=True)
    guardian_name = serializers.CharField(max_length=120, required=False, allow_blank=True)
    guardian_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    verification_token = serializers.UUIDField(required=False)
    # Optional backend handle.
    onboarding_step = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        value = (value or "").strip()
        if not is_valid_username(value):
            raise serializers.ValidationError(
                f"{Msg.USERNAME_INVALID} {Msg.USERNAME_RESERVED}"
                if not value
                else Msg.USERNAME_INVALID
            )
        user_model = self.context["user_model"]
        if not user_model.objects.username_available(value):
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        value = (value or "").strip().lower()
        if not is_valid_email(value):
            raise serializers.ValidationError(Msg.EMAIL_INVALID)
        user_model = self.context["user_model"]
        if not user_model.objects.email_available(value):
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_phone(self, value):
        value = (value or "").strip()
        if not value:
            return None
        if not is_valid_phone(value):
            raise serializers.ValidationError(Msg.PHONE_INVALID)
        user_model = self.context["user_model"]
        if not user_model.objects.phone_available(value):
            raise serializers.ValidationError(
                "An account with this phone number already exists."
            )
        return value

    def validate_date_of_birth(self, value):
        return validate_date_of_birth_value(value)

    def validate_full_name(self, value):
        value = (value or "").strip()
        if len(value) < 2:
            raise serializers.ValidationError("Please enter your name.")
        return value

    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError(Msg.TERMS_REQUIRED)
        return value

    def validate_interests(self, value):
        slugs = list(dict.fromkeys((v or "").strip().lower() for v in value if v))
        minimum = settings.MINIMUM_ONBOARDING_INTERESTS
        if len(slugs) < minimum:
            raise serializers.ValidationError(
                Msg.INTERESTS_MIN.format(count=minimum)
            )
        found = set(
            Interest.objects.filter(slug__in=slugs, is_active=True).values_list(
                "slug", flat=True
            )
        )
        unknown = [s for s in slugs if s not in found]
        if unknown:
            raise serializers.ValidationError("Some interest selections are unknown.")
        return slugs

    def validate_play_styles(self, value):
        slugs = list(dict.fromkeys((v or "").strip().lower() for v in value if v))
        if len(slugs) < 1:
            raise serializers.ValidationError(Msg.PLAYSTYLE_MIN)
        found = set(
            PlayStyle.objects.filter(slug__in=slugs, is_active=True).values_list(
                "slug", flat=True
            )
        )
        unknown = [s for s in slugs if s not in found]
        if unknown:
            raise serializers.ValidationError("Some play-style selections are unknown.")
        return slugs

    def validate_guardian_phone(self, value):
        value = (value or "").strip()
        if value and not is_valid_phone(value):
            raise serializers.ValidationError(Msg.PHONE_INVALID)
        return value

    def validate(self, attrs):
        dob = attrs.get("date_of_birth")
        region = attrs.get("region") or ""
        branch_info = services.choose_onboarding_branch(dob, region=region or None)

        attrs["_branch_info"] = branch_info
        attrs["_age"] = branch_info["age"]

        if branch_info["branch"] == "guardian":
            guardian_email = (attrs.get("guardian_email") or "").strip()
            if not guardian_email:
                raise serializers.ValidationError(
                    {"guardian_email": ["Please provide the required guardian information."]}
                )
            if not is_valid_email(guardian_email):
                raise serializers.ValidationError(
                    {"guardian_email": [Msg.GUARDIAN_EMAIL]}
                )
            attrs["guardian_email"] = guardian_email
        else:
            attrs.pop("guardian_email", None)

        if branch_info["branch"] == "verification":
            if not attrs.get("verification_token"):
                raise serializers.ValidationError(
                    {"verification_token": [Msg.VERIFICATION_REQUIRED]}
                )
        return attrs


def validate_date_of_birth_value(value):
    today = timezone.localdate()
    if value > today:
        raise serializers.ValidationError(Msg.DOB_FUTURE)
    if value.year < 1900:
        raise serializers.ValidationError(Msg.DOB_TOO_OLD)
    age = services.calculate_age(value, today)
    if age < settings.MINIMUM_ACCOUNT_AGE:
        raise serializers.ValidationError(Msg.DOB_TOO_YOUNG)
    return value


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False)

    def validate(self, attrs):
        identifier = (attrs.get("identifier") or "").strip()
        password = attrs.get("password") or ""
        user = authenticate_by_identifier(identifier, password)
        if user is None:
            raise serializers.ValidationError(
                {"identifier": ["We couldn't sign you in. Check your email/username/Vector ID and password."]}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"identifier": ["Your account has been deactivated."]}
            )
        gating_error = login_allowed_error(user)
        if gating_error:
            raise serializers.ValidationError({"identifier": [gating_error]})
        attrs["user"] = user
        return attrs


def login_allowed_error(user):
    """Return a friendly message when an account must not authenticate, else None."""
    from apps.accounts.constants import AccountStatus
    from apps.accounts.models import User

    status = user.account_status
    if status == AccountStatus.DEACTIVATED:
        return "Your account has been deactivated."
    if status == AccountStatus.SUSPENDED:
        return "Your account is currently suspended. Contact support for help."
    if status == AccountStatus.CLOSED:
        return "This account has been closed."
    if status == AccountStatus.RESTRICTED:
        return "Your account is currently restricted from signing in."
    return None


def authenticate_by_identifier(identifier, password):
    from django.contrib.auth import authenticate

    from apps.accounts.models import User

    if not identifier or not password:
        return None
    user = None
    upper = identifier.upper()
    if "@" in identifier:
        user = User.objects.filter(email__iexact=identifier.strip().lower()).first()
    elif upper.startswith("VS-"):
        user = User.objects.filter(vector_id__iexact=upper).first()
    else:
        user = User.objects.filter(username__iexact=identifier).first()
    if user is None:
        # Constant-ish behaviour: authenticate against a ghost to keep
        # timing uniform, then return None.
        authenticate(email="nonexistent@vectorstrike.invalid", password="x")
        return None
    if not user.has_usable_password():
        return None
    authenticated = user.check_password(password)
    return user if authenticated else None


class UserIdentitySerializer(serializers.ModelSerializer):
    """Public identity of a user — never exposes internal UUID or tokens."""

    vector_id = serializers.CharField(read_only=True)
    age_group = serializers.CharField(read_only=True)
    age_category = serializers.CharField(read_only=True)
    guardian_status = serializers.CharField(read_only=True)
    profile = serializers.SerializerMethodField()
    interests = serializers.SerializerMethodField()
    play_styles = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        from apps.accounts.models import User

        model = User
        fields = [
            "vector_id",
            "username",
            "email",
            "phone",
            "full_name",
            "date_of_birth",
            "age_group",
            "age",
            "age_category",
            "age_verified",
            "verification_status",
            "account_status",
            "email_verified",
            "phone_verified",
            "onboarding_completed",
            "region",
            "profile",
            "interests",
            "play_styles",
            "guardian_status",
        ]

    def get_age(self, obj):
        return obj.age

    def get_profile(self, obj):
        from apps.profiles.models import Profile

        profile = getattr(obj, "profile", None)
        if profile is None:
            return None
        return {
            "display_name": profile.display_name,
            "language": profile.language,
            "country": profile.country,
            "skill_level": profile.skill_level,
            "level": profile.level,
            "xp": profile.xp,
            "rank": profile.rank or "rookie",
            "avatar": profile.avatar or "",
        }

    def get_interests(self, obj):
        return [
            link.interest.slug
            for link in obj.user_interests.select_related("interest").order_by(
                "interest__sort_order"
            )
        ]

    def get_play_styles(self, obj):
        return [
            link.play_style.slug
            for link in obj.user_play_styles.select_related("play_style").order_by(
                "play_style__sort_order"
            )
        ]


class PasswordResetRequestSerializer(serializers.Serializer):
    """Whoever owns this account is emailed a single-use reset link."""

    identifier = serializers.CharField(max_length=254)

    def validate_identifier(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("Enter your email, username or Vector ID.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(
        max_length=128, min_length=8, trim_whitespace=False
    )


class EmailVerifySerializer(serializers.Serializer):
    token = serializers.CharField()


class GuardianSerializer(serializers.Serializer):
    guardian_email = serializers.EmailField()
    guardian_name = serializers.CharField(
        max_length=120, required=False, allow_blank=True
    )
    guardian_phone = serializers.CharField(
        max_length=32, required=False, allow_blank=True
    )
    relationship_type = serializers.CharField(
        max_length=60, required=False, allow_blank=True
    )

    def validate_guardian_phone(self, value):
        value = (value or "").strip()
        if value and not is_valid_phone(value):
            raise serializers.ValidationError(Msg.PHONE_INVALID)
        return value


class PhoneRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)

    def validate_phone(self, value):
        value = (value or "").strip()
        if not is_valid_phone(value):
            raise serializers.ValidationError(Msg.PHONE_INVALID)
        return value


class PhoneConfirmSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=8, min_length=4)