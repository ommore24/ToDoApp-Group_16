# run.py - entry point for the Todo Flask application

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run in development mode; host/port can be overridden via environment variables if desired
    app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', True))

