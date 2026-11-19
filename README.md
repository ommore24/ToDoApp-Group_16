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
