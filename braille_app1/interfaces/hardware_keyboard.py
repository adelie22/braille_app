# interfaces/hardware_keyboard.py

from interfaces.interface import BrailleKeyboardInterface
import serial
import time
import threading
import logging

logging.basicConfig(level=logging.INFO)

class HardwareBrailleKeyboard(BrailleKeyboardInterface):
    def __init__(self, port, baudrate=9600, timeout=5):
        """
        Initialize the HardwareBrailleKeyboard with the specified serial port and baud rate.
        """
        self.input_buffer = []
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout)
            logging.info(f"Connected to Arduino on port {port} at {baudrate} baud.")
            time.sleep(2)  # Allow time for the serial connection to initialize
        except serial.SerialException as e:
            logging.error(f"Failed to connect to Arduino on port {port}: {e}")
            self.serial_port = None

    def read_input(self):
        """
        Read the Braille signal from the serial port.
        Waits for a new signal from the Arduino within a timeout period.
        Returns a list of braille patterns (integers).
        """
        if not self.serial_port:
            logging.error("Serial port not initialized. Cannot read input.")
            return []

        logging.debug("Waiting for Braille input from hardware keyboard...")
        braille_signal = None
        start_time = time.time()
        while time.time() - start_time < 5:  # Timeout after 5 seconds
            if self.serial_port.in_waiting > 0:
                try:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    logging.debug(f"Received serial line: {line}")
                    if line.startswith("Braille Signal (6-bit): "):
                        binary_str = line.replace("Braille Signal (6-bit): ", "")
                        if len(binary_str) == 6 and all(c in '01' for c in binary_str):
                            braille_signal = int(binary_str, 2)
                            logging.info(f"Received Braille Signal: {braille_signal:06b}")
                            break
                        else:
                            logging.warning(f"Invalid Braille signal format: {binary_str}")
                except UnicodeDecodeError:
                    logging.warning("Received undecodable bytes from serial port.")
                except ValueError:
                    logging.warning("Failed to parse Braille signal from serial line.")
            time.sleep(0.1)
        
        if braille_signal is not None:
            self.input_buffer = [braille_signal]
            return self.input_buffer
        else:
            logging.warning("No Braille input received within timeout.")
            return []

    def send_feedback(self, message):
        """
        Send feedback to the Braille keyboard.
        For hardware, this might involve lighting LEDs or other indicators.
        Currently, it logs the feedback.
        """
        logging.info(f"Sending feedback to hardware: {message}")
        # TODO: Implement hardware feedback mechanisms if desired
        # Example: Send a specific signal to the Arduino to trigger LED patterns
