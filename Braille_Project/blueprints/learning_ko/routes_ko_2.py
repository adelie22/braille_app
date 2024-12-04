# blueprints/learning_ko/routes.py

from . import learning_bp_ko
from flask import (
    render_template, request, session, redirect, url_for,
    flash, send_file, jsonify
)
from extensions import db
from models import KoVoca, KoGrade1
from BrailleToKorean.BrailleToKor import BrailleToKor
from KorToBraille.KorToBraille import KorToBraille
from google.cloud import texttospeech
import os
import logging
import hashlib
from interfaces.hardware_keyboard import HardwareBrailleKeyboard

# Configure logging
logging.basicConfig(level=logging.DEBUG)

#===========================LED관련==================================================

import time
from threading import Timer

# 싱글턴 인스턴스 가져오기 (적절한 포트로 변경)
keyboard = HardwareBrailleKeyboard.get_instance(port='/dev/ttyACM0')  # 실제 포트로 변경

#===========================LED관련==================================================

# Initialize Google TTS client
tts_client = texttospeech.TextToSpeechClient()

# Define directories for different types of audio
AUDIO_TYPES = {
    'word': 'words',
    'feedback': 'feedback',
}

@learning_bp_ko.route('/led_control', methods=['POST'])
def led_control():
    """
    Handles LED control signals from the frontend.
    Expects JSON data with 'leds' (comma-separated string of LED numbers) and 'action' ('ON' or 'OFF').
    """
    data = request.get_json()
    leds = data.get('leds')  # 예: "4"
    action = data.get('action')  # 'ON' 또는 'OFF'

    if not leds or not action:
        return jsonify({"error": "Invalid parameters"}), 400

    # Parse LEDs into a list of integers
    try:
        led_numbers = [int(num) for num in leds.split(',')]
        keyboard.queue_led_command(led_numbers, action=action)  # Hardware LED 제어
        logging.info(f"LED control command received: {action} for LEDs {led_numbers}")
        return jsonify({"status": "success", "action": action, "leds": led_numbers})
    except ValueError:
        logging.error(f"Invalid LED numbers provided: {leds}")
        return jsonify({"error": "Invalid LED numbers"}), 400
    except Exception as e:
        logging.error(f"Error processing LED command: {e}")
        return jsonify({"error": "Internal server error"}), 500


def braille_number_to_dots(number):
    """
    점자 번호를 해당하는 점자 버튼(1~6번) 리스트로 변환합니다.
    예: 3 -> [1, 3]
    """
    dots = []
    for i in range(1, 7):
        if number & (1 << (i - 1)):
            dots.append(i)
    if dots:
        return dots
    return []

def generate_braille_buttons_feedback(word):
    braille_buttons_feedback = []
    
    # 1. 한국어 단어를 점자 유니코드로 번역
    b = KorToBraille()
    braille_result = b.korTranslate(word)
    logging.debug(f"Braille Unicode for '{word}': {braille_result}")
    
    # 2. 점자 유니코드에서 점자 번호 추출
    braille_numbers = [ord(char) - 0x2800 for char in braille_result]
    logging.debug(f"Braille Numbers: {braille_numbers}")
    
    # 3. 점자 번호를 리스트에 저장하고 버튼 조합 생성
    braille_buttons_feedback = [braille_number_to_dots(num) for num in braille_numbers[:-1]]
    
    return braille_buttons_feedback

def get_audio_path(text, audio_type='feedback'):
    """
    Generate a consistent file path for the audio based on text and type.
    """
    sanitized_text = ''.join(
        c for c in text if c.isalnum() or c in (' ', '_')
    ).rstrip().replace(' ', '_')
    hash_digest = hashlib.md5(text.encode()).hexdigest()  # Ensures uniqueness
    audio_dir = os.path.join(
        os.path.dirname(__file__), 'audio_files',
        AUDIO_TYPES.get(audio_type, 'feedback')
    )
    os.makedirs(audio_dir, exist_ok=True)
    return os.path.join(audio_dir, f"{sanitized_text}_{hash_digest}.mp3")

