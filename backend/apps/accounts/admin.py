from django.contrib import admin

from apps.accounts.models import (
    GuardianRelationship,
    IdentityDocumentUpload,
    OnboardingProgress,
    User,
    Verification,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "vector_id",
        "username",
        "email",
        "phone",
        "full_name",
        "age_group",
        "age_verified",
        "verification_status",
        "account_status",
        "onboarding_completed",
    )
    search_fields = ("vector_id", "username", "email", "phone", "full_name")
    list_filter = (
        "account_status",
        "verification_status",
        "age_verified",
        "onboarding_completed",
    )
    readonly_fields = ("vector_id", "date_joined", "created_at", "updated_at")


@admin.register(GuardianRelationship)
class GuardianRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        "student_user",
        "guardian_email",
        "guardian_name",
        "status",
        "consent_status",
        "consent_method",
    )
    search_fields = ("student_user__email", "guardian_email", "guardian_name")
    list_filter = ("status", "consent_status", "consent_method")


@admin.register(IdentityDocumentUpload)
class IdentityDocumentUploadAdmin(admin.ModelAdmin):
    list_display = ("token", "document_type", "status", "region", "created_at", "expires_at")
    list_filter = ("status", "document_type")
    readonly_fields = ("token", "created_at", "expires_at")


@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "status",
        "provider",
        "region",
        "document_type",
        "submitted_at",
        "verified_at",
        "reviewed_at",
    )
    search_fields = ("user__email", "user__username", "user__vector_id")
    list_filter = ("status", "provider", "region")
    readonly_fields = ("submitted_at", "reviewed_at", "verified_at")


@admin.register(OnboardingProgress)
class OnboardingProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "current_step", "updated_at")
    search_fields = ("user__email", "user__username", "user__vector_id")
    readonly_fields = ("updated_at",)