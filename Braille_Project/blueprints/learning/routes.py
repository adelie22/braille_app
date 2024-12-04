# blueprints/learning/routes.py

from flask import render_template, jsonify
from . import learning_bp
from models import EnVoca
from extensions import db
import logging

# Configure a logger for this module
logger = logging.getLogger(__name__)

# /learn 페이지 라우트
# @learning_bp.route('/')
# def learn():
#     return render_template('learning/home.html')

@learning_bp.route('/en')
def learn_english():
    return render_template('learning/en.html')

@learning_bp.route('/en/1')
def learn_eng_1():
    return render_template('learning/en_1.html')

# @learning_bp.route('/en/2')
# def learn_eng_2():
#     return render_template('learning/en_2.html')


@learning_bp.route('/en/3')
def fetch_en_voca():
    try:
        # Query all entries from en_voca table using SQLAlchemy
        vocabulary = EnVoca.query.all()
        
        if not vocabulary:
            logger.info("No data found in en_voca table.")
            vocabulary = None
        else:
            logger.debug(f"Fetched data: {vocabulary}")
        
        return render_template('learning/en_3.html', vocabulary=vocabulary)
    
    except Exception as e:
        logger.error(f"Error fetching data from en_voca: {e}")
        return render_template('learning/en_3.html', vocabulary=None)
