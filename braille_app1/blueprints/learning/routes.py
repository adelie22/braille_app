# blueprints/learning/routes.py

from . import learning_bp
from flask import render_template, request, session, g, redirect, url_for, flash, send_file, jsonify
from extensions import db
from models import EnGrade1
import louis
from google.cloud import texttospeech
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Path to your Braille translation table
BRAILLE_TABLE = "/home/guru/liblouis-3.21.0/tables/en-us-g1.ctb"

# Initialize Google TTS client
tts_client = texttospeech.TextToSpeechClient()

@learning_bp.route('/get_current_input_buffer')
def get_current_input_buffer():
    """
    Returns the current input buffer and any control signals from the hardware keyboard.
    """
    input_buffer = g.keyboard.get_current_input_buffer()

    # Peek at a control signal without consuming it
    control_signal = g.keyboard.peek_control_signal()
    if control_signal:
        logging.debug(f"Control signal included in response: {control_signal}")
    else:
        logging.debug("No control signal available.")

    return jsonify({'input_buffer': input_buffer, 'control_signal': control_signal})

@learning_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the Learning section.
    GET: Displays the current word or selects a new word if none exists.
    POST: Processes input from the Braille keyboard or control signals.
    """
    if request.method == 'GET':
        # Enable buffered mode at the start of a learning session
        g.keyboard.set_buffered_mode(True)
        logging.debug("Buffered mode set to True for learning session.")

        # Check if there's a current word in the session
        if 'current_word' in session and session['current_word']:
            # Use the existing word
            target_word = session['current_word']
            word_entry = EnGrade1.query.filter_by(word=target_word).first()
            if not word_entry:
                # Word not found in DB, select a new word
                word_entry = EnGrade1.query.order_by(db.func.random()).first()
                if word_entry:
                    session['current_word'] = word_entry.word.lower()
                else:
                    flash("No words available in the database.", "error")
                    logging.warning("No words found in the database.")
                    return render_template('learning/index.html')
        else:
            # Select a new word from the DB
            word_entry = EnGrade1.query.order_by(db.func.random()).first()
            if word_entry:
                session['current_word'] = word_entry.word.lower()
            else:
                flash("No words available in the database.", "error")
                logging.warning("No words found in the database.")
                return render_template('learning/index.html')

        session['user_input'] = ''  # Clear any previous user input
        audio_url = url_for('learning.audio', word_id=word_entry.id)
        logging.debug(f"Selected word: {word_entry.word} with ID: {word_entry.id}")
        return render_template('learning/index.html', target_word=word_entry.word, audio_url=audio_url)

    elif request.method == 'POST':
        queue_contents = g.keyboard.get_queue_contents()
        logging.debug(f"Queue contents before processing POST request: {queue_contents}")
        # Consume signals from the queue
        control_signal_item = None

        while True:
            signal = g.keyboard.read_input()
            if not signal:
                break
            if signal.get('type') == 'control':
                control_signal_item = signal
                logging.debug(f"Control signal detected: {control_signal_item.get('data')}")

        if control_signal_item:
            control_signal = control_signal_item.get('data')
            if control_signal == 'Enter':
                # Handle 'Enter' control signal
                return handle_enter_signal()
            elif control_signal == 'Back':
                return handle_back_signal()
            elif control_signal == 'Ctrl + Left':
                pass
                # Handle 'Ctrl + Left' control signal
                #return handle_ctrl_left_signal_learning()
            else:
                # Handle other control signals if necessary
                logging.debug(f"Unhandled control signal: {control_signal}")
                flash(f"Unhandled control signal: {control_signal}", "info")
                return redirect(url_for('learning.index'))
        else:
            # No control signal detected
            logging.debug("No control signal detected during POST request.")
            return redirect(url_for('learning.index'))

@learning_bp.route('/audio/<int:word_id>')
def audio(word_id):
    """
    Generates and serves the audio file for the given word ID using Google TTS.
    Caches the audio to disk to avoid redundant API calls.
    """
    # Retrieve the word from the database
    word_entry = EnGrade1.query.get(word_id)
    if not word_entry:
        flash("Word not found.", "error")
        logging.error(f"Word with ID {word_id} not found in the database.")
        return redirect(url_for('learning.index'))

    # Define the audio file path
    blueprint_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(blueprint_dir, 'audio_files')
    os.makedirs(audio_dir, exist_ok=True)  # Create directory if it doesn't exist
    sanitized_word = ''.join(c for c in word_entry.word if c.isalnum() or c in (' ', '_')).rstrip()
    audio_path = os.path.join(audio_dir, f"{sanitized_word}.mp3")

    # Check if audio file already exists (caching)
    if not os.path.exists(audio_path):
        try:
            # Prepare the text input for TTS using SSML
            synthesis_input = texttospeech.SynthesisInput(ssml=f"<speak>{word_entry.word}</speak>")

            # Build the voice request (language code and voice selection)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )

            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9,  # Adjust speaking rate if necessary
                pitch=0.0  # Adjust pitch if necessary
            )

            # Perform the text-to-speech request
            response = tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )

            # Save the audio content to a file
            with open(audio_path, 'wb') as out:
                out.write(response.audio_content)
                logging.debug(f'Audio content written to {audio_path}')
        except Exception as e:
            logging.error(f"Error during TTS synthesis for word '{word_entry.word}': {e}")
            flash("Error generating audio for the word.", "error")
            return redirect(url_for('learning.index'))

    # Serve the audio file
    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=f"{sanitized_word}.mp3"
    )

def handle_enter_signal():
    """
    Handles the 'Enter' control signal by processing the input buffer.
    """
    if g.keyboard.buffered_mode:
        with g.keyboard.lock:
            input_buffer = list(g.keyboard.input_buffer)
            g.keyboard.input_buffer.clear()
        if input_buffer:
            # Process the input_buffer as braille_input
            input_sequence = input_buffer
            logging.debug(f"Buffered Braille Input: {input_sequence}")

            # Convert binary strings to Braille characters
            braille_chars = ''
            for binary_str in input_sequence:
                braille_value = 0
                for i in range(6):
                    bit = binary_str[5 - i]  # Reverse order of bits
                    if bit == '1':
                        braille_value |= (1 << i)
                braille_char = chr(0x2800 + braille_value)
                braille_chars += braille_char
            logging.debug(f"Braille Characters: {braille_chars}")

            # Translate using liblouis
            try:
                entered_word = louis.backTranslateString([BRAILLE_TABLE], braille_chars).strip().lower()
                logging.debug(f"Translated Word: {entered_word}")
            except Exception as e:
                logging.error(f"Error during translation: {e}")
                flash(f"Error during translation: {e}", "error")
                return redirect(url_for('learning.index'))

            # Compare with target word
            target_word = session.get('current_word', None)
            if entered_word == target_word:
                # Correct input logic
                flash("Correct!", "success")
                logging.info("User entered the correct word.")
                session['user_input'] = ''  # Clear user input
                # Generate feedback audio
                generate_feedback_audio("Correct! The next word is coming up.", 'feedback.mp3')
                # Select the next word
                new_word_entry = EnGrade1.query.order_by(db.func.random()).first()
                if new_word_entry:
                    session['current_word'] = new_word_entry.word.lower()
                    audio_url = url_for('learning.audio', word_id=new_word_entry.id)
                    logging.debug(f"Next word selected: {new_word_entry.word} with ID: {new_word_entry.id}")
                    # Disable buffered mode temporarily if needed
                    # g.keyboard.set_buffered_mode(False)
                    return render_template(
                        'learning/index.html',
                        target_word=new_word_entry.word,
                        audio_url=audio_url,
                        feedback_audio_url=url_for('learning.message_audio', filename='feedback.mp3')
                    )
                else:
                    flash("No more words available in the database.", "error")
                    logging.warning("No more words available after correct input.")
                    return render_template('learning/index.html')
            else:
                # Incorrect input logic
                flash("Incorrect input.", "error")
                logging.info(f"User entered incorrect word: {entered_word} (expected: {target_word})")
                session['user_input'] = entered_word  # Store incorrect input for display

                # Generate feedback audio saying "Wrong"
                feedback_text = "Wrong."
                generate_feedback_audio(feedback_text, 'feedback.mp3')

                # Render the template with the same target word and feedback audio
                word_entry = EnGrade1.query.filter_by(word=target_word).first()
                if word_entry:
                    audio_url = url_for('learning.audio', word_id=word_entry.id)
                else:
                    audio_url = None
                return render_template(
                    'learning/index.html',
                    target_word=target_word,
                    audio_url=audio_url,
                    feedback_audio_url=url_for('learning.message_audio', filename='feedback.mp3')
                )
        else:
            logging.debug("Input buffer is empty upon 'Enter' signal.")
            flash("No input detected.", "error")
            return redirect(url_for('learning.index'))
    else:
        logging.debug("Buffered mode is not enabled upon 'Enter' signal.")
        flash("Buffered mode is not enabled.", "error")
        return redirect(url_for('learning.index'))

def handle_back_signal():
    """
    Handles the 'Back' control signal by removing the last item from the input buffer.
    """
    with g.keyboard.lock:
        if g.keyboard.input_buffer:
            removed_item = g.keyboard.input_buffer.pop()
            logging.debug(f"Removed last item from input buffer: {removed_item}")
            flash("Last character removed.", "info")
        else:
            logging.debug("Input buffer is empty; nothing to remove.")
            flash("No input to remove.", "info")
    return redirect(url_for('learning.index'))

@learning_bp.route('/instructions_audio/<filename>')
def instructions_audio(filename):
    """
    Serves the instructions audio file.
    """
    blueprint_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(blueprint_dir, 'audio_files')
    audio_path = os.path.join(audio_dir, filename)

    if not os.path.exists(audio_path):
        flash("Instructions audio not found.", "error")
        logging.error(f"Instructions audio file '{filename}' not found.")
        return redirect(url_for('learning.index'))

    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=filename
    )

def generate_feedback_audio(text, filename):
    """
    Generates an audio file for the given text using Google TTS.
    """
    try:
        # Define the audio file path
        blueprint_dir = os.path.dirname(__file__)
        audio_dir = os.path.join(blueprint_dir, 'audio_files')
        os.makedirs(audio_dir, exist_ok=True)  # Create directory if it doesn't exist
        audio_path = os.path.join(audio_dir, filename)

        # Prepare the text input for TTS
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request (language code and voice selection)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,  # Adjust speaking rate if necessary
            pitch=0.0  # Adjust pitch if necessary
        )

        # Perform the text-to-speech request
        response = tts_client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Save the audio content to a file
        with open(audio_path, 'wb') as out:
            out.write(response.audio_content)
            logging.debug(f'Feedback audio content written to {audio_path}')
    except Exception as e:
        logging.error(f"Error during TTS synthesis for feedback: {e}")

@learning_bp.route('/message_audio/<filename>')
def message_audio(filename):
    """
    Serves the message audio file (e.g., "Correct! The next word is...").
    """
    blueprint_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(blueprint_dir, 'audio_files')
    audio_path = os.path.join(audio_dir, filename)

    if not os.path.exists(audio_path):
        flash("Message audio not found.", "error")
        logging.error(f"Message audio file '{filename}' not found.")
        return redirect(url_for('learning.index'))

    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=filename
    )

