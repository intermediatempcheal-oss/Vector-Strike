"""Vector Strike — Game Hub domain (Phase 8).

Games, user game progress, achievements, missions, daily challenges, and live
events. All game/entity data is real rows from the database; the UI only ever
shows what this app stores or derives from actual member activity.
"""

from django.apps import AppConfig


class GamesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.games"
    label = "games"
    verbose_name = "Games & Game Hub"