# app.py

from flask import Flask, g, render_template, jsonify, request
from config import Config
from extensions import db
from interfaces.mock_keyboard import MockBrailleKeyboard
from interfaces.hardware_keyboard import HardwareBrailleKeyboard
import logging
from word_chain_ko.api import word_chain_api  
from word_chain_en.api import word_chain_en_api 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Initialize the keyboard interface
    if app.config['USE_MOCK_KEYBOARD']:
        keyboard = MockBrailleKeyboard()
        app.logger.info("Using MockBrailleKeyboard.")
    else:
        keyboard = HardwareBrailleKeyboard(port=app.config['SERIAL_PORT'], baudrate=app.config['BAUD_RATE'])
        if keyboard.serial_port and keyboard.serial_port.is_open:
            app.logger.info("Using HardwareBrailleKeyboard.")
        else:
            app.logger.error("HardwareBrailleKeyboard initialization failed. Falling back to MockBrailleKeyboard.")
            keyboard = MockBrailleKeyboard()
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Attach the keyboard to the app context before each request
    @app.before_request
    def before_request():
        g.keyboard = keyboard
        app.logger.debug("before_request: g.keyboard has been set.")
    
    # Import and register blueprints
    from blueprints.learning import learning_bp
    from blueprints.diary.routes import diary_bp
    app.register_blueprint(learning_bp, url_prefix='/learning')
    app.register_blueprint(diary_bp, url_prefix='/diary')
    
    # Register other blueprints similarly
    # from blueprints.game import game_bp
    # app.register_blueprint(game_bp, url_prefix='/game')
    
    # Home route
    @app.route('/')
    def home():
        return "Welcome to the Braille App"
    app.register_blueprint(word_chain_api)
    app.register_blueprint(word_chain_en_api)
    @app.route('/')
    @app.route('/word_chain_menu')
    def menu():
        return render_template('word_chain_menu.html')  # Render templates/menu.html

    # Route for rendering the Korean word chain game page
    @app.route('/word_chain_ko')
    def word_chain_ko():
        return render_template('word_chain_ko.html')  # Render templates/word_chain_ko.html

    # Route for rendering the English word chain game page
    @app.route('/word_chain_en')
    def word_chain_en():
        g.keyboard.set_buffered_mode(True)
        return render_template('word_chain_en.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', use_reloader=False)