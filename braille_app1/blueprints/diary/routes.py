# blueprints/diary/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, g, jsonify, Response, send_file
from models import DiaryEntry
from extensions import db
from google.cloud import texttospeech
from datetime import datetime
import os
import json
import logging

from . import diary_bp

# Configure logging if not already done
logging.basicConfig(level=logging.DEBUG)

# Initialize Google TTS client
tts_client = texttospeech.TextToSpeechClient()

@diary_bp.route('/', methods=['GET'])
def list_entries():
    """
    List all diary entries.
    """
    entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()  # Updated field name
    return render_template('diary/diary.html', entries=entries)

@diary_bp.route('/create', methods=['POST'])
def create_diary():
    """
    Create a new diary entry.
    """
    data = request.get_json()
    date_str = data.get('date')
    content = data.get('content')

    if not date_str or not content:
        return jsonify({'success': False, 'error': 'Missing date or content'}), 400

    try:
        # Parse the date to ensure correct format
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')  # Updated variable name
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    try:
        new_entry = DiaryEntry(date=date_obj, content=content)  # Updated field name
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating diary entry: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@diary_bp.route('/delete/<int:id>', methods=['POST'])
def delete_diary(id):
    """
    Delete a diary entry by its ID.
    """
    try:
        entry = DiaryEntry.query.get(id)
        if not entry:
            return jsonify({'success': False, 'error': 'Diary entry not found.'}), 404

        db.session.delete(entry)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting diary entry {id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@diary_bp.route('/content/<int:id>', methods=['GET'])
def get_diary_content(id):
    """
    Render a specific diary entry for viewing and editing.
    """
    entry = DiaryEntry.query.get(id)
    if entry:
        return render_template(
            'diary/diary_content.html',
            content=entry.content,
            date=entry.date.strftime('%Y-%m-%d'),  # Updated field name
            id=entry.id
        )
    else:
        return jsonify({"error": "Diary entry not found"}), 404

@diary_bp.route('/update_content', methods=['POST'])
def update_diary_content():
    """
    Update the content of a diary entry.
    """
    data = request.get_json()
    diary_id = data.get('id')
    updated_content = data.get('content')

    if not diary_id or not updated_content:
        return jsonify({'success': False, 'error': 'Missing id or content'}), 400

    try:
        entry = DiaryEntry.query.get(diary_id)
        if not entry:
            return jsonify({'success': False, 'error': 'Diary entry not found.'}), 404

        entry.content = updated_content
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating diary entry {diary_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@diary_bp.route('/content_from_char', methods=['GET'])
def get_content_from_char():
    """
    Get remaining content from a specific character index for speech synthesis.
    """
    date_str = request.args.get('date')  # Diary date
    char_index = request.args.get('char_index')  # Cursor character index

    # Validate required parameters
    if not date_str or char_index is None:
        return jsonify({"error": "date and char_index parameters are required"}), 400

    # Validate date format
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')  # Updated field name
    except ValueError:
        return jsonify({"error": "date must be in YYYY-MM-DD format"}), 400

    # Convert char_index to integer
    try:
        char_index = int(char_index)
    except ValueError:
        return jsonify({"error": "char_index must be an integer"}), 400

    entry = DiaryEntry.query.filter_by(date=date_obj).first()  # Updated field name
    if entry:
        content = entry.content
        if 0 <= char_index < len(content):
            remaining_content = content[char_index:].replace('\n', ' ')
            return jsonify({"remaining_content": remaining_content})
        else:
            return jsonify({"error": f"Character index {char_index} is out of range. Valid range is 0 to {len(content)-1}"}), 400
    else:
        return jsonify({"error": "Diary entry not found"}), 404

@diary_bp.route('/index', methods=['GET'])
def show_diary_page_detail():
    """
    Render a different index page if needed.
    """
    return render_template('index.html')  # Ensure 'index.html' exists in your main templates directory
