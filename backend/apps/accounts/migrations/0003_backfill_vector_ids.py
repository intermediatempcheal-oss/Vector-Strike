"""Backfill empty/null vector_ids created before IDs were allocated at create.

Regression: user rows inserted via ``User.objects.create_user`` kept the
field default ``""`` because ``vector_id`` was allocated only after the first
``save()``. Since the column is ``unique=True``, a single leftover empty row
made every later registration fail with a UNIQUE constraint error.
"""
from django.db import migrations

_ID_PREFIX = "VS"  # must mirror accounts.constants.VECTOR_ID_PREFIX
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # mirror accounts.constants.VECTOR_ID_ALPHABET
_BODY_LENGTH = 8  # mirror accounts.constants.VECTOR_ID_BODY_LENGTH


def _candidate():
    import secrets

    return f"{_ID_PREFIX}-{''.join(secrets.choice(_ALPHABET) for _ in range(_BODY_LENGTH))}"


def backfill_vector_ids(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    taken = set(
        User.objects.exclude(vector_id="")
        .exclude(vector_id__isnull=True)
        .values_list("vector_id", flat=True)
    )
    empty = User.objects.filter(vector_id__in=["", None]).order_by("id")
    for user in empty:
        candidate = _candidate()
        while candidate in taken:
            candidate = _candidate()
        user.vector_id = candidate
        user.save(update_fields=["vector_id"])
        taken.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_alter_user_phone"),
    ]

    operations = [
        migrations.RunPython(backfill_vector_ids, migrations.RunPython.noop),
    ]