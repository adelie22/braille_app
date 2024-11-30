
from BrailleToKorean.BrailleToKor import BrailleToKor
from KorToBraille.KorToBraille import KorToBraille

# 1. 한국어 단어를 점자 유니코드로 번역
target_word = '성공'
b = KorToBraille()
braille_result = b.korTranslate(target_word)
print("Braille Unicode:", braille_result)

# 2. 점자 유니코드에서 점자 번호 추출
braille_numbers = [ord(char) - 0x2800 for char in braille_result]

# 3. 점자 번호를 리스트에 저장
braille_number_list = braille_numbers

def braille_number_to_dots(number):
    dots = []
    for i in range(1, 7):
        if number & (1 << (i - 1)):
            dots.append(i)
    if dots:
        return dots
braille_dots_list = [braille_number_to_dots(num) for num in braille_number_list[:-1]]
print(braille_dots_list)      


# 점자  -> 한국어 번역해서 entered_word에 저장        

target_word = ' ⠠⠻⠈⠿⠀'
b = BrailleToKor()
entered_word = b.translation(target_word)
print(entered_word)