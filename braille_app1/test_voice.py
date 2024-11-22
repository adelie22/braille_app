# import louis

# BRAILLE_TABLE = ["en-us-g1.ctb"]
# text = "cat"
# translation_mode = louis.noContractions | louis.dotsIO

# braille = louis.backTranslateString(BRAILLE_TABLE, text)
# print(f"Translated Braille: {braille}")

# for char in braille:
#     unicode_value = ord(char)
#     print(f"Char: '{char}', Unicode: {hex(unicode_value)}")
import louis

sen = "안녕하세요"

a = louis.translateString(["braille-patterns.cti", "/home/guru/liblouis-3.21.0/tables/ko-g1.ctb"],  f"{sen}")

print("eng -> braile :", a)
braille = "⠃⠣⠒⠉⠱⠶⠚⠣⠠⠝⠬"

b = louis.backTranslateString(["/home/guru/liblouis-3.21.0/tables/ko-g1.ctb"], f"{braille}")

print("braille -> eng :", b)


# Dictionary: Alphabet to Braille (Unicode)
alphabet_to_braille = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽',
    'z': '⠵'
}

# Dictionary: Alphabet to Buttons
alphabet_to_buttons = {
    'a': [1],         'b': [1, 2],      'c': [1, 4],      'd': [1, 4, 5],
    'e': [1, 5],      'f': [1, 2, 4],   'g': [1, 2, 4, 5],'h': [1, 2, 5],
    'i': [2, 4],      'j': [2, 4, 5],   'k': [1, 3],      'l': [1, 2, 3],
    'm': [1, 3, 4],   'n': [1, 3, 4, 5],'o': [1, 3, 5],   'p': [1, 2, 3, 4],
    'q': [1, 2, 3, 4, 5], 'r': [1, 2, 3, 5],'s': [2, 3, 4], 't': [2, 3, 4, 5],
    'u': [1, 3, 6],   'v': [1, 2, 3, 6],'w': [2, 4, 5, 6],'x': [1, 3, 4, 6],
    'y': [1, 3, 4, 5, 6], 'z': [1, 3, 5, 6]
}