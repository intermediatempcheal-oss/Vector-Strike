import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager for the Vector Strike user model.

    Login is performed with the email address. Username and phone are unique
    platform identifiers in addition to the human-facing ``vector_id``.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        if not user.vector_id:
            user.allocate_vector_id()
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("account_status", "active")
        extra_fields.setdefault("onboarding_completed", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must be staff.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must be superuser.")
        return self._create_user(email, password, **extra_fields)

    def for_vector_id(self, vector_id):
        return self.get(vector_id__iexact=vector_id)

    def username_available(self, username, exclude_id=None):
        qs = self.filter(username__iexact=username)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return not qs.exists()

    def email_available(self, email, exclude_id=None):
        qs = self.filter(email__iexact=email)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return not qs.exists()

    def phone_available(self, phone, exclude_id=None):
        qs = self.filter(phone__iexact=phone)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        return not qs.exists()