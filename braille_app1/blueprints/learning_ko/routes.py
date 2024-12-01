# blueprints/learning/routes.py

from flask import render_template, jsonify
from . import learning_bp_ko
from models import KoVoca
from extensions import db
import logging

# Configure a logger for this module
logger = logging.getLogger(__name__)

# /learn 페이지 라우트
@learning_bp_ko.route('/')
def learn():
    return render_template('learning_ko/home.html')

@learning_bp_ko.route('/ko')
def learn_korean():
    return render_template('learning_ko/ko.html')

@learning_bp_ko.route('/ko/1')
def learn_kor_1():
    return render_template('learning_ko/ko_1.html')

@learning_bp_ko.route('/ko/2')
def learn_kor_2():
    return render_template('learning_ko/ko_2.html')

@learning_bp_ko.route('/ko/3')
def fetch_ko_voca():
    try:
        # Query all entries from ko_voca table using SQLAlchemy
        vocabulary = KoVoca.query.all()
        
        if not vocabulary:
            logger.info("No data found in ko_voca table.")
            vocabulary = None
        else:
            logger.debug(f"Fetched data: {vocabulary}")
        
        return render_template('learning_ko/ko_3.html', vocabulary=vocabulary)
    
    except Exception as e:
        logger.error(f"Error fetching data from ko_voca: {e}")
        return render_template('learning_ko/ko_3.html', vocabulary=None)

