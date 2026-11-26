from flask import request, jsonify, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb

from . import auth_bp
from ..database import get_db


def format_user(user):
    return {
        "id": user["id"],
        "name": user["username"],
        "email": user["email"],
        "role": user["role"]
    }


def set_user_session(user):
    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]
    session["name"] = user["username"]


# -------------------------
# REGISTER
# -------------------------

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if len(name) > 100 or len(email) > 150:
        return jsonify({"error": "Name or email is too long"}), 400

    if "@" not in email:
        return jsonify({"error": "Enter a valid email address"}), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters"
        }), 400

    db = get_db()
    cursor = db.cursor()

    try:
        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (name, email, password_hash)
        )
        db.commit()

        user_id = cursor.lastrowid

        cursor.execute(
            """
            SELECT id, username, email, role
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()
        set_user_session(user)

        return jsonify({
            "message": "Registration successful",
            "user": format_user(user)
        }), 201

    except MySQLdb.IntegrityError:
        db.rollback()
        return jsonify({
            "error": "This email is already registered"
        }), 409

    finally:
        cursor.close()


# -------------------------
# LOGIN
# -------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT id, username, email, password_hash, role, active
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({
                "error": "Invalid email or password"
            }), 401

        if not user["active"]:
            return jsonify({
                "error": "Your account has been disabled"
            }), 403

        set_user_session(user)

        return jsonify({
            "message": "Login successful",
            "user": format_user(user)
        })

    finally:
        cursor.close()


# -------------------------
# CURRENT USER
# -------------------------

@auth_bp.route("/me", methods=["GET"])
def current_user():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            SELECT id, username, email, role, active
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user or not user["active"]:
            session.clear()
            return jsonify({"error": "Account unavailable"}), 401

        return jsonify({"user": format_user(user)})

    finally:
        cursor.close()


# -------------------------
# LOGOUT
# -------------------------

@auth_bp.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "message": "Logged out successfully"
    })