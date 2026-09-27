import uuid

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.accounts import services
from apps.accounts.constants import (
    AccountStatus,
    ConsentMethod,
    ConsentStatus,
    GuardianStatus,
    OneTimeTokenPurpose,
    UploadStatus,
    VerificationProvider,
    VerificationStatus,
)
from apps.accounts.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """The Vector Strike member.

    The human-facing platform identity is ``vector_id`` (e.g. ``VS-7K4M92Q1``),
    generated server-side. The internal primary key is a UUID and is never
    exposed through public APIs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vector_id = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        blank=True,
        help_text="Permanent, unique, immutable Vector Strike ID (server generated).",
    )

    username = models.CharField(
        max_length=30, unique=True, db_index=True, help_text="Unique platform handle."
    )
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(
        max_length=32, unique=True, db_index=True, null=True, blank=True
    )
    full_name = models.CharField(max_length=120)
    date_of_birth = models.DateField(null=True, blank=True)

    age_group = models.CharField(
        max_length=16, blank=True, help_text="Preliminary onboarding bucket."
    )
    age_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=24,
        choices=VerificationStatus.choices,
        default=VerificationStatus.NOT_REQUIRED,
    )
    account_status = models.CharField(
        max_length=24,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING_ONBOARDING,
    )
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    onboarding_completed = models.BooleanField(default=False)
    region = models.CharField(max_length=8, blank=True, default="")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "full_name"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.vector_id or self.email

    @property
    def age(self):
        return services.calculate_age(self.date_of_birth)

    @property
    def age_category(self):
        """Coarse lifecycle bucket: UNDER_17 or 17_PLUS (backend-authoritative)."""
        age = self.age
        if age is None:
            return None
        return "UNDER_17" if age < settings.GUARDIAN_AGE_THRESHOLD else "17_PLUS"

    @property
    def guardian_status(self):
        relationship = getattr(self, "guardian_relationship", None)
        return relationship.status if relationship else None

    @property
    def display_identity(self):
        return self.vector_id or self.username

    def natural_key(self):
        return (self.email,)

    def allocate_vector_id(self):
        if self.vector_id:
            return self.vector_id
        self.vector_id = services.generate_unique_vector_id(
            lambda candidate: type(self).objects.filter(vector_id=candidate).exists()
        )
        return self.vector_id

    def calibrate_from_dob(self):
        age = services.calculate_age(self.date_of_birth)
        self.age_group = services.age_group_from_birthdate(self.date_of_birth)
        return age

    def finalize_onboarding(self):
        age = self.calibrate_from_dob()
        _, region_config = services.verification_required_for_region(
            age, self.region or None
        )
        if self.verification_status == VerificationStatus.APPROVED:
            self.age_verified = True
        elif age is not None and age < settings.GUARDIAN_AGE_THRESHOLD:
            self.age_verified = True  # Guardian flow handles consent.
        else:
            self.age_verified = self.verification_status == VerificationStatus.APPROVED
        self.onboarding_completed = True
        self.account_status = AccountStatus.ACTIVE


class GuardianRelationship(models.Model):
    """Connects a younger user's account to a parent or guardian.

    ``status`` and ``consent_status`` are intentionally not marked verified
    when an email address is simply typed into a form — a future consent
    mechanism (email/SMS link) upgrades these states.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student_user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="guardian_relationship",
    )
    guardian_email = models.EmailField()
    guardian_name = models.CharField(max_length=120, blank=True, default="")
    guardian_phone = models.CharField(max_length=32, blank=True, default="")
    relationship_type = models.CharField(max_length=60, blank=True, default="")

    status = models.CharField(
        max_length=16,
        choices=GuardianStatus.choices,
        default=GuardianStatus.PENDING,
    )
    consent_status = models.CharField(
        max_length=16,
        choices=ConsentStatus.choices,
        default=ConsentStatus.PENDING,
    )
    consent_method = models.CharField(
        max_length=16, choices=ConsentMethod.choices, default=ConsentMethod.NONE
    )
    consent_token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    consent_requested_at = models.DateTimeField(auto_now_add=True)
    consented_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_guardian_relationship"
        verbose_name = "guardian relationship"
        verbose_name_plural = "guardian relationships"

    def __str__(self):
        return f"{self.student_user.display_identity} -> {self.guardian_email}"

    def request_consent(self):
        self.status = GuardianStatus.PENDING
        self.consent_status = ConsentStatus.PENDING
        self.consent_token = uuid.uuid4()
        self.consent_requested_at = timezone.now()
        self.save(update_fields=[
            "status",
            "consent_status",
            "consent_token",
            "consent_requested_at",
            "updated_at",
        ])


