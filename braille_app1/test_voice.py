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

sen = "시각장애인 점자 프로젝트"

a = louis.translateString(["braille-patterns.cti", "ko-g1.ctb"],  f"{sen}")

print("eng -> braile :", a)
braille = "⠃⠗⠁⠊⠇⠇⠑⠀⠞⠗⠁⠝⠎⠇⠁⠞⠕⠗"

b = louis.backTranslateString(["braille-patterns.cti", "en-us-g1.ctb"], f"{braille}")

print("braille -> eng :", b)