def generate_feedback_audio(text, filename=None):
    """
    Generates an audio file for the given feedback text using Google TTS.
    Caches the audio to disk to avoid redundant API calls.
    Returns the URL to the audio file.
    """
    if not filename:
        # Generate filename based on text if not provided
        filename = f"{text.replace(' ', '_').lower()}.mp3"
    audio_path = get_audio_path(text, 'feedback')
    
    if not os.path.exists(audio_path):
        try:
            # Prepare the text input for TTS
            synthesis_input = texttospeech.SynthesisInput(text=text)

            # Build the voice request using config parameters
            voice = texttospeech.VoiceSelectionParams(
                language_code="ko-KR",
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
            logging.error(f"Error during TTS synthesis for feedback '{text}': {e}")
            return None  # Return None if audio generation fails

    # Generate the URL for the feedback audio file
    feedback_audio_url = url_for('learning_ko.message_audio', filename=os.path.basename(audio_path))
    return feedback_audio_url

@learning_bp_ko.route('/message_audio/<filename>')
def message_audio(filename):
    """
    Serves the message audio file (e.g., "Delete", "Left", "Right").
    """
    blueprint_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(blueprint_dir, 'audio_files', 'feedback')
    audio_path = os.path.join(audio_dir, filename)

    if not os.path.exists(audio_path):
        flash("Message audio not found.", "error")
        logging.error(f"Message audio file '{filename}' not found.")
        return redirect(url_for('learning_ko.index'))

    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=filename
    )

@learning_bp_ko.route('/audio/<int:word_id>')
def audio(word_id):
    """
    Generates and serves the audio file for the given word ID using Google TTS.
    Caches the audio to disk to avoid redundant API calls.
    """
    # Retrieve the word from the database
    word_entry = KoGrade1.query.get(word_id)
    if not word_entry:
        flash("Word not found.", "error")
        logging.error(f"Word with ID {word_id} not found in the database.")
        return redirect(url_for('learning_ko.index'))

    # Define the audio file path
    blueprint_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(blueprint_dir, 'audio_files', 'words')
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
                language_code="ko-KR",
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
            return redirect(url_for('learning_ko.index'))

    # Serve the audio file
    return send_file(
        audio_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=f"{sanitized_word}.mp3"
    )

@learning_bp_ko.route('/get_current_input_buffer')
def get_current_input_buffer():
    """
    Returns the current input buffer and cursor position.
    """
    input_buffer = keyboard.get_current_input_buffer()
    cursor_position = keyboard.get_cursor_position()
    control_signal = keyboard.peek_control_signal()
    
    if control_signal:
        logging.debug(f"Control signal included in response: {control_signal}")
    else:
        logging.debug("No control signal available.")

    return jsonify({
        'input_buffer': input_buffer, 
        'cursor_position': cursor_position,
        'control_signal': control_signal
    })

