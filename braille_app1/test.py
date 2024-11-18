import louis

# Path to your Braille translation table
BRAILLE_TABLE = ["en-us-g1.ctb"]  # Replace with the full path if necessary

def calculate_braille_pattern(dots):
    """
    Calculate the Braille pattern byte based on the dots pressed.
    Dots are numbered 1-8 corresponding to bits 0-7.
    """
    braille_pattern = 0
    for dot in dots:
        if 1 <= dot <= 8:
            braille_pattern |= (1 << (dot - 1))
        else:
            print(f"Invalid dot number: {dot}. Must be between 1 and 8.")
            return None
    return braille_pattern

def main():
    print("Braille Translation Test")
    print("Enter Braille characters by specifying the dots pressed.")
    print("Dots for a single character should be input without spaces between the numbers.")
    print("Separate multiple characters with spaces.")
    print("Type 'exit' to quit.\n")

    while True:
        dots_input = input("Enter dots (e.g., '135 24' for 'k' and 'b'): ")
        if dots_input.lower() == 'exit':
            print("Exiting...")
            break

        try:
            dots_list = dots_input.strip().split()
            braille_bytes = []
            for dots_str in dots_list:
                # Handle multiple dots for a single character
                dots = [int(d) for d in dots_str if d.isdigit()]
                if not dots:
                    print(f"Invalid dots input: '{dots_str}'. Please enter digits between 1 and 8.")
                    continue
                braille_byte = calculate_braille_pattern(dots)
                if braille_byte is not None:
                    braille_bytes.append(braille_byte)
                else:
                    print("Invalid input. Please try again.")
                    continue

            if not braille_bytes:
                print("No valid Braille patterns entered. Please try again.\n")
                continue

            # Convert braille bytes to Unicode Braille characters
            braille_chars = ''.join([chr(0x2800 + byte) for byte in braille_bytes])
            print(f"Braille Characters: {braille_chars}")

            # Use Liblouis to translate Braille Unicode string to text
            try:
                translated_text = louis.backTranslateString(BRAILLE_TABLE, braille_chars).strip()
                print(f"Translated Text: {translated_text}\n")
            except Exception as e:
                print(f"Error during translation: {e}\n")

        except ValueError as ve:
            print(f"Invalid input. Error: {ve}. Please enter numbers between 1 and 8.\n")

if __name__ == "__main__":
    main()

