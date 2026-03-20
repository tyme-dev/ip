"""
webapp package init

Provides a create_app factory for the Flask app.
"""
from flask import Flask

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    # Simple config; extend as needed
    app.config.setdefault("JSON_SORT_KEYS", False)

    # Import and register routes
    from . import app as app_module  # noqa: E402, F401
    return app
