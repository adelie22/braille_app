from . import manual_bp
from flask import render_template, g, jsonify
import logging

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

@manual_bp.route('/keyboard/get_braille_signals', methods=['GET'])
def get_keyboard_braille_signals():
    """
    API endpoint to fetch and return the latest Braille and control signals specific to the keyboard manual.
    This endpoint is polled by the frontend of keyboard_manual.html to receive signals.
    """
    # Enable buffered mode to capture Braille signals
    g.keyboard.set_buffered_mode(True)
    
    control_signals = []
    braille_signals = []
    
    # Retrieve Control Signals from the Queue
    while True:
        input_signal = g.keyboard.read_input()
        if input_signal:
            if input_signal['type'] == 'control':
                control_signals.append(input_signal['data'])
            else:
                logging.warning(f"Keyboard Manual - Unexpected input type: {input_signal}")
        else:
            break
    
    # Retrieve Braille Signals from the Input Buffer
    braille_buffer = g.keyboard.get_current_input_buffer()
    if braille_buffer:
        braille_signals.extend(braille_buffer)
        g.keyboard.clear_input_buffer()  # Clear buffer after reading
        logging.debug(f"Keyboard Manual - Retrieved Braille Signals: {braille_signals}")
    
    response = {
        'control_signals': control_signals,
        'braille_signals': braille_signals
    }
    
    logging.debug(f"Keyboard Manual - Sending response: {response}")
    
    return jsonify(response), 200