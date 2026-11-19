
from flask import Flask, jsonify, render_template, request, session, redirect
from functools import wraps
import hmac

app = Flask(__name__)
app.secret_key = "demo-only-change-before-deployment"

# ==========================================
# ADMIN LOGIN CONFIGURATION
# ==========================================

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123"

# ==========================================
# DEMO DATABASE
# Replace with your teammate's MySQL backend
# ==========================================

users = [
    {
        "id": 1,
        "name": "Aarav Shah",
        "email": "aarav@example.com",
        "role": "user",
        "active": True
    },
    {
        "id": 2,
        "name": "Mira Patel",
        "email": "mira@example.com",
        "role": "user",
        "active": True
    },
    {
        "id": 3,
        "name": "Administrator",
        "email": ADMIN_EMAIL,
        "role": "admin",
        "active": True
    }
]

tasks = [
    {
        "id": 101,
        "user_id": 1,
        "title": "Complete Python assignment",
        "description": "Finish exercises and test output.",
        "status": "pending",
        "priority": "high",
        "due_date": "2026-11-21"
    },
    {
        "id": 102,
        "user_id": 1,
        "title": "Prepare project presentation",
        "description": "Organise slides for review.",
        "status": "in_progress",
        "priority": "medium",
        "due_date": "2026-11-23"
    },
    {
        "id": 103,
        "user_id": 2,
        "title": "Review database schema",
        "description": "Check users and tasks tables.",
        "status": "completed",
        "priority": "low",
        "due_date": None
    }
]


# ==========================================
# AUTHENTICATION HELPERS
# ==========================================

def me():
    return next(
        (u for u in users if u["id"] == session.get("user_id")),
        None
    )