@learning_bp_ko.route('/ko/2', methods=['GET', 'POST'])
def index():
    """
    Handles the Learning section.
    GET: Displays the current word or selects a new word if none exists.
    POST: Processes input from the Braille keyboard or control signals.
    """
    if request.method == 'GET':
        # Enable buffered mode at the start of a learning session
        keyboard.set_buffered_mode(True)
        logging.debug("Buffered mode set to True for learning session.")

        # Attempt to retrieve the current word from the session
        target_word_id = session.get('current_word_id')

        if target_word_id:
            # Fetch the word from the database
            word_entry = KoGrade1.query.get(target_word_id)
            if not word_entry:
                logging.warning(f"Word with ID '{target_word_id}' not found in the database. Selecting a new word.")
        else:
            word_entry = None

        # If the word is not found or not set, select a new word
        if not word_entry:
            # Replace db.func.rand() with db.func.random() if using PostgreSQL or SQLite
            word_entry = KoGrade1.query.order_by(db.func.rand()).first()
            if word_entry:
                # Update the session with the new word
                session['current_word_id'] = word_entry.id
                session['word_audio_played'] = False  # Initialize flag
                logging.debug(f"Selected new word: {word_entry.word} with ID: {word_entry.id}")
            else:
                # Handle the case where no words are available in the database
                flash("No words available in the database.", "error")
                logging.warning("No words found in the database.")
                return render_template('learning_ko/ko_2.html')

        # Determine whether to play word audio
        word_audio_played = session.get('word_audio_played', False)
        if not word_audio_played:
            audio_url = url_for('learning_ko.audio', word_id=word_entry.id)
            session['word_audio_played'] = True  # Set flag to prevent replay
            logging.debug(f"Word audio will be played: {audio_url}")
        else:
            audio_url = None  # Do not play audio again

        # Check if there's a feedback audio to play
        feedback_audio_url = session.pop('feedback_audio_url', None)

        return render_template('learning_ko/ko_2.html', target_word=word_entry.word, audio_url=audio_url, feedback_audio_url=feedback_audio_url)

    elif request.method == 'POST':
        control_signal_item = None

        while True:
            signal = keyboard.read_input()
            if not signal:
                break
            if signal.get('type') == 'control':
                control_signal_item = signal
                logging.debug(f"Control signal detected: {control_signal_item.get('data')}")

        if control_signal_item:
            control_signal = control_signal_item.get('data')
            logging.debug(f"Handling control signal: {control_signal}")
            if control_signal == 'Enter':
                return handle_enter_signal()
            elif control_signal == 'Back':
                return handle_back_signal()
            elif control_signal == 'Left':
                return handle_left_signal()
            elif control_signal == 'Right':
                return handle_right_signal()
            elif control_signal == 'Ctrl+Enter':
                return handle_ctrl_enter_signal()
            elif control_signal == 'Ctrl+Backspace':
                return handle_ctrl_backspace_signal()
            elif control_signal in ['Ctrl + Left', 'Ctrl + Right', 'Ctrl', 'Up', 'Down', 'Space', 'Ctrl + Up', 'Ctrl + Down', 'Ctrl + Space']:
                # Handle other Ctrl + directions if needed
                logging.debug(f"Unhandled control signal: {control_signal}")
                flash(f"Unhandled control signal: {control_signal}", "info")
                return redirect(url_for('learning_ko.index'))
            else:
                # Handle other control signals if necessary
                logging.debug(f"Unhandled control signal: {control_signal}")
                flash(f"Unhandled control signal: {control_signal}", "info")
                return redirect(url_for('learning_ko.index'))
        else:
            # No control signal detected
            logging.debug("No control signal detected during POST request.")
            return redirect(url_for('learning_ko.index'))

#------------------------------------------Functions--------------------------

