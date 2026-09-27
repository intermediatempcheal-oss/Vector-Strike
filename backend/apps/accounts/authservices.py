"""Phase 7 identity-security services.

One-time tokens (e-mail verification, password reset) and the phone OTP
provider abstraction. Tokens are random at the point of use, single-use,
expiring, and stored only as SHA-256 digests.
"""

import hashlib
import logging
import secrets

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from apps.accounts.constants import OneTimeTokenPurpose

logger = logging.getLogger("vector_strike.security")

# ---------------------------------------------------------------------------
# One-time tokens
# ---------------------------------------------------------------------------


def hash_token(raw_token):
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _random_token():
    # 32 bytes of OS-entropy, URL-safe base64 (43 chars).
    return secrets.token_urlsafe(32)


def _lifetime_hours(purpose):
    if purpose == OneTimeTokenPurpose.PASSWORD_RESET:
        return settings.PASSWORD_RESET_TOKEN_HOURS
    return settings.EMAIL_VERIFICATION_TOKEN_HOURS


def issue_one_time_token(user, purpose):
    """Create a new one-time token for ``user`` and return the raw value.

    Previously issued, still-unused tokens of the same purpose are invalidated
    so only the newest token ever works.
    """
    from apps.accounts.models import OneTimeToken

    (OneTimeToken.objects.filter(user=user, purpose=purpose, used_at__isnull=True)
     .update(expires_at=timezone.now()))
    raw = _random_token()
    token = OneTimeToken.objects.create(
        user=user,
        purpose=purpose,
        token_hash=hash_token(raw),
        expires_at=timezone.now() + timezone.timedelta(hours=_lifetime_hours(purpose)),
    )
    return raw, token


def consume_one_time_token(raw_token, purpose):
    """Validate + consume a single-use token. Returns the user or raises ValueError."""
    from apps.accounts.models import OneTimeToken, User

    if not raw_token:
        raise ValueError("This verification link is not valid.")
    try:
        token = (
            OneTimeToken.objects.select_for_update()
            .filter(token_hash=hash_token(raw_token), purpose=purpose)
            .get()
        )
    except OneTimeToken.DoesNotExist:
        raise ValueError("This verification link is not valid.")
    if not token.is_usable():
        raise ValueError("This verification link has expired. Please request a new one.")
    token.consume()
    return User.objects.get(pk=token.user_id)


# ---------------------------------------------------------------------------
# E-mail delivery
# ---------------------------------------------------------------------------

def account_action_link(path, raw_token):
    origin = settings.FRONTEND_ORIGIN.rstrip("/")
    return f"{origin}/{path.lstrip('/')}?token={raw_token}"


def send_email_verification(user, raw_token):
    link = account_action_link("verify-email", raw_token)
    subject = "Confirm your Vector Strike email"
    message = (
        f"Hi {user.full_name or user.username},\n\n"
        f"Confirm this e-mail address to finish setting up your account:\n\n{link}\n\n"
        "This link expires in a few hours and can only be used once.\n"
        "If you didn't create a Vector Strike account, you can ignore this message.\n"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    logger.info("Email verification token issued for %s", user.email)


def send_password_reset(user, raw_token):
    link = account_action_link("reset-password", raw_token)
    subject = "Reset your Vector Strike password"
    message = (
        f"Hi {user.full_name or user.username},\n\n"
        f"Someone asked to reset your password. Use this link to set a new one:\n\n{link}\n\n"
        "This link expires in a few hours and can only be used once.\n"
        "If this wasn't you, you can safely ignore this e-mail.\n"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    logger.info("Password reset token issued for %s", user.email)


# ---------------------------------------------------------------------------
# Phone verification — provider abstraction
# ---------------------------------------------------------------------------

class SmsProvider:
    """Base SMS provider contract."""

    name = "base"

    def send(self, to, code):
        raise NotImplementedError


class ConsoleSmsProvider(SmsProvider):
    """Isolated DEVELOPMENT behaviour: never sends a real message.

    The OTP is logged to the ``vector_strike.security`` logger. It is still a
    random per-user code (never e.g. ``123456`` for everyone), so the same
    hardened verification logic exercises in development.
    """

    name = "console"

    def send(self, to, code):
        logger.info("DEV SMS provider: code %s -> %s", code, to)


class ProductionSmsProvider(SmsProvider):
    """Placeholder for a real SMS adapter (Twilio, Vonage, …).

    Selecting this provider without configuring an adapter raises clearly so a
    misconfigured production environment can never silently operate in a fake
    mode. Wire a real adapter here when integrating Phase 7 with an SMS vendor.
    """

    name = "production-placeholder"

    def send(self, to, code):
        raise NotImplementedError(
            "PHONE_VERIFICATION_PROVIDER is set to a production provider, but no "
            "real SMS adapter is configured yet. Refusing to send a fake OTP."
        )


def get_sms_provider():
    name = (settings.PHONE_VERIFICATION_PROVIDER or "console").lower()
    if name in ("console", "dev", "log"):
        return ConsoleSmsProvider()
    return ProductionSmsProvider()


def _random_otp():
    return f"{secrets.randbelow(1000000):06d}"


class PhoneVerificationService:
    """Issues and checks OTP codes through the configured SMS provider."""

    def __init__(self, provider=None):
        self.provider = provider or get_sms_provider()
        self._dev_provider = isinstance(self.provider, ConsoleSmsProvider)

    def is_development(self):
        """True when actually running the isolated console behaviour."""
        return self._dev_provider

    def issue(self, user, phone):
        from apps.accounts.models import PhoneVerification

        code = _random_otp()
        record = PhoneVerification.objects.create(
            user=user,
            phone=phone,
            otp_hash=hash_token(code),
            expires_at=timezone.now()
            + timezone.timedelta(minutes=settings.PHONE_OTP_LIFETIME_MINUTES),
        )
        self.provider.send(phone, code)
        return record, code

    def verify(self, record, code):
        from django.utils import timezone as _tz

        if record.verified:
            raise ValueError("This code has already been used.")
        if record.expires_at <= _tz.now():
            raise ValueError("This code has expired. Request a new one.")
        if record.attempts >= settings.PHONE_OTP_MAX_ATTEMPTS:
            raise ValueError("Too many attempts. Request a new code.")
        if not secrets.compare_digest(record.otp_hash, hash_token(code)):
            record.attempts += 1
            record.save(update_fields=["attempts"])
            raise ValueError("That code wasn't correct. Please try again.")
        record.verified = True
        record.attempts += 1
        record.verified_at = _tz.now()
        record.save(update_fields=["verified", "attempts", "verified_at"])
        return True