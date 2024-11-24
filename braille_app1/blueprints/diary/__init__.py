# blueprints/diary/__init__.py

from flask import Blueprint

# Initialize the diary blueprint
diary_bp = Blueprint(
    'diary',                # Blueprint name
    __name__,               # Blueprint's import name
    template_folder='templates'  # Path to the blueprint's templates
)

from . import routes  # Import routes to register them with the blueprint
