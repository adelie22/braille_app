from flask import render_template, request, redirect, url_for, flash, g, send_file
from models import DiaryEntry
from extensions import db
from google.cloud import texttospeech
import os
import logging
from . import diary_bp

# Configure logging if not already done
logging.basicConfig(level=logging.DEBUG)

# Google TTS client initialization
tts_client = texttospeech.TextToSpeechClient()

@diary_bp.route('/')
def list_entries():
    """
    List all diary entries.
    """
    entries = DiaryEntry.query.order_by(DiaryEntry.entry_date.desc()).all()
    return render_template('diary/index.html', entries=entries)

@diary_bp.route('/add', methods=['GET', 'POST'])
@diary_bp.route('/add/<int:entry_id>', methods=['GET', 'POST'])
def add_entry(entry_id=None):
    """
    Add a new diary entry or edit an existing one.
    """
    entry = None
    if entry_id:
        entry = DiaryEntry.query.get(entry_id)
        if not entry:
            flash("Diary entry not found.", "error")
            return redirect(url_for('diary.list_entries'))

    if request.method == 'POST':
        # Read inputs from the Braille keyboard
        input_sequence = g.keyboard.read_input()

        if input_sequence:
            content = entry.content if entry else ''  # If editing, start with existing content
            for braille_byte in input_sequence:
                # Handle control bytes for editing content
                if 224 <= braille_byte <= 231:  # E0 to E7 control bytes
                    if braille_byte == 226:  # E2: Backspace
                        content = content[:-1]
                    elif braille_byte == 225:  # E1: Space
                        content += ' '
                    # Additional control inputs can be handled here
                    continue

                # Convert Braille byte to character
                braille_char = chr(0x2800 + braille_byte)
                content += braille_char

            if not content:
                flash("Converted content is empty. Please try again.", "error")
                return redirect(url_for('diary.add_entry', entry_id=entry_id) if entry else url_for('diary.add_entry'))

            # Save content to database
            if entry:
                entry.content = content
                flash("Diary entry updated successfully!", "success")
            else:
                entry = DiaryEntry(content=content)
                db.session.add(entry)
                flash("Diary entry added successfully!", "success")

            db.session.commit()
            return redirect(url_for('diary.list_entries'))

    # For GET requests, render the add_entry page, including existing content if editing
    return render_template('diary/add.html', entry=entry)

@diary_bp.route('/speak/<int:entry_id>')
def speak_entry(entry_id):
    """
    Convert a diary entry to speech and play it.
    """
    entry = DiaryEntry.query.get(entry_id)

    if not entry:
        flash("Diary entry not found.", "error")
        return redirect(url_for('diary.list_entries'))

    try:
        # Define paths
        blueprint_dir = os.path.dirname(__file__)
        audio_dir = os.path.join(blueprint_dir, 'audio_files')
        os.makedirs(audio_dir, exist_ok=True)
        audio_filename = f"entry_{entry_id}.mp3"
        audio_path = os.path.join(audio_dir, audio_filename)

        # Check if audio already exists
        if not os.path.exists(audio_path):
            # Synthesize speech
            synthesis_input = texttospeech.SynthesisInput(text=entry.content)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9,  # Slightly slower
                pitch=0.0
            )
            response = tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Save the audio file
            with open(audio_path, 'wb') as audio_file:
                audio_file.write(response.audio_content)
                logging.debug(f"Audio content written to {audio_path}")

        # Serve the audio file
        return send_file(
            audio_path,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name=audio_filename
        )

    except Exception as e:
        logging.error(f"Error during speech synthesis: {e}")
        flash(f"Error during speech synthesis: {e}", "error")
        return redirect(url_for('diary.list_entries'))

@diary_bp.route('/delete/<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    """
    Delete a diary entry by its ID.
    """
    entry = DiaryEntry.query.get(entry_id)
    if not entry:
        flash("Diary entry not found.", "error")
        return redirect(url_for('diary.list_entries'))
    try:
        db.session.delete(entry)
        db.session.commit()
        flash("Diary entry deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting diary entry {entry_id}: {e}")
        flash(f"Error deleting diary entry: {e}", "error")
    return redirect(url_for('diary.list_entries'))
