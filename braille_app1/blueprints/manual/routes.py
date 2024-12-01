from . import manual_bp
from flask import render_template

@manual_bp.route('/')
def manual():
    return render_template('manual/home.html')

@manual_bp.route('/learning')
def m_learning():
    return render_template('manual/learning.html')

@manual_bp.route('/game')
def m_game():
    return render_template('manual/game.html')

@manual_bp.route('/diary')
def ma_diary():
    return render_template('manual/diary.html')

@manual_bp.route('/keyboard')
def m_keyboard():
    return render_template('manual/keyboard.html')