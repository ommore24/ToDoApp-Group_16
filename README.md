# TaskFlow – enhanced ToDo App preview

## Run locally (Windows PowerShell)
1. Extract this ZIP and open the `todo_app_updated` folder in VS Code.
2. Open Terminal in that folder.
3. Install dependencies: `py -m pip install -r requirements.txt`
4. Start the app: `py app.py`
5. Open `http://127.0.0.1:5000`

## Added features
- User dashboard shows overdue tasks and task summary.
- Dark mode toggle (saved in the browser).
- In-app popup/toast notifications for task actions and overdue reminders.
- Admin analytics page at `/admin` with task status graphs and summary figures.
- Responsive layout improvements.

## Important integration note
This ZIP is based on the supplied project, which uses temporary Python in-memory sample data. The supplied `app.py` did not contain MySQL connection code, authentication, user records, or role checks. Therefore, the admin analytics currently summarize the demo task list only; they do not represent real multi-user monitoring. Login and registration remain UI placeholders. Before using this in your combined team project, merge the templates/CSS/JS with your teammate's Flask routes and connect the queries to the actual MySQL database. Add proper login, admin authorization, CSRF protection, and a secure secret key before deployment.
