from flask import Blueprint, request, jsonify, current_app, g, flash
from word_chain_en.logic import check_word_validity, generate_next_word, translate_braille_to_text
import logging

# Blueprint 정의
word_chain_en_api = Blueprint('word_chain_en_api', __name__)

#---------------------------------------------------------------------------------------#

@word_chain_en_api.route('/word_chain_en/get_current_input_buffer', methods=['GET'])
def get_current_input_buffer_word_chain():
    input_buffer = g.keyboard.get_current_input_buffer()
    control_signal = g.keyboard.peek_control_signal()
    return jsonify({'input_buffer': input_buffer, 'control_signal': control_signal})

@word_chain_en_api.route('/word_chain_en/submit_braille_word', methods=['POST'])
def submit_braille_word():
    """
    Translates Braille inputs and submits the word for validation.
    """
    input_buffer = g.keyboard.get_current_input_buffer()
    input_signal = g.keyboard.read_input()  # Retrieve and remove the next signal

    control_signal = None
    if input_signal and input_signal.get('type') == 'control':
        control_signal = input_signal.get('data')

    logging.debug(f"Submit Braille Word - Input Buffer: {input_buffer}, Control Signal: {control_signal}")

    if control_signal != 'Enter':
        return jsonify({'error': 'No Enter signal detected.'}), 400

    # Translate Braille to Text
    translated_word = translate_braille_to_text(input_buffer)
    if not translated_word:
        flash("Braille translation failed.", "error")
        logging.error("Braille translation failed.")
        return jsonify({'error': 'Braille translation failed.'}), 400

    logging.debug(f"Translated Word: {translated_word}")

    # Clear the input buffer after translation
    g.keyboard.clear_input_buffer()

    # Validate the translated word
    history = current_app.config.setdefault('HISTORY_EN', [])

    is_valid, error_message = check_word_validity(translated_word, history)
    if not is_valid:
        flash(error_message, "error")
        logging.info(f"Invalid word submitted: {translated_word} - {error_message}")
        return jsonify({'error': error_message}), 400

    # Valid word: add to history and generate computer word
    history.append(translated_word)
    logging.info(f"Valid word submitted: {translated_word}. Updated history: {history}")

    # Generate computer's next word
    next_word = generate_next_word(history)
    if next_word:
        history.append(next_word.lower())
        logging.info(f"Computer generated word: {next_word}. Updated history: {history}")
        return jsonify({"message": "Valid word", "history": history, "computer_word": next_word}), 200
    else:
        logging.warning("Computer cannot generate a word. Game over.")
        return jsonify({"message": "Valid word", "history": history, "computer_word": None, "game_over": True}), 200
    
@word_chain_en_api.route('/word_chain_en/translate_braille', methods=['POST'])
def translate_braille():
    """
    Translates the current Braille input buffer into English text.
    """
    input_buffer = g.keyboard.get_current_input_buffer()
    translated_text = translate_braille_to_text(input_buffer)
    return jsonify({'translated_text': translated_text}), 200


#---------------------------------------------------------------------------------------#

@word_chain_en_api.route('/word_chain_en/check_word', methods=['POST'])
def check_word():
    history = current_app.config.setdefault('HISTORY_EN', [])  # 서버 전역 history 가져오기

    print(f"Server history (before validation): {history}")

    try:
        data = request.json
        word = data.get('word')
        if not word:
            return jsonify({"error": "Word is required"}), 400

        # 유효성 검사: 항상 history의 마지막 단어를 기준으로 확인
        is_valid, error_message = check_word_validity(word, history)
        if not is_valid:
            return jsonify({"error": error_message}), 400

        # 유효한 단어인 경우, history에 추가
        history.append(word.lower())  # 단어를 소문자로 변환하여 추가
        print(f"Server history (after validation): {history}")

        return jsonify({"message": "Valid word", "history": history}), 200

    except Exception as e:
        print(f"Error during word validation: {e}")
        return jsonify({"error": "Internal server error"}), 500


@word_chain_en_api.route('/word_chain_en/generate_word', methods=['GET'])
def generate_word():
    try:
        # 서버의 history 가져오기
        history_en = current_app.config.setdefault('HISTORY_EN', [])
        # print(f"DEBUG: Server history before generating word: {history}")

        # 다음 단어 생성
        next_word = generate_next_word(history_en)

        if next_word:
            # 컴퓨터 단어를 history에 추가
            history_en.append(next_word.lower())  # 단어를 소문자로 변환하여 추가
            # print(f"DEBUG: Server history after generating word: {history}")
            return jsonify({"word": next_word}), 200
        else:
            # print("DEBUG: No valid word generated. Game over.")
            return jsonify({"error": "The computer cannot generate a word."}), 400
    except Exception as e:
        print(f"Error in generate_word: {e}")
        return jsonify({"error": "Internal server error"}), 500


@word_chain_en_api.route('/word_chain_en/reset', methods=['POST'])
def reset_game():
    # Flask의 current_app.config로 history 초기화
    history = current_app.config.setdefault('HISTORY_EN', [])
    history.clear()  # 기록 초기화
    print('Server-side history after reset:', history)
    return jsonify({"message": "Game has been reset."}), 200
