# ToDo App – Group 16

A web-based task management application built using **Python Flask, MySQL, HTML, CSS, and JavaScript**. It allows users to manage their daily tasks while providing administrators with a dashboard to monitor users and application activity.

---

## 1. Project Overview

The ToDo application is designed to help users organize and manage their tasks efficiently.

### Main Features

**User Features**
- User registration and login
- Secure password hashing
- Personal dashboard
- Create, view, update, and delete tasks
- Mark tasks as completed
- Task priority management
- Due date management
- Task status tracking

**Admin Features**
- Separate admin dashboard
- View application statistics
- View registered users
- View user details and account status
- Access task management functionality

---

## 2. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web application framework |
| MySQL | Database management |
| HTML5 | Frontend structure |
| CSS3 | Styling and responsive UI |
| JavaScript | Frontend interactions and API requests |
| Jinja2 | Flask template rendering |
| Git & GitHub | Version control and collaboration |

---

## 3. Project Structure

```text
todo_app/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── setup.py
│   │
│   ├── templates/
│   │
│   └── static/
│       ├── css/
│       │   └── style.css
│       │
│       └── js/
│           ├── common.js
│           ├── auth.js
│           ├── user_dashboard.js
│           ├── admin_dashboard.js
│           └── admin_users.js
│
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
└── run.py
```

### Important Files

- `run.py` – Application entry point.
- `app/__init__.py` – Flask application initialization and blueprint registration.
- `app/config.py` – Application and database configuration.
- `app/database.py` – MySQL connection handling.
- `app/auth/routes.py` – Registration, login, logout, and authentication APIs.
- `app/tasks/routes.py` – Task-related APIs.
- `app/admin/routes.py` – Admin statistics and user management APIs.
- `app/admin/setup.py` – Default admin account initialization.
- `schema.sql` – Database and table creation script.

---

## 4. Requirements

Before running the project, install the following:

1. Python 3.10 or later (use a version compatible with the project's dependencies).
2. MySQL Server.
3. Git.
4. Visual Studio Code or another code editor.

---

## 5. Installation and Setup

Follow these steps whenever you clone the project for the first time.

### Step 1: Clone the repository

```bash
git clone https://github.com/ommore24/ToDoApp-Group_16.git
```

Navigate into the project:

```bash
cd ToDoApp-Group_16
```

### Step 2: Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

If using Command Prompt:

```cmd
venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure MySQL

1. Start your local MySQL server.
2. Open MySQL Workbench.
3. Open the project's `schema.sql` file.
4. Execute the complete SQL script.

This creates the database and required tables.

**Important:** Every team member must execute `schema.sql` on their own local MySQL installation.

Each person's database is separate. GitHub shares the project code, not database records.

### Step 5: Configure environment variables

Create a file named `.env` in the project's root directory.

Copy the structure from `.env.example` and configure your local values:

```env
# Flask Configuration
FLASK_SECRET_KEY=your_unique_secret_key
FLASK_DEBUG=1

# MySQL Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=todo_app_db

# Default Admin Account
ADMIN_NAME=Project Admin
ADMIN_EMAIL=admin@todoapp.com
ADMIN_PASSWORD=your_development_admin_password
```

Replace the example values with your own configuration.

**Important:**
- Every teammate must create their own `.env` file.
- Do not upload `.env` to GitHub.
- Never commit database passwords or secret keys.
- Use a strong, unique secret key and password.

### Step 6: Run the application

```bash
python run.py
```

Open your browser:

```text
http://127.0.0.1:5000/
```

The application should now be running locally.

---

## 6. Admin Account Setup

The project includes automatic default admin account initialization through `app/admin/setup.py`.

When the application starts:

- It checks whether the configured admin email exists.
- If the account does not exist, it creates the admin account.
- If the account already exists, it ensures that its role is set to admin.

The default admin credentials are configured through each developer's `.env` file.

To access the admin dashboard:

```text
http://127.0.0.1:5000/admin
```

To manage registered users:

```text
http://127.0.0.1:5000/admin/users
```

**Note:** These are shared development credentials for the team. Do not use default credentials in a production deployment.

---

## 7. Application URLs

| URL | Description |
|---|---|
| `/` | Login page |
| `/login` | User login |
| `/register` | User registration |
| `/dashboard` | User dashboard |
| `/tasks` | Task management |
| `/admin` | Admin dashboard |
| `/admin/users` | Registered user management |
| `/health` | Application health check |
| `/db-test` | Database connection test |

### Important API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Register a user |
| POST | `/api/auth/login` | Authenticate a user |
| GET | `/api/auth/me` | Get logged-in user details |
| POST | `/api/auth/logout` | Log out |
| GET | `/api/tasks` | Retrieve tasks |
| GET | `/api/admin/stats` | Retrieve admin statistics |
| GET | `/api/admin/users` | Retrieve registered users |

Additional task and admin endpoints are implemented in their respective route files.

---

## 8. GitHub Collaboration Guidelines

All team members should follow these rules while contributing.

### Before starting work

Always synchronize your local main branch:

```bash
git switch main
git pull origin main
```

### Create a feature branch

Do not directly modify `main` for individual features.

```bash
git switch -c feature/your-feature-name
```

Example:

```bash
git switch -c feature/task-management
```

### After making changes

```bash
git add .
git commit -m "Describe your changes"
git push origin feature/your-feature-name
```

### Submit a Pull Request

1. Open the GitHub repository.
2. Create a Pull Request from your feature branch into `main`.
3. Add a description of your changes.
4. Wait for review and approval before merging.

### Important Git Rules

- Do not directly push unfinished work to `main`.
- Do not commit `.env` files.
- Do not commit your virtual environment.
- Pull the latest `main` before starting new work.
- Inform the team before making major changes.
- Resolve merge conflicts carefully.

---

## 9. Troubleshooting

| Problem | Possible Solution |
|---|---|
| MySQL connection error | Check MySQL server status and `.env` credentials. |
| `No module named flask` | Activate the virtual environment and install requirements. |
| Session unavailable / secret key error | Check `FLASK_SECRET_KEY` in `.env`. |
| Admin dashboard shows 404 | Check admin blueprint registration and API routes. |
| Admin login fails | Check admin credentials and database initialization. |
| Tables not found | Execute `schema.sql` in your local MySQL server. |
| Port 5000 already in use | Stop the other application using that port. |
| Changes not appearing | Refresh the page and restart Flask if necessary. |

---

## 10. Important Notes for Team Members

1. Every team member must configure their own MySQL database.
2. Every team member must create their own `.env` file.
3. The `schema.sql` file should be executed before running the application.
4. Never share or commit actual passwords and secret keys.
5. Always test your changes locally before creating a Pull Request.
6. Keep the `main` branch stable and functional.

---

## 11. Running the Project – Quick Reference

For subsequent runs, after completing the initial setup:

```powershell
# 1. Navigate to project directory
cd ToDoApp-Group_16

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Run application
python run.py
```

Open:

```text
http://127.0.0.1:5000/
```

---

**Project:** ToDo App – Group 16  
**Backend:** Python Flask  
**Database:** MySQL  
**Frontend:** HTML, CSS, JavaScript and Jinja2  
**Version Control:** GitHub
