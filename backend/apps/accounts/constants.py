"""Account-level constants shared between apps and services."""

from django.db import models

# Onboarding age-range buckets. The value is the bucket key presented to the
# user during onboarding; it is only a preliminary value — the backend
# recalculates the age from ``date_of_birth`` at registration.
AGE_RANGES = [
    {"value": "6-9", "label": "6–9", "age_range": (6, 9)},
    {"value": "10-12", "label": "10–12", "age_range": (10, 12)},
    {"value": "13-15", "label": "13–15", "age_range": (13, 15)},
    {"value": "16-17", "label": "16–17", "age_range": (16, 17)},
    {"value": "18+", "label": "18+", "age_range": (18, 130)},
]


class AccountStatus(models.TextChoices):
    """Server-authoritative lifecycle of an account.

    The backend decides whether a user may authenticate and what they may do:
    only ACTIVE accounts are fully unlocked; RESTRICTED/SUSPENDED/DEACTIVATED
    accounts are refused on login; PENDING_VERIFICATION accounts may sign in
    but cannot reach fully protected gameplay areas until identity is approved.
    """

    PENDING_ONBOARDING = "pending_onboarding", "Pending onboarding"
    PENDING_VERIFICATION = "pending_verification", "Pending verification"
    ACTIVE = "active", "Active"
    RESTRICTED = "restricted", "Restricted"
    SUSPENDED = "suspended", "Suspended"
    DEACTIVATED = "deactivated", "Deactivated"
    CLOSED = "closed", "Closed"


class VerificationStatus(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not required"
    PENDING = "pending", "Pending review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"


class OneTimeTokenPurpose(models.TextChoices):
    EMAIL_VERIFICATION = "email_verification", "Email verification"
    PASSWORD_RESET = "password_reset", "Password reset"


class VerificationProvider(models.TextChoices):
    DOCUMENT = "document", "Document upload"
    EXTERNAL = "external_provider", "External verification provider"
    NONE = "none", "None"


class GuardianStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    VERIFIED = "verified", "Verified"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"


class ConsentStatus(models.TextChoices):
    PENDING = "pending", "Pending consent"
    CONSENTED = "consented", "Consented"
    DECLINED = "declined", "Declined"
    EXPIRED = "expired", "Expired"


class ConsentMethod(models.TextChoices):
    EMAIL = "email", "Email"
    PHONE = "phone", "Phone"
    IN_PERSON = "in_person", "In person"
    NONE = "none", "None"


class UploadStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    CONSUMED = "consumed", "Consumed"
    EXPIRED = "expired", "Expired"