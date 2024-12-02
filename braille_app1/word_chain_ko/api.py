from flask import Blueprint, request, jsonify, current_app, g, flash
from word_chain_ko.logic import check_word_validity, generate_next_word, translate_braille_to_text
import logging

# Blueprint 정의
word_chain_api = Blueprint('word_chain_api', __name__)



#---------------------------------------------------------------------------------------#

@word_chain_api.route('/word_chain/get_current_input_buffer', methods=['GET'])
def get_current_input_buffer_word_chain():
    input_buffer = g.keyboard.get_current_input_buffer()
    input_signal = g.keyboard.peek_control_signal()  # Peek without consuming
    control_signal = None
    quit_game = False  # Flag to indicate if the game should quit
    restart_game = False  # Flag to indicate if the game should restart

    if input_signal and isinstance(input_signal, str):
        control_signal = input_signal
        logging.debug(f"Processing Control Signal: {control_signal}")

        # Handle specific control signals except 'Enter'
        if control_signal == 'Left':
            g.keyboard.move_cursor_left()
            g.keyboard.read_input()  # Consume the signal
            logging.info("Cursor moved left.")
        elif control_signal == 'Right':
            g.keyboard.move_cursor_right()
            g.keyboard.read_input()  # Consume the signal
            logging.info("Cursor moved right.")
        elif control_signal == 'Back':
            success = g.keyboard.delete_at_cursor()
            g.keyboard.read_input()  # Consume the signal
            if success:
                logging.info("Character deleted at cursor.")
            else:
                logging.info("No character to delete at cursor.")
        elif control_signal == 'Ctrl+Backspace':
            quit_game = True
            g.keyboard.read_input()  # Consume the signal
            logging.info("Ctrl + Backspace received. Preparing to quit the game.")
        elif control_signal == 'Ctrl+Enter':
            restart_game = True
            g.keyboard.read_input()  # Consume the signal
            logging.info("Ctrl + Enter received. Preparing to restart the game.")
        elif control_signal == 'Ctrl':
            g.keyboard.read_input()
        elif control_signal == 'Enter':
            # Do NOT consume the 'Enter' signal here
            logging.info("'Enter' signal detected. Will be handled in submit_braille_word.")
        else:
            logging.warning(f"Unhandled Control Signal: {control_signal}")

    # Fetch the updated input buffer and cursor position
    updated_input_buffer = g.keyboard.get_current_input_buffer()
    cursor_position = g.keyboard.get_cursor_position()

    response = {
        'input_buffer': updated_input_buffer,
        'cursor_position': cursor_position,
        'control_signal': control_signal,
        'quit_game': quit_game,
        'restart_game': restart_game  # Include the restart flag
    }

    return jsonify(response)


@word_chain_api.route('/word_chain/submit_braille_word', methods=['POST'])
def submit_braille_word():
    """
    Translates Braille inputs and submits the word for validation.
    """
    data = request.get_json()
    input_buffer = data.get('input_buffer', [])
    input_signal = g.keyboard.read_input()  # Retrieve and remove the next signal

    control_signal = None
    if input_signal and isinstance(input_signal, str):
        control_signal = input_signal

    logging.debug(f"Submit Braille Word - Input Buffer: {input_buffer}, Control Signal: {control_signal}")

    if control_signal != 'Enter':
        return jsonify({'error': 'No Enter signal detected.'}), 400

    # Translate Braille to Text
    translated_text = translate_braille_to_text(input_buffer)
    
    if not translated_text:
        flash("Braille translation failed.", "error")
        logging.error("Braille translation failed.")
        return jsonify({'error': 'Braille translation failed.'}), 400

    logging.debug(f"Translated Text: {translated_text}")

    # Clear the input buffer after translation
    g.keyboard.clear_input_buffer()

    # Validate the translated word
    history_ko = current_app.config.setdefault('HISTORY_KO', [])

    is_valid, error_message = check_word_validity(translated_text, history_ko)
    if not is_valid:
        flash(error_message, "error")
        logging.info(f"Invalid word submitted: {translated_text} - {error_message}")
        return jsonify({'error': error_message}), 400

    # Valid word: add to history and generate computer word
    history_ko.append(translated_text)
    logging.info(f"Valid word submitted: {translated_text}. Updated history: {history_ko}")

    # Generate computer's next word
    next_word = generate_next_word(history_ko)
    if next_word:
        history_ko.append(next_word.lower())
        logging.info(f"Computer generated word: {next_word}. Updated history: {history_ko}")
        return jsonify({"message": "Valid word", "history": history_ko, "computer_word": next_word}), 200
    else:
        logging.warning("Computer cannot generate a word. Game over.")
        return jsonify({"message": "Valid word", "history": history_ko, "computer_word": None, "game_over": True}), 200

    

@word_chain_api.route('/word_chain/translate_braille', methods=['POST'])
def translate_braille():
    """
    Translates the current Braille input buffer into Korean text.
    Returns the complete translated text and the cursor position.
    """
    data = request.get_json()
    input_buffer = data.get('input_buffer', [])
    logging.debug(f"Received input_buffer for translation: {input_buffer}")
    translated_text = translate_braille_to_text(input_buffer)
    cursor_position = g.keyboard.get_cursor_position()
    
    response = {
        'translated_text': translated_text,
        'cursor_position': cursor_position
    }
    
    logging.debug(f"Translated text: {translated_text}, Cursor position: {cursor_position}")
    
    return jsonify(response), 200





#---------------------------------------------------------------------------------------#

@word_chain_api.route('/word_chain/check_word', methods=['POST'])
def check_word():
    history_ko = current_app.config.setdefault('HISTORY', [])  # 서버 전역 history 가져오기

    print(f"Server history (before validation): {history_ko}")

    try:
        data = request.json
        word = data.get('word')
        if not word:
            return jsonify({"error": "Word is required"}), 400

        # 유효성 검사: 항상 history의 마지막 단어를 기준으로 확인
        is_valid, error_message = check_word_validity(word, history_ko)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        # 유효한 단어인 경우, history에 추가
        history_ko.append(word)
        print(f"Server history (after validation): {history_ko}")

        return jsonify({"message": "유효한 단어", "history": history_ko}), 200

    except Exception as e:
        print(f"Error during word validation: {e}")
        return jsonify({"error": "Internal server error"}), 500







@word_chain_api.route('/word_chain/generate_word', methods=['GET'])
def generate_word():
    try:
        # 서버의 history 가져오기
        history_ko = current_app.config.setdefault('HISTORY', [])
        # print(f"DEBUG: Server history before generating word: {history}")

        # 다음 단어 생성
        next_word = generate_next_word(history_ko)

        if next_word:
            # 컴퓨터 단어를 history에 추가
            history_ko.append(next_word)
            # print(f"DEBUG: Server history after generating word: {history}")
            return jsonify({"word": next_word}), 200
        else:
            # print("DEBUG: No valid word generated. Game over.")
            return jsonify({"error": "컴퓨터가 생성할 수 있는 단어가 없습니다."}), 400
    except Exception as e:
        print(f"Error in generate_word: {e}")
        return jsonify({"error": "서버 오류 발생"}), 500



@word_chain_api.route('/word_chain/reset', methods=['POST'])
def reset_game():
    # Flask의 current_app.config로 history 초기화
    history_ko = current_app.config.setdefault('HISTORY', [])
    history_ko.clear()  # 기록 초기화
    print('Server-side history after reset:', history_ko)
    return jsonify({"message": "게임이 재시작되었습니다."}), 200