"""Tasks blueprint routes implementation."""
from datetime import datetime
from flask import request, jsonify, session
import MySQLdb

from . import tasks_bp
from ..database import get_db

ALLOWED_STATUSES = {"pending", "in_progress", "completed"}
ALLOWED_PRIORITIES = {"low", "medium", "high"}


def format_task(task):
    """Format task record for JSON response."""
    due_date = task.get("due_date")
    if due_date is not None:
        if hasattr(due_date, "isoformat"):
            due_date = due_date.isoformat()
        else:
            due_date = str(due_date)

    return {
        "id": task["id"],
        "user_id": task["user_id"],
        "title": task["title"],
        "description": task["description"],
        "status": task["status"],
        "priority": task["priority"],
        "due_date": due_date,
    }


def parse_and_validate_due_date(due_date_raw):
    """Validate and return YYYY-MM-DD or None, or raise ValueError."""
    if due_date_raw is None or due_date_raw == "":
        return None
    if isinstance(due_date_raw, str):
        due_date_str = due_date_raw.strip()
        if not due_date_str:
            return None
        # Strict validation of YYYY-MM-DD
        datetime.strptime(due_date_str, "%Y-%m-%d")
        return due_date_str
    raise ValueError("Invalid due_date format. Must be YYYY-MM-DD or null.")


@tasks_bp.route("", methods=["GET"])
@tasks_bp.route("/", methods=["GET"])
def get_tasks():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    db = get_db()
    cursor = db.cursor()

    try:
        scope = request.args.get("scope")
        if scope == "all":
            # Check if user is admin
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user or user.get("role") != "admin":
                return jsonify({"error": "Admin access required"}), 403

            cursor.execute(
                """
                SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at
                FROM tasks
                ORDER BY id ASC
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at
                FROM tasks
                WHERE user_id = %s
                ORDER BY id ASC
                """,
                (user_id,),
            )

        rows = cursor.fetchall()
        tasks = [format_task(row) for row in rows]
        return jsonify({"tasks": tasks}), 200

    finally:
        cursor.close()


@tasks_bp.route("", methods=["POST"])
@tasks_bp.route("/", methods=["POST"])
def create_task():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    title_raw = data.get("title")
    if title_raw is None or not isinstance(title_raw, str):
        return jsonify({"error": "Title is required"}), 400

    title = title_raw.strip()
    if not (1 <= len(title) <= 200):
        return jsonify({"error": "Title must be between 1 and 200 characters"}), 400

    description = data.get("description")
    if description is not None and not isinstance(description, str):
        return jsonify({"error": "Description must be a string or null"}), 400

    status = data.get("status", "pending")
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": f"Status must be one of {sorted(ALLOWED_STATUSES)}"}), 400

    priority = data.get("priority", "medium")
    if priority not in ALLOWED_PRIORITIES:
        return jsonify({"error": f"Priority must be one of {sorted(ALLOWED_PRIORITIES)}"}), 400

    try:
        due_date = parse_and_validate_due_date(data.get("due_date"))
    except ValueError:
        return jsonify({"error": "due_date must be formatted as YYYY-MM-DD or null"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO tasks (user_id, title, description, status, priority, due_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, title, description, status, priority, due_date),
        )
        new_task_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at
            FROM tasks
            WHERE id = %s
            """,
            (new_task_id,),
        )
        task = cursor.fetchone()
        return jsonify({"task": format_task(task)}), 201

    finally:
        cursor.close()


@tasks_bp.route("/<int:task_id>", methods=["PATCH", "PUT"])
def update_task(task_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        # Check if task exists and belongs to the user
        cursor.execute(
            """
            SELECT id, user_id, title, description, status, priority, due_date
            FROM tasks
            WHERE id = %s
            """,
            (task_id,),
        )
        existing_task = cursor.fetchone()
        if not existing_task or existing_task["user_id"] != user_id:
            return jsonify({"error": "Task not found"}), 404

        fields_to_update = []
        params = []

        if "title" in data:
            title_raw = data.get("title")
            if title_raw is None or not isinstance(title_raw, str):
                return jsonify({"error": "Title must be a non-empty string"}), 400
            title = title_raw.strip()
            if not (1 <= len(title) <= 200):
                return jsonify({"error": "Title must be between 1 and 200 characters"}), 400
            fields_to_update.append("title = %s")
            params.append(title)

        if "description" in data:
            description = data.get("description")
            if description is not None and not isinstance(description, str):
                return jsonify({"error": "Description must be a string or null"}), 400
            fields_to_update.append("description = %s")
            params.append(description)

        if "status" in data:
            status = data.get("status")
            if status not in ALLOWED_STATUSES:
                return jsonify({"error": f"Status must be one of {sorted(ALLOWED_STATUSES)}"}), 400
            fields_to_update.append("status = %s")
            params.append(status)

        if "priority" in data:
            priority = data.get("priority")
            if priority not in ALLOWED_PRIORITIES:
                return jsonify({"error": f"Priority must be one of {sorted(ALLOWED_PRIORITIES)}"}), 400
            fields_to_update.append("priority = %s")
            params.append(priority)

        if "due_date" in data:
            try:
                due_date = parse_and_validate_due_date(data.get("due_date"))
            except ValueError:
                return jsonify({"error": "due_date must be formatted as YYYY-MM-DD or null"}), 400
            fields_to_update.append("due_date = %s")
            params.append(due_date)

        if fields_to_update:
            sql = f"UPDATE tasks SET {', '.join(fields_to_update)} WHERE id = %s AND user_id = %s"
            params.extend([task_id, user_id])
            cursor.execute(sql, tuple(params))

        cursor.execute(
            """
            SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at
            FROM tasks
            WHERE id = %s
            """,
            (task_id,),
        )
        updated_task = cursor.fetchone()
        return jsonify({"task": format_task(updated_task)}), 200

    finally:
        cursor.close()


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("SELECT id, user_id FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task or task["user_id"] != user_id:
            return jsonify({"error": "Task not found"}), 404

        cursor.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, user_id))
        return "", 204

    finally:
        cursor.close()
