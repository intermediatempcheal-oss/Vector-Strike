"""Core Vector Strike account services.

Vector IDs and age calculations are backend-authored so that the distributed
frontend can never forge a permanent identity or lie about its age.
"""

import secrets
from datetime import date

from django.conf import settings
from django.utils import timezone

VECTOR_ID_PREFIX = "VS"
VECTOR_ID_BODY_LENGTH = 8
# Ambiguity-safe alphabet: no 0/O, 1/I/L.
VECTOR_ID_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"

MAX_ID_GENERATION_ATTEMPTS = 50


class VectorIDGenerationError(RuntimeError):
    """Raised when a unique Vector Strike ID could not be generated."""


def compose_vector_id(body):
    return f"{VECTOR_ID_PREFIX}-{body}"


def generate_vector_id_candidate():
    body = "".join(
        secrets.choice(VECTOR_ID_ALPHABET) for _ in range(VECTOR_ID_BODY_LENGTH)
    )
    return compose_vector_id(body)


def generate_unique_vector_id(exists_check):
    """Generate a globally unique Vector ID.

    ``exists_check`` receives a candidate and returns True when it is already
    taken. A unique database constraint is enforced on ``User.vector_id`` as a
    second line of defense, so concurrent collisions cannot slip through.
    """
    for _ in range(MAX_ID_GENERATION_ATTEMPTS):
        candidate = generate_vector_id_candidate()
        if not exists_check(candidate):
            return candidate
    raise VectorIDGenerationError("Could not allocate a unique Vector Strike ID.")


def calculate_age(date_of_birth, today=None):
    """Return the user's age in whole years on ``today``."""
    if date_of_birth is None:
        return None
    ref = today or timezone.localdate()
    had_birthday_this_year = (ref.month, ref.day) >= (
        date_of_birth.month,
        date_of_birth.day,
    )
    return (
        ref.year - date_of_birth.year - (0 if had_birthday_this_year else 1)
    )


def age_group_from_birthdate(date_of_birth, today=None):
    """Classify an age into the onboarding age-range buckets."""
    from apps.accounts.constants import AGE_RANGES

    age = calculate_age(date_of_birth, today)
    if age is None:
        return None
    for bucket in AGE_RANGES:
        low, high = bucket["age_range"]
        if low <= age <= high:
            return bucket["value"]
    return "13-15"


def verification_required_for_region(age, region=None):
    """Whether age verification is required for ``age`` in ``region``.

    Region handling is configurable so the platform can adapt per country,
    e.g. where 16-year-olds must verify but 13-year-olds are gated by
    guardian consent instead.
    """
    config = settings.AGE_VERIFICATION_REGION_CONFIG.get(
        region and region.upper(), settings.AGE_VERIFICATION_REGION_CONFIG["default"]
    )
    if not config.get("required"):
        return False, config
    if age is None:
        return True, config
    return age >= int(config.get("min_age", settings.VERIFICATION_AGE_THRESHOLD)), config


def choose_onboarding_branch(date_of_birth, region=None, today=None):
    """Return the age-based onboarding branch for a date of birth.

    Returns a dict with ``age``, ``branch`` ("guardian" | "verification") and
    the region verification config. This is the single source of truth used by
    both the age-check endpoint and registration.
    """
    age = calculate_age(date_of_birth, today)
    verify, region_config = verification_required_for_region(age, region)
    if age < settings.GUARDIAN_AGE_THRESHOLD:
        branch = "guardian"
    else:
        branch = "verification" if verify else "none"
    return {
        "age": age,
        "branch": branch,
        "guardian_threshold": settings.GUARDIAN_AGE_THRESHOLD,
        "verification_threshold": settings.VERIFICATION_AGE_THRESHOLD,
        "region": region,
        "region_config": region_config,
    }