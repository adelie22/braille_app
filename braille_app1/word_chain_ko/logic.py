#끝말잇기 알고리즘(단어 검색, 두음법칙, 유효성 검사)
import hgtk
import random
from word_chain_ko.utils import is_valid_korean_word, fetch_nouns_from_api  # 필요한 유틸리티 가져오기

def check_word_validity(word, history_ko):
    """
    사용자가 입력한 단어의 유효성을 검사하고,
    각 상황에 맞는 주의문구를 출력합니다.
    """
    print(f"Validating word: {word}")

    # 단어 길이 검사
    if len(word) < 2:
        error_message = "단어는 2글자 이상이어야 합니다."
        print(f"Invalid word: {error_message}")
        return False, error_message

    # 첫 번째 입력 처리
    if not history_ko:
        print("DEBUG: First word. Performing dictionary validation.")
        if not is_valid_korean_word(word):  # 사전 유효성 검사 추가
            error_message = "단어가 사전에 존재하지 않습니다."
            print(f"Invalid word: {error_message}")
            return False, error_message
        return True, None  # 유효하면 통과

    # 끝말잇기 규칙 확인: 이전 단어의 마지막 글자와 현재 단어의 첫 글자 (두음법칙 적용)
    last_word = history_ko[-1]
    last_char = apply_duum_law(last_word[-1])  # 컴퓨터 단어 마지막 글자에 두음법칙 적용
    if last_char != word[0]:  # 사용자의 단어 첫 글자와 비교
        error_message = f"첫 글자는 '{last_char}'입니다."
        print(f"Invalid word: {error_message}")
        return False, error_message

    # 단어 중복 검사
    if word in history_ko:
        error_message = "이미 사용된 단어입니다."
        print(f"Invalid word: {error_message}")
        return False, error_message

    # 단어 유효성 검사
    if not is_valid_korean_word(word):
        error_message = "단어가 사전에 존재하지 않습니다."
        print(f"Invalid word: {error_message}")
        return False, error_message

    # 유효한 단어일 경우
    return True, None  # 유효한 단어라면 True 반환





import hgtk

def apply_duum_law(full_letter):
    """
    두음법칙을 적용하여 변환된 음절을 반환합니다.
    """
    import hgtk

    # 두음법칙 규칙 매핑
    duum_law_mapping = {
        "라": "나", "락": "낙", "란": "난", "랄": "날", "람": "남", "랍": "납", "랑": "낭",
        "래": "내", "랭": "냉", "냑" : "약", "략" : "약", "냐": "야", "냥": "양", "녀": "여", "려": "여",
        "녁": "역", "력": "역", "년": "연", "련": "연", "녈": "열", "렬": "열", "념": "염",
        "렴": "염", "렵": "엽", "령": "영", "녕": "영", "녜": "예", "례": "예", "로": "노",
        "록": "녹", "론": "논", "롱": "농", "뢰": "뇌", "료": "요", "뇨": "요", "루": "누", "룡" : "용",
        "류": "유", "뉴": "유", "륙": "육", "륜": "윤", "률": "율", "륭": "융", "릉": "능",
        "늠": "능", "린": "인", "리": "이", "립": "임", "립": "임", "니" : "이", "림" : "임", '님': '임', '름': '음', '량' : '양'
    }

    try:
        # 두음법칙이 적용될 특정 음절이 있는지 확인
        if full_letter in duum_law_mapping:
            transformed_letter = duum_law_mapping[full_letter]
            print(f"Applying duum law: {full_letter} → {transformed_letter}")
            return transformed_letter
        else:
            print(f"No duum law applied: {full_letter}")
            return full_letter  # 변환되지 않는 경우 그대로 반환
    except Exception as e:
        print(f"Error applying duum law: {e}")
        return full_letter  # 오류가 발생해도 그대로 반환




def generate_next_word(history_ko):
    """
    사용자의 입력을 기반으로 컴퓨터의 다음 단어를 생성합니다.
    두음법칙을 우선 적용하여 API에서 단어를 검색하고 선택합니다.
    """
    if not history_ko:
        print("DEBUG: History is empty. No word to generate next word from.")
        return None  # 사용자가 입력한 단어가 없을 경우

    last_word = history_ko[-1]  # 사용자가 마지막으로 입력한 단어
    last_char = last_word[-1]  # 마지막 글자 추출

    # print(f"DEBUG: Last word in history: {last_word}")
    # print(f"DEBUG: Last character of last word: {last_char}")

    # 두음법칙 적용된 음절로 후보 찾기 (우선적으로 적용)
    transformed_char = apply_duum_law(last_char)
    # print(f"DEBUG: Transformed char after duum law: {transformed_char}")
    candidates = fetch_nouns_from_api(transformed_char)
    # print(f"DEBUG: Candidates from API with transformed char '{transformed_char}': {candidates}")

    # 두음법칙으로 후보가 없을 경우 원래 마지막 글자로 후보 찾기
    if not candidates:
        # print(f"DEBUG: No candidates with transformed char '{transformed_char}'. Trying last char '{last_char}'...")
        candidates = fetch_nouns_from_api(last_char)
        # print(f"DEBUG: Candidates from API with last char '{last_char}': {candidates}")

    # 후보가 없다면 None 반환
    if not candidates:
        # print("DEBUG: No valid candidates available. Ending the game.")
        return None

    # 2글자 이상 단어만 필터링
    filtered_candidates = [word for word in candidates if len(word) >= 2]
    # print(f"DEBUG: Filtered candidates (2 or more chars): {filtered_candidates}")

    # 필터링 후 후보가 없다면 None 반환
    if not filtered_candidates:
        # print("DEBUG: No valid 2-character candidates available. Ending the game.")
        return None

    # 후보가 있다면 무작위로 선택하여 반환
    chosen_word = random.choice(filtered_candidates)
    # print(f"DEBUG: Chosen computer word: {chosen_word}")
    return chosen_word






if __name__ == "__main__":
    history_ko = ["사과", "라면"]  # 입력된 단어 기록
    next_word = generate_next_word(history_ko)  # 다음 단어 생성
    print(f"Next word: {next_word}")

