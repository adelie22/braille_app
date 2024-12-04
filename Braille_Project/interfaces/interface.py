# interfaces/interface.py

class BrailleKeyboardInterface:
    def read_input(self):
        """Read input from the Braille keyboard."""
        raise NotImplementedError("Subclasses must implement this method")

    def send_feedback(self, message):
        """Send feedback to the Braille keyboard."""
        raise NotImplementedError("Subclasses must implement this method")
