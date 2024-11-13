# blueprints/diary/__init__.py

from flask import Blueprint

# Initialize the learning blueprint
diary_bp = Blueprint(
    'diary',                # Blueprint name
    __name__,                  # Blueprint's import name
    template_folder='templates'  # Path to the blueprint's templates
)

