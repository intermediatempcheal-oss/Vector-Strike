"""Server-side validators for onboarding account fields."""

import re

USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{3,30}$")
# International-friendly phone: optional +, digits, spaces, dashes, parens.
PHONE_RE = re.compile(r"^\+?[0-9][0-9\s\-()]{6,24}$")
# Reserved handles that must not be impersonated.
RESERVED_USERNAMES = {
    "vector",
    "vectorstrike",
    "vs",
    "admin",
    "administrator",
    "system",
    "support",
    "moderator",
    "staff",
    "root",
    "help",
    "official",
    "team",
    "guest",
}
PROFESSIONAL_SUFFIXES = ("admin", "support", "official", "system", "staff")


class ValidationErrorMessages:
    USERNAME_INVALID = (
        "Use 3–30 characters: letters, numbers, periods or underscores."
    )
    USERNAME_RESERVED = "That username is reserved and cannot be used."
    PHONE_INVALID = "Please enter a valid phone number, including the country code."
    DOB_FUTURE = "Date of birth cannot be in the future."
    DOB_TOO_OLD = "Please enter a valid date of birth."
    DOB_TOO_YOUNG = "Vector Strike accounts require users to be at least 6 years old."
    EMAIL_INVALID = "Please enter a valid email address."
    NAME_REQUIRED = "Please enter your name."
    TERMS_REQUIRED = "Please accept the Terms and Privacy Policy to continue."
    INTERESTS_MIN = "Please select at least {count} interests."
    PLAYSTYLE_MIN = "Please choose at least one play style."
    GUARDIAN_EMAIL = "Please provide a valid guardian email."
    GUARDIAN_REQUIRED = "This account requires parent/guardian details."
    VERIFICATION_REQUIRED = "Please complete age verification to continue."


def is_valid_username(value):
    if not value or not USERNAME_RE.match(value):
        return False
    lower = value.lower().strip("._")
    if lower in RESERVED_USERNAMES:
        return False
    if any(lower.endswith(suffix) for suffix in PROFESSIONAL_SUFFIXES):
        return False
    return True


def is_valid_phone(value):
    if not value:
        return False
    compact = re.sub(r"[\s\-()]", "", value)
    return bool(PHONE_RE.match(value)) and len(compact) >= 7


def is_valid_email(value):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    try:
        validate_email(value or "")
    except ValidationError:
        return False
    return True