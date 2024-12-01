# blueprints/diary/routes.py

from flask import render_template, jsonify, request, g, redirect, url_for, flash
from extensions import db
from models import DiaryEntry
from flask import current_app
import logging
import threading

# Import the Blueprint from __init__.py
from . import diary_bp

@diary_bp.route('/', methods=['GET'])
def diary_home():
    """
    Render the diary home page with existing diary entries and a 'Create New Diary' option.
    """
    diaries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    return render_template('diary/diary.html', diaries=diaries)

@diary_bp.route('/get_diaries', methods=['GET'])
def get_diaries():
    """
    API endpoint to fetch all diary entries.
    """
    diaries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    diary_list = [{
        'id': diary.id,
        'date': diary.date.strftime('%Y-%m-%d %H:%M:%S'),
        'content': diary.content
    } for diary in diaries]
    return jsonify({'diaries': diary_list}), 200

@diary_bp.route('/create', methods=['POST'])
def create_diary():
    """
    API endpoint to create a new diary entry.
    """
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Content cannot be empty.'}), 400
    
    new_diary = DiaryEntry(content=content)
    db.session.add(new_diary)
    db.session.commit()
    
    logging.info(f"New diary created with ID: {new_diary.id}")
    
    return jsonify({'message': 'Diary created successfully.'}), 201

@diary_bp.route('/revise/<int:diary_id>', methods=['POST'])
def revise_diary(diary_id):
    """
    API endpoint to revise an existing diary entry.
    """
    diary = DiaryEntry.query.get_or_404(diary_id)
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Content cannot be empty.'}), 400
    
    diary.content = content
    db.session.commit()
    
    logging.info(f"Diary ID {diary_id} revised.")
    
    return jsonify({'message': 'Diary revised successfully.'}), 200

@diary_bp.route('/delete/<int:diary_id>', methods=['DELETE'])
def delete_diary(diary_id):
    """
    API endpoint to delete an existing diary entry.
    """
    diary = DiaryEntry.query.get_or_404(diary_id)
    db.session.delete(diary)
    db.session.commit()
    
    logging.info(f"Diary ID {diary_id} deleted.")
    
    return jsonify({'message': 'Diary deleted successfully.'}), 200

@diary_bp.route('/read/<int:diary_id>', methods=['GET'])
def read_diary(diary_id):
    """
    API endpoint to get the content of a diary entry for reading via speech synthesis.
    """
    diary = DiaryEntry.query.get_or_404(diary_id)
    return jsonify({'content': diary.content}), 200

# blueprints/diary/routes.py

@diary_bp.route('/get_braille_signals', methods=['GET'])
def get_braille_signals():
    """
    API endpoint to fetch and return the latest Braille signals.
    This endpoint should be polled by the frontend to receive signals.
    """
    signals = []
    control_signals = []
    
    # Fetch all Braille inputs
    input_buffer = g.keyboard.get_current_input_buffer()
    if input_buffer:
        logging.debug(f"Current input buffer: {input_buffer}")  # Added for debugging
        for bits in input_buffer:
            # Directly append the bits without checking for prefix
            if len(bits) == 6 and all(c in '01' for c in bits):
                signals.append(bits)
            else:
                logging.warning(f"Unexpected input format: {bits}")
        # Clear the buffer after fetching
        g.keyboard.clear_input_buffer()
    
    # Fetch all control signals
    while True:
        input_signal = g.keyboard.read_input()
        if input_signal:
            if input_signal['type'] == 'control':
                control_signals.append(input_signal['data'])
            else:
                # Optionally handle other types
                logging.warning(f"Unexpected input type: {input_signal}")
        else:
            break
    
    response = {
        'braille_signals': signals,
        'control_signals': control_signals
    }
    
    logging.debug(f"Sending response: {response}")  # Added for debugging
    
    return jsonify(response), 200


@diary_bp.route('/content', methods=['GET'])
def diary_content():
    """
    Render the diary content page for creating or revising diary entries.
    If a 'revise' query parameter is present, load the existing diary for revision.
    """
    revise_id = request.args.get('revise')
    revise = False
    if revise_id:
        diary = DiaryEntry.query.get_or_404(int(revise_id))
        content = diary.content
        revise = True
    else:
        content = ''
    
    # Enable buffered mode
    g.keyboard.set_buffered_mode(True)
    
    return render_template('diary/diary_content.html', revise=revise, diary_id=revise_id)
