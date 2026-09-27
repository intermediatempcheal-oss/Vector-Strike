from django.urls import path

from apps.accounts import views
from apps.profiles import views as profiles_views

urlpatterns = [
    path("interests/", views.interests_view, name="interests"),
    path("play-styles/", views.play_styles_view, name="play-styles"),
    path("profile/avatar/", profiles_views.avatar_view, name="profile-avatar"),
    path("profile/", profiles_views.profile_view, name="profile"),
    path(
        "profile/summary/",
        profiles_views.profile_summary_view,
        name="profile-summary",
    ),
    path(
        "profile/patch/",
        profiles_views.profile_patch_view,
        name="profile-patch",
    ),
    path("stack/", profiles_views.stack_view, name="stack"),
    path("stack/overview/", profiles_views.stack_overview_view, name="stack-overview"),
    path("stack/progress/", profiles_views.stack_progress_view, name="stack-progress"),
    path(
        "stack/achievements/",
        profiles_views.stack_achievements_view,
        name="stack-achievements",
    ),
    path(
        "stack/milestones/",
        profiles_views.stack_milestones_view,
        name="stack-milestones",
    ),
    path(
        "stack/activity/",
        profiles_views.stack_activity_view,
        name="stack-activity",
    ),
]