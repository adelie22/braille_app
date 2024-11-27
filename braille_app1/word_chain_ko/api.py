from flask import Blueprint, request, jsonify, current_app
from word_chain_ko.logic import check_word_validity, generate_next_word

# Blueprint 정의
word_chain_api = Blueprint('word_chain_api', __name__)

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