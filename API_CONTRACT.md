# Proposed API contract — confirm with your teammate

The frontend uses these proposed routes and fields. Do not assume the real backend already matches them.

## Roles
- `user`: can view/create/edit/delete only their own tasks.
- `admin`: can view all users, all tasks, and aggregate task statistics; can enable/disable user accounts.
- Public registration always creates `user`. Never let a public form choose `admin`.
- Backend must enforce authorization. Hiding buttons in the frontend is not security.

## Suggested task fields
`id`, `user_id`, `title`, `description`, `status`, `priority`, `due_date`.
Status: `pending`, `in_progress`, `completed`.
Priority: `low`, `medium`, `high`.
Date: `YYYY-MM-DD` or null.

## Endpoints expected by this frontend
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/me` | Current user + role |
| GET | `/api/tasks` | User's own tasks |
| GET | `/api/tasks?scope=all` | Admin all tasks |
| POST | `/api/tasks` | Create task for signed-in user |
| PATCH | `/api/tasks/{id}` | Edit task/status |
| DELETE | `/api/tasks/{id}` | Delete task |
| GET | `/api/admin/users` | Admin list users |
| PATCH | `/api/admin/users/{id}` | Enable/disable user |
| GET | `/api/admin/stats` | Admin statistics |

## Confirm with teammate
1. Exact endpoint names and HTTP methods (PATCH or PUT)?
2. Exact JSON keys and response shape (`{"tasks":[]}`, `{"user":{}}`)?
3. Are enum values and date format exactly as above?
4. Is authentication Flask session cookie or bearer token?
5. What does Manage Users require: enable/disable, edit, delete, or more?
6. Can admins edit/delete tasks, or only view them?

The included app.py is a local mock backend only. It uses in-memory lists, does not persist to MySQL, and does not securely verify/hash passwords. Never deploy it as a real authentication system.
