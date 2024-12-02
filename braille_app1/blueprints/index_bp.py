# blueprints/index_bp.py

from flask import Blueprint, jsonify, g
import logging

index_bp = Blueprint('index_bp', __name__)

@index_bp.route('/index/get_braille_signals', methods=['GET'])
def get_braille_signals():
    """
    API endpoint to fetch and return the latest Braille control signals specific to index.html.
    This endpoint should be polled by the frontend of index.html to receive signals.
    """
    g.keyboard.set_buffered_mode(False)
    control_signals = []
    
    # Fetch all control signals
    while True:
        input_signal = g.keyboard.read_input()
        if input_signal:
            if input_signal['type'] == 'control':
                control_signals.append(input_signal['data'])
            else:
                # Optionally handle other types or ignore them
                logging.warning(f"Index Blueprint - Unexpected input type: {input_signal}")
        else:
            break
    
    response = {
        'control_signals': control_signals
    }
    
    logging.debug(f"Index Blueprint - Sending response: {response}")  # Debugging
    
    return jsonify(response), 200
