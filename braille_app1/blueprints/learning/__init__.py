# blueprints/learning/__init__.py

from flask import Blueprint

# Initialize the learning blueprint
learning_bp = Blueprint(
    'learning',                # Blueprint name
    __name__,                  # Blueprint's import name
    template_folder='templates'  # Path to the blueprint's templates
)

# Import routes to register them with the blueprint
from . import routes