# Configuration for the Todo app
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if present)
load_dotenv()

class Config:
    """Base configuration class.
    Extend or modify as needed for different environments.
    """
    # General Flask settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # MySQL settings – read from environment variables
    MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_USER = os.getenv('DB_USER', 'root')
    MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
    MYSQL_DB = os.getenv('DB_NAME', 'todo_app_db')
    MYSQL_CURSORCLASS = 'DictCursor'

