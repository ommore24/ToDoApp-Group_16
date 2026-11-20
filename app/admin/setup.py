from werkzeug.security import generate_password_hash
from ..database import get_db
from flask import current_app


def create_default_admin():

    db = get_db()
    cursor = db.cursor()

    try:
        admin_email = current_app.config.get("ADMIN_EMAIL")
        admin_name = current_app.config.get("ADMIN_NAME")
        admin_password = current_app.config.get("ADMIN_PASSWORD")

        if not admin_email or not admin_name or not admin_password:
            raise RuntimeError("Admin credentials are not configured")

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (admin_email,)
        )

        existing_admin = cursor.fetchone()

        if existing_admin:
            cursor.execute(
                """
                UPDATE users
                SET role = 'admin'
                WHERE email = %s
                """,
                (admin_email,)
            )
        else:
            password_hash = generate_password_hash(admin_password)

            cursor.execute(
                """
                INSERT INTO users
                (username, email, password_hash, role, active)
                VALUES (%s, %s, %s, 'admin', 1)
                """,
                (admin_name, admin_email, password_hash)
            )

    finally:
        cursor.close()