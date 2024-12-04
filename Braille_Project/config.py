# config.py

import os

class Config:
    SECRET_KEY = 'Saveme'  # Replace with a secure key
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://scott:tiger@192.168.56.1/braille_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Hardware Keyboard Configuration
    SERIAL_PORT = '/dev/ttyACM0'      # Replace with your Arduino's serial port (e.g., '/dev/ttyUSB0' on Linux)
    BAUD_RATE = 9600          # Must match Arduino's Serial.begin rate