
from flask import jsonify, session

from . import admin_bp
from ..database import get_db


def get_admin_user(cursor):
    user_id = session.get("user_id")

    if not user_id:
        return None

    cursor.execute(
        "SELECT id, role, active FROM users WHERE id = %s",
        (user_id,)
    )

    user = cursor.fetchone()

    if not user or not user["active"]:
        return None

    if user["role"] != "admin":
        return None

    return user


@admin_bp.route("/stats", methods=["GET"])
def admin_stats():

    db = get_db()
    cursor = db.cursor()

    try:
        admin = get_admin_user(cursor)

        if not admin:
            return jsonify({"error": "Admin access required"}), 403

        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(*) AS total_tasks FROM tasks")
        total_tasks = cursor.fetchone()["total_tasks"]

        cursor.execute("""
            SELECT COUNT(*) AS pending_tasks
            FROM tasks
            WHERE status = 'pending'
        """)
        pending_tasks = cursor.fetchone()["pending_tasks"]

        cursor.execute("""
            SELECT COUNT(*) AS completed_tasks
            FROM tasks
            WHERE status = 'completed'
        """)
        completed_tasks = cursor.fetchone()["completed_tasks"]

        return jsonify({
            "total_users": total_users,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks
        })

    finally:
        cursor.close()



@admin_bp.route("/users", methods=["GET"])
def get_all_users():

    db = get_db()
    cursor = db.cursor()

    try:
        admin = get_admin_user(cursor)

        if not admin:
            return jsonify({"error": "Admin access required"}), 403

        cursor.execute("""
            SELECT
                id,
                username,
                email,
                role,
                active,
                created_at
            FROM users
            ORDER BY created_at DESC
        """)

        users = cursor.fetchall()

        return jsonify({
            "users": [
                {
                    "id": user["id"],
                    "name": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "active": bool(user["active"]),
                    "created_at": (
                        user["created_at"].isoformat()
                        if user["created_at"] else None
                    )
                }
                for user in users
            ]
        })

    finally:
        cursor.close()
      