def require_login(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not me():
            return jsonify(error="Authentication required"), 401
        return fn(*args, **kwargs)

    return wrapped


def require_admin(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = me()

        if not user:
            return jsonify(error="Authentication required"), 401

        if user["role"] != "admin":
            return jsonify(error="Admin access required"), 403

        return fn(*args, **kwargs)

    return wrapped


# ==========================================
# WEBSITE PAGES
# ==========================================

@app.get("/")
def home():
    user = me()

    if not user:
        return redirect("/login")

    if user["role"] == "admin":
        return redirect("/admin")

    return redirect("/dashboard")


@app.get("/login")
def login_page():
    return render_template("login.html")


@app.get("/register")
def register_page():
    return render_template("register.html")


@app.get("/dashboard")
def user_page():
    return render_template("user_dashboard.html")


@app.get("/admin")
def admin_page():
    return render_template("admin_dashboard.html")


@app.get("/admin/users")
def users_page():
    return render_template("admin_users.html")


@app.get("/tasks")
def tasks_page():
    return render_template("tasks.html")


# ==========================================
# LOGIN API
# ==========================================

@app.post("/api/auth/login")
def login():

    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify(error="Email and password are required."), 400

    # ADMIN LOGIN
    if email == ADMIN_EMAIL:

        if not hmac.compare_digest(password, ADMIN_PASSWORD):
            return jsonify(error="Invalid admin email or password."), 401

        admin = next(
            (u for u in users if u["email"] == ADMIN_EMAIL),
            None
        )

        if not admin or not admin["active"]:
            return jsonify(error="Admin account is disabled."), 403

        session.clear()
        session["user_id"] = admin["id"]

        return jsonify(user=admin)

    # NORMAL USER LOGIN
    user = next(
        (u for u in users if u["email"].lower() == email),
        None
    )

    if not user:
        return jsonify(error="Account not found. Please register first."), 401

    if not user["active"]:
        return jsonify(error="Your account has been disabled."), 403

    if user["role"] != "user":
        return jsonify(error="Invalid account role."), 403

    # Demo only: existing normal-user accounts accept any non-empty password.
    session.clear()
    session["user_id"] = user["id"]

    return jsonify(user=user)


# ==========================================
# REGISTRATION API
# ==========================================

@app.post("/api/auth/register")
def register():

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify(
            error="Name, email and password are required."
        ), 400

    if len(password) < 8:
        return jsonify(
            error="Password must contain at least 8 characters."
        ), 400

    # Reserve the admin email.
    if email == ADMIN_EMAIL:
        return jsonify(
            error="This email is reserved for the administrator."
        ), 403

    if any(u["email"].lower() == email for u in users):
        return jsonify(error="Email already registered."), 409

    new_user = {
        "id": max((u["id"] for u in users), default=0) + 1,
        "name": name,
        "email": email,
        "role": "user",
        "active": True
    }

    users.append(new_user)

    session.clear()
    session["user_id"] = new_user["id"]

    return jsonify(user=new_user), 201


# ==========================================
# LOGOUT API
# ==========================================

@app.post("/api/auth/logout")
@require_login
def logout():

    session.clear()

    return "", 204


# ==========================================
# CURRENT USER API
# ==========================================

@app.get("/api/auth/me")
@require_login
def auth_me():

    return jsonify(user=me())


# ==========================================
# TASK APIs
# ==========================================

@app.get("/api/tasks")
@require_login
def list_tasks():

    user = me()

    if user["role"] == "admin" and request.args.get("scope") == "all":
        result = tasks.copy()
    else:
        result = [
            task for task in tasks
            if task["user_id"] == user["id"]
        ]

    status = request.args.get("status", "")
    query = request.args.get("q", "").lower()

    if status:
        result = [
            task for task in result
            if task["status"] == status
        ]

    if query:
        result = [
            task for task in result
            if query in task["title"].lower()
            or query in task["description"].lower()
        ]

    return jsonify(tasks=result)


@app.post("/api/tasks")
@require_login
def add_task():

    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()

    if not title:
        return jsonify(error="Task title is required."), 400

    task = {
        "id": max((t["id"] for t in tasks), default=100) + 1,
        "user_id": me()["id"],
        "title": title,
        "description": data.get("description", ""),
        "status": "pending",
        "priority": data.get("priority", "medium"),
        "due_date": data.get("due_date") or None
    }

    tasks.append(task)

    return jsonify(task=task), 201


@app.patch("/api/tasks/<int:tid>")
@require_login
def edit_task(tid):

    user = me()

    task = next(
        (t for t in tasks if t["id"] == tid),
        None
    )

    if not task:
        return jsonify(error="Task not found."), 404

    if user["role"] != "admin" and task["user_id"] != user["id"]:
        return jsonify(error="Task not found."), 404

    data = request.get_json(silent=True) or {}

    for key in ("title", "description", "status", "priority", "due_date"):
        if key in data:
            task[key] = data[key]

    return jsonify(task=task)


@app.delete("/api/tasks/<int:tid>")
@require_login
def remove_task(tid):

    user = me()

    task = next(
        (t for t in tasks if t["id"] == tid),
        None
    )

    if not task:
        return jsonify(error="Task not found."), 404

    if user["role"] != "admin" and task["user_id"] != user["id"]:
        return jsonify(error="Task not found."), 404

    tasks.remove(task)

    return "", 204


# ==========================================
# ADMIN APIs
# ==========================================

@app.get("/api/admin/users")
@require_admin
def admin_users():

    return jsonify(users=users)


@app.patch("/api/admin/users/<int:uid>")
@require_admin
def change_user(uid):

    user = next(
        (u for u in users if u["id"] == uid),
        None
    )

    if not user:
        return jsonify(error="User not found."), 404

    # Prevent disabling or modifying the admin account.
    if user["role"] == "admin":
        return jsonify(error="Admin account cannot be modified here."), 403

    data = request.get_json(silent=True) or {}

    user["active"] = bool(data.get("active", user["active"]))

    return jsonify(user=user)


@app.get("/api/admin/stats")
@require_admin
def stats():

    return jsonify(
        total_users=sum(u["role"] == "user" for u in users),
        total_tasks=len(tasks),
        pending_tasks=sum(t["status"] == "pending" for t in tasks),
        completed_tasks=sum(t["status"] == "completed" for t in tasks),
        in_progress_tasks=sum(t["status"] == "in_progress" for t in tasks)
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
