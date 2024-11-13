# blueprints/learning/routes.py

from . import learning_bp
from flask import render_template, request, session, g, redirect, url_for, flash, send_file
from extensions import db
from models import EnGrade1
import louis
from google.cloud import texttospeech
import io
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Path to your Braille translation table
BRAILLE_TABLE = ["en-us-g1.ctb"]  # Ensure the table is in the correct directory or provide the absolute path

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
            try:
                # Convert input_sequence to Braille Unicode characters
                braille_chars = ''.join([chr(0x2800 + byte) for byte in input_sequence])
                logging.debug(f"Braille Characters: {braille_chars}")

                # Use louis.backTranslateString to translate Braille Unicode string to text
                entered_word = louis.backTranslateString(BRAILLE_TABLE, braille_chars).strip().lower()
                logging.debug(f"Translated Word: {entered_word}")

                # For display purposes, extract dot numbers for each Braille byte
                user_input_dots_list = []
                for byte in input_sequence:
                    dots = []
                    for i in range(6):  # Dots 1-6
                        if byte & (1 << i):
                            dots.append(str(i+1))
                    user_input_dots_list.append(' '.join(dots))
                user_input_dots_str = ' | '.join(user_input_dots_list)
                logging.debug(f"User Input Dots: {user_input_dots_str}")

                # Compare with target word
                if entered_word == target_word:
                    # Generate "Correct! The next word is ___" audio
                    # Select a new word
                    new_word_entry = EnGrade1.query.order_by(db.func.rand()).first()
                    if new_word_entry:
                        session['current_word'] = new_word_entry.word.lower()
                        next_word = new_word_entry.word
                        # Generate the combined message with SSML pauses
                        message_text = f"Correct!<break time='500ms'/> The next word is {next_word}."
                        # Generate the audio message
                        message_audio_filename = "correct_next_word.mp3"
                        audio_dir = os.path.join(os.path.dirname(__file__), 'audio_files')
                        os.makedirs(audio_dir, exist_ok=True)
                        message_audio_path = os.path.join(audio_dir, message_audio_filename)

                        # Synthesize speech for the message with adjusted speaking rate and SSML
                        synthesis_input = texttospeech.SynthesisInput(ssml=f"<speak>{message_text}</speak>")
                        voice = texttospeech.VoiceSelectionParams(
                            language_code="en-US",
                            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                        )
                        audio_config = texttospeech.AudioConfig(
                            audio_encoding=texttospeech.AudioEncoding.MP3,
                            speaking_rate=0.9,  # Adjust speaking rate to be slightly slower
                            pitch=0.0  # Adjust pitch if necessary
                        )
                        response = tts_client.synthesize_speech(
                            input=synthesis_input, voice=voice, audio_config=audio_config
                        )

                        # Save the audio content to a file
                        with open(message_audio_path, 'wb') as out:
                            out.write(response.audio_content)
                            logging.debug(f'Correct message audio content written to {message_audio_path}')

                        # Generate the message audio URL
                        message_audio_url = url_for('learning.message_audio', filename=message_audio_filename)

                        # Generate audio URL for the next word
                        audio_url = url_for('learning.audio', word_id=new_word_entry.id)

                        return render_template(
                            'learning/index.html',
                            target_word=next_word,
                            audio_url=audio_url,
                            message_audio_url=message_audio_url
                        )
                    else:
                        flash("No more words available in the database.", "error")
                        return render_template('learning/index.html')
                else:
                    feedback = "Wrong!"
                    flash(feedback, "error")

                    # Generate instructions automatically
                    instructions_list = []
                    for i, letter in enumerate(target_word):
                        # Get the Braille characters for the letter with adjusted modes
                        # translation_mode = louis.noContractions | louis.dotsIO
                        braille_chars_for_letter = louis.translateString(BRAILLE_TABLE, letter)

                        if braille_chars_for_letter:
                            # Convert each Braille character to dots representation
                            for braille_char in braille_chars_for_letter:
                                unicode_value = ord(braille_char)
                                braille_byte = unicode_value - 0x2800
                                dots = [str(j + 1) for j in range(6) if braille_byte & (1 << j)]
                                
                                if dots:  # Ensure dots are valid before adding
                                    dots_str = ','.join(dots)
                                    instructions_list.append(f"{dots_str}<break time='300ms'/> for<break time='200ms'/> {letter}")


                    # Combine the instructions into one string
                    instructions_text = "Press<break time='300ms'/> " + ';<break time="500ms"/> '.join(instructions_list) + '.'
                    logging.debug(f"Instructions Text with SSML: {instructions_text}")

                    # Generate the instructions audio
                    instructions_audio_filename = f"{target_word}_instructions.mp3"
                    blueprint_dir = os.path.dirname(__file__)
                    audio_dir = os.path.join(blueprint_dir, 'audio_files')
                    os.makedirs(audio_dir, exist_ok=True)
                    instructions_audio_path = os.path.join(audio_dir, instructions_audio_filename)

                    # Check if instructions audio already exists (caching)
                    if not os.path.exists(instructions_audio_path):
                        # Synthesize speech for the instructions with adjusted speaking rate and SSML
                        synthesis_input = texttospeech.SynthesisInput(ssml=f"<speak>{instructions_text}</speak>")
                        voice = texttospeech.VoiceSelectionParams(
                            language_code="en-US",
                            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
                        )
                        audio_config = texttospeech.AudioConfig(
                            audio_encoding=texttospeech.AudioEncoding.MP3,
                            speaking_rate=0.9,  # Adjust speaking rate to be slightly slower
                            pitch=0.0  # Adjust pitch if necessary
                        )
                        response = tts_client.synthesize_speech(
                            input=synthesis_input, voice=voice, audio_config=audio_config
                        )

                        # Save the audio content to a file
                        with open(instructions_audio_path, 'wb') as out:
                            out.write(response.audio_content)
                            logging.debug(f'Instructions audio content written to {instructions_audio_path}')
                    else:
                        logging.debug(f'Instructions audio already exists at {instructions_audio_path}')

                    # Generate the instructions audio URL
                    instructions_audio_url = url_for('learning.instructions_audio', filename=instructions_audio_filename)

                    # Render the template with the instructions audio
                    return render_template(
                        'learning/index.html',
                        target_word=target_word,
                        instructions_audio_url=instructions_audio_url,
                        user_input=entered_word,
                        user_input_dots=user_input_dots_str
                    )
            except Exception as e:
                feedback = f"Error during translation: {e}"
                logging.error(feedback)
                flash(feedback, "error")
                return redirect(url_for('learning.index'))
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
                speaking_rate=0.9,  # Adjust speaking rate to be slightly slower
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
        download_name=f"{word_entry.word}.mp3"
    )

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
        return redirect(url_for('learning.index'))

    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=filename
    )

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
        return redirect(url_for('learning.index'))

    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=filename
    )
