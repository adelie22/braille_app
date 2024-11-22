# interfaces/mock_keyboard.py

from interfaces.interface import BrailleKeyboardInterface

class MockBrailleKeyboard(BrailleKeyboardInterface):
    def __init__(self):
        self.input_buffer = []

    def read_input(self):
        """
        Simulate reading input from the Braille keyboard.
        Allows multiple inputs using a buffer.
        After finishing input, returns the buffer and clears it.
        """
        while True:
            print("\nSimulate Braille Keyboard Input:")
            print("1. Braille Character Input")
            print("2. Control Input (Enter, Space, Backspace, Arrows)")
            print("3. Finish Input")
            choice = input("Select input type (1, 2, or 3): ")

            if choice == '1':
                # Simulate Braille character input
                print("Enter Braille dots pressed (e.g., 1 3 5 for dots 1, 3, and 5):")
                dots_input = input("Dots: ")
                try:
                    dots = [int(d.strip()) for d in dots_input.split() if d.strip().isdigit()]
                except ValueError:
                    print("Invalid input. Please enter numbers separated by spaces.")
                    continue

                braille_pattern = self.calculate_braille_pattern(dots)
                self.input_buffer.append(braille_pattern)
                print(f"Braille pattern added to buffer. Current buffer length: {len(self.input_buffer)}")
            elif choice == '2':
                # Simulate control input
                print("Control Inputs:")
                print("E0: Enter")
                print("E1: Space")
                print("E2: Backspace")
                print("E3: Arrow Up")
                print("E4: Arrow Down")
                print("E5: Arrow Left")
                print("E6: Arrow Right")
                hex_input = input("Enter control signal (e.g., E0): ")
                try:
                    control_byte = int(hex_input, 16)
                    self.input_buffer.append(control_byte)
                    print(f"Control input added to buffer. Current buffer length: {len(self.input_buffer)}")
                except ValueError:
                    print("Invalid input. Please enter a valid hexadecimal value (e.g., E0).")
            elif choice == '3':
                # Finish input and return the buffer
                if self.input_buffer:
                    input_sequence = self.input_buffer.copy()
                    self.input_buffer.clear()  # Clear the buffer after reading
                    print(f"Input session finished. Returning {len(input_sequence)} braille patterns.")
                    return input_sequence
                else:
                    print("Buffer is empty. Please enter some inputs before finishing.")
            else:
                print("Invalid choice. Please select 1, 2, or 3.")

    def calculate_braille_pattern(self, dots):
        """
        Calculate the Braille pattern byte based on the dots pressed.
        Dots are numbered 1-6 corresponding to bits 0-5.
        """
        braille_pattern = 0
        for dot in dots:
            if 1 <= dot <= 6:
                braille_pattern |= (1 << (dot - 1))
            else:
                print(f"Invalid dot number: {dot}. Must be between 1 and 6.")
        return braille_pattern

    def send_feedback(self, message):
        print(f"Feedback: {message}")