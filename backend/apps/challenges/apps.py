class VectorStrikeAppConfig:
    """Marker class for app registration helpers (Phase 11)."""


class ChallengesAppConfig(VectorStrikeAppConfig):
    """Vector Strike Challenges domain entry point.

    Real, relational, backend-owned competition system: players create genuine
    challenges, invite real members, join real rooms (secure non-sequential
    codes), form real teams, ready up, play real results. Nothing fabricated,
    no fake members, no fabricated scores/rank/participants.
    """

    name = "apps.challenges"
    label = "challenges"
    verbose_name = "Challenges & Competition"
