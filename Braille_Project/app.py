# app.py

from flask import Flask, g, render_template
from config import Config
from extensions import db
from interfaces.hardware_keyboard import HardwareBrailleKeyboard
from word_chain_ko.api import word_chain_api  
from word_chain_en.api import word_chain_en_api 
import logging


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    logging.basicConfig(
        level=logging.WARNING,  # Set the global logging level to WARNING
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.StreamHandler(),             # Logs to the console
            logging.FileHandler("app.log")       # Logs to a file named app.log
        ]
    )
    
    # Optionally, set specific loggers if needed
    app.logger.setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Suppress Werkzeug logs below WARNING
    
    
    # Initialize SQLAlchemy with the app
    db.init_app(app)
    
    # Initialize the keyboard interface
    keyboard = HardwareBrailleKeyboard(port=app.config['SERIAL_PORT'], baudrate=app.config['BAUD_RATE'])
    if keyboard.serial_port and keyboard.serial_port.is_open:
        app.logger.info("Using HardwareBrailleKeyboard.")
    else:
        app.logger.error("HardwareBrailleKeyboard initialization failed.")
    
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
    from blueprints.manual.routes import manual_bp
    from blueprints.learning_ko import learning_bp_ko
    from blueprints.index_bp import index_bp
    app.register_blueprint(learning_bp, url_prefix='/learning')
    app.register_blueprint(diary_bp, url_prefix='/diary')
    app.register_blueprint(manual_bp, url_prefix='/manual')
    app.register_blueprint(learning_bp_ko, url_prefix='/learning_ko')
    app.register_blueprint(index_bp)  # Register the Index Blueprint No prefix needed as route is specific
    app.register_blueprint(word_chain_api)
    app.register_blueprint(word_chain_en_api)
    
    # Home route
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/home')
    def home():
        return render_template('home.html')
    
    @app.route('/word_chain_menu')
    def menu():
        return render_template('word_chain_menu.html')  # Render templates/menu.html

    # Route for rendering the Korean word chain game page
    @app.route('/word_chain_ko')
    def word_chain_ko():
        g.keyboard.set_buffered_mode(True)
        return render_template('word_chain_ko.html')  # Render templates/word_chain_ko.html

    # Route for rendering the English word chain game page
    @app.route('/word_chain_en')
    def word_chain_en():
        g.keyboard.set_buffered_mode(True)
        return render_template('word_chain_en.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0')