class IdentityDocumentUpload(models.Model):
    """A pending, unauthenticated identity document upload.

    The document itself lives in dedicated secure storage (``MEDIA_ROOT``),
    never inside the user table, and only metadata is retained here. Uploads
    expire shortly after creation if no account claims them.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    document = models.FileField(
        upload_to="verification/pending/", max_length=255, blank=True
    )
    document_type = models.CharField(max_length=8, blank=True, default="")
    status = models.CharField(
        max_length=16, choices=UploadStatus.choices, default=UploadStatus.PENDING
    )
    region = models.CharField(max_length=8, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "accounts_identity_document_upload"
        verbose_name = "identity document upload"
        verbose_name_plural = "identity document uploads"

    def __str__(self):
        return f"{self.token} ({self.document_type})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(
                days=settings.VERIFICATION_UPLOAD_EXPIRY_DAYS
            )
        super().save(*args, **kwargs)

    def is_valid(self):
        return (
            self.status == UploadStatus.PENDING
            and self.document
            and self.expires_at > timezone.now()
        )


class Verification(models.Model):
    """Age / identity verification metadata for a user account.

    Stores only metadata and a reference to the uploaded document; document
    contents remain in secure storage. ``provider`` keeps the door open for
    third-party age-verification providers.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="verification"
    )
    status = models.CharField(
        max_length=24,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    provider = models.CharField(
        max_length=24,
        choices=VerificationProvider.choices,
        default=VerificationProvider.NONE,
    )
    region = models.CharField(max_length=8, blank=True, default="")
    document_type = models.CharField(max_length=8, blank=True, default="")
    document = models.FileField(upload_to="verification/verified/", blank=True)
    uploaded = models.OneToOneField(
        IdentityDocumentUpload,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="consumed_by",
    )
    reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Provider-level reference for this verification (e.g. external supplier ref).",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_verification"
        verbose_name = "verification"
        verbose_name_plural = "verifications"

    def __str__(self):
        return f"{self.user.display_identity} ({self.status})"

    def mark_expired(self):
        self.status = VerificationStatus.EXPIRED
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_at"])
        self.user.verification_status = VerificationStatus.EXPIRED
        self.user.save(update_fields=["verification_status", "updated_at"])

    def mark_approved(self):
        now = timezone.now()
        self.status = VerificationStatus.APPROVED
        self.reviewed_at = now
        self.verified_at = now
        self.save(update_fields=["status", "reviewed_at", "verified_at"])
        if not self.user.verification_status == VerificationStatus.APPROVED:
            self.user.verification_status = VerificationStatus.APPROVED
            self.user.age_verified = True
        if self.user.account_status == AccountStatus.PENDING_VERIFICATION:
            self.user.account_status = AccountStatus.ACTIVE
        self.user.save(
            update_fields=[
                "verification_status",
                "age_verified",
                "account_status",
                "updated_at",
            ]
        )

    def mark_rejected(self):
        self.status = VerificationStatus.REJECTED
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "reviewed_at"])


class OnboardingProgress(models.Model):
    """Server-side mirror of a user's onboarding position.

    Non-sensitive selections only; account credentials are never stored here.
    Lets a user resume onboarding after a refresh even mid-window.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="onboarding_progress"
    )
    current_step = models.CharField(max_length=40, blank=True, default="")
    completed_steps = models.JSONField(default=list, blank=True)
    data = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_onboarding_progress"
        verbose_name = "onboarding progress"
        verbose_name_plural = "onboarding progress"

    def __str__(self):
        return f"{self.user.display_identity} @ {self.current_step}"


class OneTimeToken(models.Model):
    """A random, expiring, single-use token for sensitive account actions.

    Only a SHA-256 digest of the raw token is stored, so a database leak does
    not expose usable tokens. The raw value is sent exactly once to the user.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="one_time_tokens"
    )
    purpose = models.CharField(
        max_length=32, choices=OneTimeTokenPurpose.choices
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_one_time_token"
        verbose_name = "one-time token"
        verbose_name_plural = "one-time tokens"
        indexes = [
            models.Index(fields=["user", "purpose"], name="ot_token_user_purpose"),
        ]

    def __str__(self):
        return f"{self.purpose} for {self.user.display_identity}"

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()

    def is_usable(self):
        return self.used_at is None and not self.is_expired

    def consume(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])


class PhoneVerification(models.Model):
    """Server-side OTP verification state for a phone number.

    Never stores the plaintext OTP — only its SHA-256 digest. ``attempts``
    enforces a small retry budget per request to frustrate brute force.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="phone_verifications"
    )
    phone = models.CharField(max_length=32, db_index=True)
    otp_hash = models.CharField(max_length=64, db_index=True)
    verified = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_phone_verification"
        verbose_name = "phone verification"
        verbose_name_plural = "phone verifications"

    def __str__(self):
        return f"{self.phone} (verified={self.verified})"

    @property
    def is_expired(self):
        return self.expires_at <= timezone.now()