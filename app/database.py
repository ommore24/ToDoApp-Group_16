# Database setup for Todo app
# pyrefly: ignore[missing-import]
from flask import current_app, g
import MySQLdb
from MySQLdb.cursors import DictCursor

def get_db():
    """Get a database connection for the current request.
    The connection is stored in Flask's `g` object and reused.
    """
    if 'db' not in g:
        try:
            g.db = MySQLdb.connect(
                host=current_app.config['MYSQL_HOST'],
                user=current_app.config['MYSQL_USER'],
                passwd=current_app.config['MYSQL_PASSWORD'],
                db=current_app.config['MYSQL_DB'],
                cursorclass=DictCursor,
                charset='utf8mb4',
                autocommit=True,
            )

        except MySQLdb.Error as e:
              current_app.logger.exception("Database connection failed")
            
              raise RuntimeError(f"Database connection error: {e}") from e


        # except MySQLdb.Error as e:
        #     current_app.logger.error(f"Database connection failed: {e}")
        #     # Re‑raise as a generic exception; route handlers can catch this.
        #     raise RuntimeError('Database connection error')
    return g.db

def init_db(app):
    """Initialize the database connection handling for the app.
    Registers a teardown function to close the connection after each request.
    """
    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop('db', None)
        if db is not None:
            db.close()
    # No immediate connection here – connections are lazy.
    return None

