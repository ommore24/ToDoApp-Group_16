# ToDo App role-based To-Do app

## Screens
- Common: Registration, Login
- User: Dashboard, personal tasks, add/edit/delete/complete, status and priority filters
- Admin: Dashboard, all task overview, registered users, enable/disable control, task statistics

## Run in VS Code (Windows PowerShell)
1. Extract ZIP and open this folder in VS Code.
2. Run:
   `python -m pip install -r requirements.txt`
3. Run:
   `python app.py`
4. Visit `http://127.0.0.1:5000/login`

Demo login:
- Admin: admin@example.com
- User: aarav@example.com
- Any password works in this demo only.

The included app.py is a mock preview backend with in-memory data. It is not connected to MySQL and is not production authentication. Read API_CONTRACT.md and agree on fields, routes, auth, and permissions with your teammate before integration.

## Tasks REST API (Route to SQL Mapping)

All tasks endpoints are implemented in [app/tasks/routes.py](file:///c:/Users/patha/Desktop/ToDoApp-Group_16/app/tasks/routes.py). Every endpoint requires user authentication via session cookie (`session["user_id"]`), enforces parameterized SQL queries (`%s`), validates inputs according to the API contract, and isolates tasks per user (preventing cross-user access with 404 responses).

| Endpoint | HTTP Method | Handler Function | SQL Queries Executed |
|---|---|---|---|
| `/api/tasks` | `GET` | `get_tasks` | `SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at FROM tasks WHERE user_id = %s ORDER BY id ASC` |
| `/api/tasks?scope=all` | `GET` | `get_tasks` | `SELECT role FROM users WHERE id = %s` (verify admin role, returns 403 if not admin);<br>`SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at FROM tasks ORDER BY id ASC` |
| `/api/tasks` | `POST` | `create_task` | `INSERT INTO tasks (user_id, title, description, status, priority, due_date) VALUES (%s, %s, %s, %s, %s, %s)`;<br>`SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at FROM tasks WHERE id = %s` |
| `/api/tasks/<id>` | `PATCH` / `PUT` | `update_task` | `SELECT id, user_id, title, description, status, priority, due_date FROM tasks WHERE id = %s` (checks ownership; returns 404 if not found or belongs to another user);<br>`UPDATE tasks SET <fields> WHERE id = %s AND user_id = %s`;<br>`SELECT id, user_id, title, description, status, priority, due_date, created_at, updated_at FROM tasks WHERE id = %s` |
| `/api/tasks/<id>` | `DELETE` | `delete_task` | `SELECT id, user_id FROM tasks WHERE id = %s` (checks ownership; returns 404 if not found or belongs to another user);<br>`DELETE FROM tasks WHERE id = %s AND user_id = %s` |