def handle_enter_signal():
    """
    Handles the 'Enter' control signal by processing the input buffer.
    Generates feedback audio with correct Braille button instructions if the input is wrong.
    """
    if keyboard.buffered_mode and keyboard.input_buffer:
        with keyboard.lock:
            input_buffer = list(keyboard.input_buffer)
            keyboard.input_buffer = []
            keyboard.cursor_position = 0  # Reset cursor position

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

            # Translate Braille to text using liblouis
            try:
                b = BrailleToKor()
                entered_word = b.translation(braille_chars).strip().lower()
                logging.debug(f"Translated Word: {entered_word}")
            except Exception as e:
                logging.error(f"Error during translation: {e}")
                flash(f"Error during translation: {e}", "error")
                return redirect(url_for('learning_ko.index'))

            # Retrieve the target word from the session
            target_word_id = session.get('current_word_id', None)
            if not target_word_id:
                logging.error("No target word ID in session during Enter signal handling.")
                flash("No target word selected.", "error")
                return redirect(url_for('learning_ko.index'))

            target_word_entry = KoGrade1.query.get(target_word_id)
            if not target_word_entry:
                logging.error(f"Target word with ID '{target_word_id}' not found.")
                flash("Target word not found.", "error")
                return redirect(url_for('learning_ko.index'))
            target_word = target_word_entry.word.lower()

            if entered_word == target_word:
                # Correct input logic
                flash("Correct!", "success")
                logging.info("User entered the correct word.")
                # Generate feedback audio for correct input
                feedback_audio_url = generate_feedback_audio('정답입니다. 다음 단어는', 'feedback_correct.mp3')
                if feedback_audio_url:
                    session['feedback_audio_url'] = feedback_audio_url
                # Select the next word
                new_word_entry = KoGrade1.query.order_by(db.func.rand()).first()
                if new_word_entry:
                    session['current_word_id'] = new_word_entry.id
                    session['word_audio_played'] = False  # Reset flag for new word
                    audio_url = url_for('learning_ko.audio', word_id=new_word_entry.id)
                    logging.debug(f"Next word selected: {new_word_entry.word} with ID: {new_word_entry.id}")
                else:
                    flash("No more words available in the database.", "error")
                    logging.warning("No more words available after correct input.")
                    audio_url = None

                return render_template(
                    'learning_ko/ko_2.html',
                    target_word=new_word_entry.word if new_word_entry else None,
                    audio_url=audio_url,
                    feedback_audio_url=feedback_audio_url
                )
            else:
                # Incorrect input logic
                flash("Incorrect input.", "error")
                logging.info(f"User entered incorrect word: {entered_word} (expected: {target_word})")

                # Generate Braille button feedback for each letter in the target word
                braille_feedback = generate_braille_buttons_feedback(target_word)

                # 포맷팅: 각 점자 버튼 리스트를 "1,2,3점" 형식으로 변환
                formatted_braille_feedback = ", ".join([",".join(map(str, dots)) + "점" for dots in braille_feedback])

                # 피드백 텍스트 생성
                feedback_text = f"오답입니다. '{target_word}' 는 '{formatted_braille_feedback}' 입니다."

                # 음성 출력용 피드백 텍스트 설정 (필요시)
                feedback_audio_url = generate_feedback_audio(feedback_text, 'wrong_feedback.mp3')

                # LED 순차 점등
                for index, led_group in enumerate(braille_feedback):
                    # LED 켜기 명령 전송 (인덱스별로 순차적으로 점등)
                    Timer(index * 2.0, lambda group=led_group, kb=keyboard: kb.queue_led_command(group, action='ON')).start()
                    logging.debug(f"Scheduled ON command for LED group {index + 1}: {led_group}")

                    # LED 끄기 명령 전송 (2초 후 소등)
                    Timer((index + 1) * 2.0, lambda group=led_group, kb=keyboard: kb.queue_led_command(group, action='OFF')).start()
                    logging.debug(f"Scheduled OFF command for LED group {index + 1}: {led_group}")

                # 세션에 피드백 오디오 URL 저장 (필요 시)
                if feedback_audio_url:
                    session['feedback_audio_url'] = feedback_audio_url

                # 로그 추가
                logging.debug(f"Feedback Text: {feedback_text}")

                return redirect(url_for('learning_ko.index'))

def handle_back_signal():
    """
    Handles the 'Back' control signal by deleting the character at the current cursor position
    and announcing 'Delete' via audio.
    """
    success = keyboard.delete_at_cursor()
    if success:
        flash("Character deleted.", "info")
    else:
        flash("Nothing to delete.", "info")
    
    # Generate feedback audio saying "Delete"
    feedback_audio_url = generate_feedback_audio("Delete", 'delete.mp3')
    if feedback_audio_url:
        session['feedback_audio_url'] = feedback_audio_url
    return redirect(url_for('learning_ko.index'))

def handle_left_signal():
    """
    Handles the 'Left' control signal by moving the cursor one position to the left
    and announcing 'Left' via audio.
    """
    success = keyboard.move_cursor_left()
    if success:
        flash("Moved cursor left.", "info")
    else:
        flash("Cannot move cursor left.", "info")
    
    # Generate feedback audio saying "Left"
    feedback_audio_url = generate_feedback_audio("Left", 'left.mp3')
    if feedback_audio_url:
        session['feedback_audio_url'] = feedback_audio_url
    return redirect(url_for('learning_ko.index'))

