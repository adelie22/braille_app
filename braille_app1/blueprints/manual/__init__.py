# blueprints/manual/__init__.py

from flask import Blueprint

# Initialize the learning blueprint
manual_bp = Blueprint(
    'manual',                # Blueprint name
    __name__,                  # Blueprint's import name
    template_folder='templates',# Path to the blueprint's templates
    static_folder='static'
)

def register_routes():
    from . import routes