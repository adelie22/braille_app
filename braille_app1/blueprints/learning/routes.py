# blueprints/learning/routes.py

from . import learning_bp
from flask import render_template, request, session, g, redirect, url_for, flash, send_file
from extensions import db
from models import EnGrade1
import louis  # Using louis as per your preference
from google.cloud import texttospeech
import io
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Path to your Braille translation table
BRAILLE_TABLE = ["en-us-g1.ctb"]  # Ensure the table is in the default directory or provide the absolute path

# Initialize Google TTS client
tts_client = texttospeech.TextToSpeechClient()

@learning_bp.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the Learning section.
    GET: Selects a random word, displays it, and prepares its audio.
    POST: Takes input from the braille keyboard, compares it to the target word, provides feedback,
          and if incorrect, provides the correct braille pattern in speech.
    """
    if request.method == 'GET':
        # Select a random word from the DB
        word_entry = EnGrade1.query.order_by(db.func.rand()).first()
        if word_entry:
            session['current_word_id'] = word_entry.id  # Store word ID in session for comparison
            session['current_word'] = word_entry.word.lower()  # Store word in session for comparison
            # Generate audio URL (served via a separate route)
            audio_url = url_for('learning.audio', word_id=word_entry.id)
            return render_template('learning/index.html', target_word=word_entry.word, audio_url=audio_url)
        else:
            flash("No words available in the database.", "error")
            return render_template('learning/index.html')

    elif request.method == 'POST':
        target_word = session.get('current_word', None)
        if not target_word:
            flash("No target word found. Please try again.", "error")
            return redirect(url_for('learning.index'))

        # Read inputs from the braille keyboard
        input_sequence = g.keyboard.read_input()
        logging.debug(f"Raw Braille Input: {input_sequence}")

        if input_sequence:
            # Convert braille bytes to string using Liblouis
            try:
                # Convert list of bytes to a bytes object
                braille_bytes = bytes(input_sequence)
                logging.debug(f"Braille Bytes: {braille_bytes}")

                # Map braille bytes to Unicode braille characters
                braille_chars = ''.join([chr(0x2800 + byte) for byte in input_sequence])
                logging.debug(f"Braille Characters: {braille_chars}")

                # Translate braille to string
                entered_word = louis.translateString(BRAILLE_TABLE, braille_chars).strip().lower()
                logging.debug(f"Translated Word: {entered_word}")

                # Convert input_sequence to dot numbers for display
                user_input_dots = []
                for byte in input_sequence:
                    dots = []
                    for i in range(6):  # Dots 1-6
                        if byte & (1 << i):
                            dots.append(str(i+1))
                    if dots:
                        user_input_dots.append(','.join(dots))
                    else:
                        user_input_dots.append('')  # Handle empty braille
                user_input_dots_str = ' '.join(user_input_dots)
                logging.debug(f"User Input Dots: {user_input_dots_str}")

                # Compare with target word
                if entered_word == target_word:
                    feedback = "Correct!"
                    flash(feedback, "success")
                    # Optionally, you can select a new word or let the user continue with the same
                    # For this example, let's select a new word
                    new_word_entry = EnGrade1.query.order_by(db.func.rand()).first()
                    if new_word_entry:
                        session['current_word_id'] = new_word_entry.id
                        session['current_word'] = new_word_entry.word.lower()
                        # Generate new audio URL
                        new_audio_url = url_for('learning.audio', word_id=new_word_entry.id)
                        return render_template('learning/index.html', target_word=new_word_entry.word, audio_url=new_audio_url)
                    else:
                        flash("No more words available in the database.", "error")
                        return render_template('learning/index.html')
                else:
                    feedback = f"Wrong! You entered: '{entered_word}'. The correct word was: '{target_word}'."
                    flash(feedback, "error")

                    # Generate pattern string based on the correct word
                    correct_word_entry = EnGrade1.query.filter_by(word=target_word).first()
                    if correct_word_entry:
                        correct_braille_bytes = correct_word_entry.bin  # Assuming 'bin' is a list of integers representing braille bytes

                        # Convert each byte to braille dot numbers
                        pattern_strings = []
                        for byte in correct_braille_bytes:
                            dots = []
                            for i in range(6):  # Dots 1-6
                                if byte & (1 << i):
                                    dots.append(str(i+1))
                            if dots:
                                pattern_strings.append(','.join(dots))
                            else:
                                pattern_strings.append('')  # Handle empty braille

                        # Join the patterns with spaces
                        pattern_speech = ' '.join(pattern_strings)
                        logging.debug(f"Pattern Speech String: {pattern_speech}")

                        # Define the pattern audio filename
                        pattern_audio_filename = f"{target_word}_pattern.mp3"

                        # Define the pattern audio file path
                        blueprint_dir = os.path.dirname(__file__)
                        audio_dir = os.path.join(blueprint_dir, 'audio_files')
                        os.makedirs(audio_dir, exist_ok=True)  # Create directory if it doesn't exist
                        pattern_audio_path = os.path.join(audio_dir, pattern_audio_filename)

                        # Check if pattern audio already exists (caching)
                        if not os.path.exists(pattern_audio_path):
                            # Synthesize speech for the pattern
                            synthesis_input = texttospeech.SynthesisInput(text=pattern_speech)
                            voice = texttospeech.VoiceSelectionParams(
                                language_code="en-US",
                                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                            )
                            audio_config = texttospeech.AudioConfig(
                                audio_encoding=texttospeech.AudioEncoding.MP3
                            )
                            response = tts_client.synthesize_speech(
                                input=synthesis_input, voice=voice, audio_config=audio_config
                            )

                            # Save the audio content to a file
                            with open(pattern_audio_path, 'wb') as out:
                                out.write(response.audio_content)
                                logging.debug(f'Pattern audio content written to {pattern_audio_path}')
                        else:
                            logging.debug(f'Pattern audio already exists at {pattern_audio_path}')

                        # Generate the pattern audio URL
                        pattern_audio_url = url_for('learning.pattern_audio', filename=pattern_audio_filename)

                        # Render the template with both word audio and pattern audio, and user input
                        return render_template(
                            'learning/index.html',
                            target_word=target_word,
                            audio_url=url_for('learning.audio', word_id=correct_word_entry.id),
                            pattern_audio_url=pattern_audio_url,
                            user_input=entered_word,
                            user_input_dots=user_input_dots_str
                        )
                    else:
                        logging.error(f"Could not find the word entry for '{target_word}'.")
                        flash("Internal error: Correct word not found in the database.", "error")
            except Exception as e:
                feedback = f"Error during translation: {e}"
                flash(feedback, "error")
        else:
            flash("No input received from the braille keyboard.", "error")

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
        return redirect(url_for('learning.index'))

    # Define the audio file path
    blueprint_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(blueprint_dir, 'audio_files')
    os.makedirs(audio_dir, exist_ok=True)  # Create directory if it doesn't exist
    audio_path = os.path.join(audio_dir, f"{word_entry.word}.mp3")

    # Check if audio file already exists (caching)
    if not os.path.exists(audio_path):
        try:
            # Prepare the text input for TTS
            synthesis_input = texttospeech.SynthesisInput(text=word_entry.word)

            # Build the voice request (language code and voice selection)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",  # Adjust as needed
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )

            # Select the type of audio file you want returned
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3  # Can be MP3, LINEAR16, etc.
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
        download_name=f"{word_entry.word}.mp3"  # Updated keyword argument for Flask >=2.0
    )

@learning_bp.route('/pattern_audio/<filename>')
def pattern_audio(filename):
    """
    Serves the pattern audio file.
    """
    blueprint_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(blueprint_dir, 'audio_files')
    audio_path = os.path.join(audio_dir, filename)

    if not os.path.exists(audio_path):
        flash("Pattern audio not found.", "error")
        return redirect(url_for('learning.index'))

    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=filename  # Updated keyword argument for Flask >=2.0
    )
