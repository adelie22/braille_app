# blueprints/learning/routes.py

from flask import render_template, jsonify
from . import learning_bp_ko
from models import KoVoca
from KorToBraille.KorToBraille import KorToBraille
from extensions import db
import logging

# Configure a logger for this module
logger = logging.getLogger(__name__)

# /learn 페이지 라우트
# @learning_bp_ko.route('/')
# def learn():
#     return render_template('learning_ko/home.html')

@learning_bp_ko.route('/ko')
def learn_korean():
    return render_template('learning_ko/ko.html')

@learning_bp_ko.route('/ko/1')
def learn_kor_1():
    return render_template('learning_ko/ko_1.html')

# @learning_bp_ko.route('/ko/2')
# def learn_kor_2():
#     return render_template('learning_ko/ko_2.html')

# Helper function to fetch the vocabulary
def fetch_vocabulary():
    try:
        # Query all entries from ko_voca table using SQLAlchemy
        vocabulary = KoVoca.query.all()
        
        if not vocabulary:
            logger.info("No data found in ko_voca table.")
            return None
        else:
            logger.debug(f"Fetched data: {vocabulary}")
            return vocabulary
    except Exception as e:
        logger.error(f"Error fetching data from ko_voca: {e}")
        return None

@learning_bp_ko.route('/ko/3')
def display_ko_voca_words():
    """
    `ko_voca` 테이블의 단어를 점자로 변환하고, 각 점자 번호를 positions 리스트로 추가하여 렌더링합니다.
    """
    try:
        # 데이터베이스에서 단어 가져오기
        words = fetch_vocabulary()
        if words is None:
            logger.error("No vocabulary data available.")
            return render_template('learning_ko/ko_3.html', vocabulary=[])

        # 점자로 변환 및 positions 생성
        b = KorToBraille()
        vocabulary = []
        for word_entry in words:
            braille = b.korTranslate(word_entry.word)  # 단어를 점자로 변환
            if braille is None or braille == "":
                logger.error(f"Failed to translate word {word_entry.word} to Braille.")
                continue

            braille = braille[:-1]  # 마지막 점자 삭제
            positions = []
            for braille_char in braille:
                braille_number = ord(braille_char) - 0x2800
                positions.append(braille_number_to_dots(braille_number))

            vocabulary.append({
                'id': word_entry.id,
                'word': word_entry.word,      # 원본 단어
                'braille': braille,              # 변환된 점자 문자열
                'positions': positions           # 점자 번호 리스트
            })

        return render_template('learning_ko/ko_3.html', vocabulary=vocabulary)
    except Exception as e:
        logger.error(f"Error processing vocabulary: {e}")
        return render_template('learning_ko/ko_3.html', vocabulary=[])



def braille_number_to_dots(number):
    """
    점자 번호를 해당하는 점자 버튼(1~6번) 리스트로 변환합니다.
    """
    dots = []
    for i in range(1, 7):
        if number & (1 << (i - 1)):  # 비트 연산으로 점자 활성화 버튼 추출
            dots.append(i)
    return dots
