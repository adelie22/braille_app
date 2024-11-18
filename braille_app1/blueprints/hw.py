import louis
import logging

# Configure logging to display debug information
logging.basicConfig(level=logging.DEBUG, format='DEBUG:%(levelname)s:%(message)s')

# Define the Braille translation tables
BRAILLE_TABLE = ["braille-patterns.cti", "en-us-g1.ctb"]  # Ensure these are correct and accessible

# Define the target word
target_word = "cat"  # You can change this to test different words

# Define a function to translate a single letter and extract dots
def translate_letter(letter, braille_table):
    try:
        # Translate the letter to Braille using Liblouis
        braille_chars = louis.translateString(braille_table, letter)
        logging.debug(f"Letter: '{letter}' -> Braille Characters: '{braille_chars}'")

        dots_per_char = []
        for braille_char in braille_chars:
            unicode_value = ord(braille_char)
            logging.debug(f"  Braille Char: '{braille_char}' (Unicode: {hex(unicode_value)})")

            if 0x2800 <= unicode_value <= 0x28FF:
                braille_byte = unicode_value - 0x2800
                dots = [str(j + 1) for j in range(6) if braille_byte & (1 << j)]
                dots_str = ','.join(dots)
                logging.debug(f"    Extracted Dots: {dots_str}")
                dots_per_char.append(dots_str)
            else:
                logging.warning(f"    Unexpected Braille character '{braille_char}' with Unicode {hex(unicode_value)}")
        
        return dots_per_char

    except louis.LouisError as e:
        logging.error(f"Liblouis translation error for letter '{letter}': {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error for letter '{letter}': {e}")
        return []

# Initialize a list to hold instructions
instructions_list = []

# Iterate over each letter in the target word
for letter in target_word:
    letter = letter.lower()
    dots_per_char = translate_letter(letter, BRAILLE_TABLE)
    
    if dots_per_char:
        for dots_str in dots_per_char:
            # Check if dots_str contains only '5,6' or includes '5,6' along with others
            if dots_str == "5,6":
                logging.debug(f"    Detected unwanted '5,6' pattern for letter '{letter}'")
                continue  # Skip adding this instruction
            elif "5" in dots_str or "6" in dots_str:
                # If '5,6' is part of a larger pattern, remove them
                filtered_dots = [dot for dot in dots_str.split(',') if dot not in ["5", "6"]]
                if filtered_dots:
                    filtered_dots_str = ','.join(filtered_dots)
                    instructions_list.append(f"{filtered_dots_str}<break time='300ms'/> for<break time='200ms'/> {letter}")
                    logging.debug(f"    Filtered Dots: {filtered_dots_str} for letter '{letter}'")
                else:
                    logging.debug(f"    All dots filtered out for letter '{letter}'")
            else:
                instructions_list.append(f"{dots_str}<break time='300ms'/> for<break time='200ms'/> {letter}")
                logging.debug(f"    Added Instruction: {dots_str} for letter '{letter}'")
    else:
        logging.warning(f"No Braille dots extracted for letter '{letter}'")

# Combine the instructions into one SSML string
instructions_text = "Press<break time='300ms'/> " + ';<break time=\"500ms\"/> '.join(instructions_list) + '.'
logging.debug(f"Instructions Text with SSML: {instructions_text}")

# Output the final instructions text
print("Final Instructions Text with SSML:")
print(instructions_text)
