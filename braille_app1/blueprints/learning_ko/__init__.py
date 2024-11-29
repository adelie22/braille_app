# blueprints/learning/__init__.py

from flask import Blueprint

# Initialize the learning blueprin


learning_bp_ko = Blueprint(
    'learning_ko',                # Blueprint name
    __name__,                  # Blueprint's import name
    template_folder='templates'  # Path to the blueprint's templates
)
# Import routes to register them with the blueprint
from . import routes
