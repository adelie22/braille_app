# interfaces/hardware_keyboard.py

import serial
from interfaces.interface import BrailleKeyboardInterface

class HardwareBrailleKeyboard(BrailleKeyboardInterface):
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600, timeout=1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        self.input_buffer = []

    def read_input(self):
        """
        Read bytes from the serial port and accumulate them.
        """
        while True:
            if self.ser.in_waiting > 0:
                input_byte = self.ser.read(1)
                input_value = int.from_bytes(input_byte, byteorder='big')
                if input_value == 0xE0:  # Enter key to finish input
                    return self.input_buffer
                else:
                    self.input_buffer.append(input_value)
            else:
                pass  # No data available, continue waiting

    def send_feedback(self, message):
        # Implement if your hardware supports feedback
        pass

    def close(self):
        self.ser.close()
