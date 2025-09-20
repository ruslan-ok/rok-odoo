from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Populate passwords.value_encrypted from legacy plaintext passwords.value on upgrade."""
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Fetch legacy plaintext values. Column `value` may still exist from older versions.
    try:
        cr.execute(
            """
            SELECT id, value
            FROM passwords
            WHERE value IS NOT NULL
                AND (value_encrypted IS NULL OR value_encrypted = '')
            """
        )
    except Exception:
        # If legacy column doesn't exist, nothing to migrate
        return

    rows = cr.fetchall() or []
    # if not rows:
    #     return

    Passwords = env['passwords']
    for rec_id, plaintext in rows:
        # Use model helper to encrypt with configured Fernet key
        enc = Passwords.browse(rec_id)._encrypt_value(plaintext)
        cr.execute(
            "UPDATE passwords SET value_encrypted=%s WHERE id=%s",
            (enc, rec_id),
        )

    # Drop legacy plaintext column to avoid storing clear text in DB
    try:
        cr.execute("ALTER TABLE passwords DROP COLUMN IF EXISTS value")
    except Exception:
        # Ignore if already dropped or insufficient privileges
        pass


