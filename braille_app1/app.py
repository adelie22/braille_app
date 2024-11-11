# app.py

from flask import Flask, g
from config import Config
from extensions import db
from interfaces.mock_keyboard import MockBrailleKeyboard
# Uncomment the following line when using the hardware keyboard
# from interfaces.hardware_keyboard import HardwareBrailleKeyboard

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Initialize the keyboard interface
    if Config.USE_MOCK_KEYBOARD:
        keyboard = MockBrailleKeyboard()
    else:
        # keyboard = HardwareBrailleKeyboard(port='/dev/ttyUSB0')  # Adjust port as needed
        keyboard = None
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Attach the keyboard to the app context
    @app.before_request
    def before_request():
        g.keyboard = keyboard
    
    # Import and register blueprints
    from blueprints.learning import learning_bp
    app.register_blueprint(learning_bp, url_prefix='/learning')
    
    # Register other blueprints similarly
    # from blueprints.game import game_bp
    # app.register_blueprint(game_bp, url_prefix='/game')
    # from blueprints.diary import diary_bp
    # app.register_blueprint(diary_bp, url_prefix='/diary')
    
    # Home route
    @app.route('/')
    def home():
        return "Welcome to the Braille App"
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
