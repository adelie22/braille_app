import requests, hgtk
from word_chain_ko.config import API_KEY  # API 키를 config에서 가져오기

API_URL = "https://opendict.korean.go.kr/api/search"

import re

def fetch_nouns_from_api(starting_char, num_results=50):
    """
    특정 초성으로 시작하는 명사를 API에서 가져옵니다.
    """
    params = {
        "key": API_KEY,
        "q": starting_char,
        "req_type": "json",
        "part": "word",
        "sort": "popular",
        "type": "general",
        "type4" : "general",
        "pos": 1,
        "num": num_results,
        "stirng" : 'start',
        "start" : 1
    }

    try:
        # print(f"DEBUG: Fetching nouns from API with starting_char '{starting_char}'")
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # API 응답에서 단어 추출
        items = data.get("channel", {}).get("item", [])
        # print(f"DEBUG: Items count: {len(items)}")

        def clean_word(word):
            """
            단어를 정제하여 특수문자를 제거합니다.
            """
            return re.sub(r"[^\w가-힣]", "", word)

        # 명사 추출 및 정제
        nouns = []
        for item in items:
            word = item.get("sense", {}).get("word", "")
            pos = item.get("sense", {}).get("pos", "")
            if word and pos == "명사":  # 명사만 추출
                cleaned_word = clean_word(word)
                nouns.append(cleaned_word)

        # print(f"DEBUG: Cleaned nouns: {nouns}")

        # 초성으로 시작하는 단어 필터링
        filtered_nouns = [word for word in nouns if word.startswith(starting_char)]
        # print(f"DEBUG: Nouns starting with '{starting_char}': {filtered_nouns}")

        # 2~3글자 단어로 최종 필터링
        final_nouns = [word for word in filtered_nouns if 2 <= len(word) <= 3]
        # print(f"DEBUG: Final filtered nouns (2~3 chars): {final_nouns}")

        return final_nouns

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []


def is_valid_korean_word(word):
    """
    국립국어원 API를 사용하여 한국어 단어의 유효성을 확인합니다.
    """
    # 한글만 포함되는지 확인
    if not all('\uac00' <= char <= '\ud7a3' for char in word):
        print(f"Invalid Korean word (not Hangul): {word}")
        return False

    params = {
        "key": API_KEY,
        "q": word,
        "req_type": "json",
        "part": "word",
        "sort": "dict"
    }
    try:
        # API 호출
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # API 응답 디버깅
        print(f"DEBUG: API Response for word '{word}': {data}")

        # 단어가 존재하는지 확인
        items = data.get("channel", {}).get("item", [])
        if items:
            print(f"Valid word found in dictionary: {word}")
            return True
        else:
            print(f"Word not found in dictionary: {word}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error validating word via API: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error during word validation: {e}")
        return False