def handle_right_signal():
    """
    Handles the 'Right' control signal by moving the cursor one position to the right
    and announcing 'Right' via audio.
    """
    success = keyboard.move_cursor_right()
    if success:
        flash("Moved cursor right.", "info")
    else:
        flash("Cannot move cursor right.", "info")
    
    # Generate feedback audio saying "Right"
    feedback_audio_url = generate_feedback_audio("Right", 'right.mp3')
    if feedback_audio_url:
        session['feedback_audio_url'] = feedback_audio_url
    return redirect(url_for('learning_ko.index'))

def handle_ctrl_backspace_signal():
    """
    Handles the 'Ctrl + Backspace' control signal by redirecting to the home menu.
    """
    logging.debug("Ctrl + Backspace signal detected. Redirecting to home menu.")
    # 학습 관련 세션 변수 초기화
    session.pop('current_word_id', None)
    session.pop('word_audio_played', None)
    session.pop('feedback_audio_url', None)
    keyboard.clear_input_buffer()
    return redirect(url_for('learning_ko.learn_korean'))

def handle_ctrl_enter_signal():
    """
    Handles the 'Ctrl+Enter' control signal by storing the current word into KoVoca
    and triggering audio playback for the stored word.
    """
    target_word_id = session.get('current_word_id', None)
    if not target_word_id:
        flash("No target word to store.", "error")
        logging.error("No target word found in session.")
        return redirect(url_for('learning_ko.index'))
    # Retrieve the word entry from KoGrade1 by its ID
    word_entry = KoGrade1.query.get(target_word_id)
    if not word_entry:
        flash("Target word not found.", "error")
        logging.error(f"Word with ID '{target_word_id}' not found for storing.")
        return redirect(url_for('learning_ko.index'))
    # Check if the word already exists in KoVoca to prevent duplicates
    existing_entry = KoVoca.query.filter_by(word=word_entry.word).first()
    if existing_entry:
        flash(f"'{word_entry.word}' is already in your vocabulary list.", "info")
        logging.info(f"Word '{word_entry.word}' already exists in KoVoca.")
        
        # Generate feedback audio saying "Word is already in your list"
        feedback_audio_url = generate_feedback_audio(f"'{word_entry.word}' is already in your vocabulary list.", 'already_in_list.mp3')
        if feedback_audio_url:
            session['feedback_audio_url'] = feedback_audio_url
        
        audio_url = None  # No need to trigger word audio again
        
    else:
        try:
            # Store the word in the KoVoca table
            new_voca = KoVoca(word=word_entry.word)
            db.session.add(new_voca)
            db.session.commit()
            flash(f"'{word_entry.word}' stored in your vocabulary list.", "success")
            logging.info(f"Word '{word_entry.word}' successfully stored in KoVoca.")
            # Generate feedback audio saying "Stored in your list"
            feedback_audio_url = generate_feedback_audio(f"'{word_entry.word}' stored in your vocabulary list.", 'stored.mp3')
            if feedback_audio_url:
                session['feedback_audio_url'] = feedback_audio_url
            # Now, trigger the audio of the word itself if it hasn't been played yet
            word_audio_played = session.get('word_audio_played', False)
            if not word_audio_played:
                audio_url = url_for('learning_ko.audio', word_id=word_entry.id)
                session['word_audio_played'] = True  # Set flag to prevent replay
                logging.debug(f"Word audio will be played: {audio_url}")
            else:
                audio_url = None  # Do not play audio again
        except Exception as e:
            db.session.rollback()
            flash("Error storing the word in vocabulary list.", "error")
            logging.error(f"Error storing word in KoVoca: {e}")
    # Render the template with the stored word and feedback audio
    return render_template(
        'learning_ko/ko_2.html',
        target_word=word_entry.word,
        audio_url=audio_url,
        feedback_audio_url=feedback_audio_url
    )
