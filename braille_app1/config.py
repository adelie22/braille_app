# config.py

class Config:
    SECRET_KEY = 'Saveme'  # Replace with a secure key
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://scott:tiger@192.168.56.1/braille_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USE_MOCK_KEYBOARD = True  # Set to False when using the hardware keyboard
