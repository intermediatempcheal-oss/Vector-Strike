from django.urls import path

from apps.accounts import views

urlpatterns = [
    # Auth & session
    path("auth/csrf/", views.csrf_view, name="auth-csrf"),
    path("auth/session/", views.session_view, name="auth-session"),
    path("auth/login/", views.login_view, name="auth-login"),
    path("auth/token/refresh/", views.token_refresh_view, name="token-refresh"),
    path("auth/logout/", views.logout_view, name="auth-logout"),
    # Identity verification & recovery (Phase 7)
    path("auth/email/verify/request/", views.email_verify_request_view, name="email-verify-request"),
    path("auth/email/verify/", views.email_verify_confirm_view, name="email-verify-confirm"),
    path("auth/password/reset/", views.password_reset_request_view, name="password-reset-request"),
    path("auth/password/reset/confirm/", views.password_reset_confirm_view, name="password-reset-confirm"),
    path("auth/phone/verify/request/", views.phone_verify_request_view, name="phone-verify-request"),
    path("auth/phone/verify/", views.phone_verify_confirm_view, name="phone-verify-confirm"),
    # Onboarding discovery & checks
    path("onboarding/config/", views.onboarding_config_view, name="onboarding-config"),
    path("onboarding/age-check/", views.age_check_view, name="onboarding-age-check"),
    path("onboarding/progress/", views.onboarding_progress_view, name="onboarding-progress"),
    path("onboarding/first-experience/", views.first_experience_view, name="onboarding-first-experience"),
    path("username/check/", views.username_check_view, name="username-check"),
    path("accounts/register/", views.register_view, name="account-register"),
    path("accounts/me/", views.me_view, name="account-me"),
    # Verification & guardian
    path("verification/upload/", views.verification_upload_view, name="verification-upload"),
    path("verification/", views.verification_status_view, name="verification-status"),
    path("guardian/", views.guardian_view, name="guardian"),
]