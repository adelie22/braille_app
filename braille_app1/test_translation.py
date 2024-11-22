# test_translation.py

import louis

# Path to your Braille translation table
BRAILLE_TABLE = "/home/guru/liblouis-3.21.0/tables/ko-g1.ctb"

# Sample braille bytes for 'lion'
braille_bytes = [7, 10, 21, 13]  # [0x07, 0x0A, 0x15, 0x0D]
braille_chars = ''.join([chr(0x2800 + byte) for byte in braille_bytes])

print(f"Braille Characters: {braille_chars}")  # Expected: ⠇⠊⠕⠍

try:
    translated_word = louis.translateString([BRAILLE_TABLE], braille_chars).strip().lower()
    print(f"Translated Word: {translated_word}")  # Expected: "lion"
except Exception as e:
    print(f"Error during translation: {e}")
