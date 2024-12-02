# hardware_keyboard.py

import threading
import queue
import logging
import serial
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class SingletonMeta(type):
    """
    A thread-safe implementation of Singleton.
    """
    _instances = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class HardwareBrailleKeyboard(metaclass=SingletonMeta):
    """
    Singleton class to manage hardware Braille keyboard interactions.
    """
    def __init__(self, port, baudrate=9600, timeout=5):
        self.input_buffer = []       # Buffer storing Braille inputs as binary strings
        self.queue = queue.Queue(maxsize=10)  # Queue for control signals
        self.buffered_mode = False   # Determines if inputs are buffered
        self.cursor_position = 0     # Current cursor position within input_buffer
        self.lock = threading.Lock()
        
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout)
            logging.info(f"Connected to Arduino on port {port} at {baudrate} baud.")
            time.sleep(2)  # Allow time for the serial connection to initialize

            # Start a separate thread to read from the serial port continuously
            self.thread = threading.Thread(target=self._serial_read_thread, daemon=True)
            self.thread.start()
        except serial.SerialException as e:
            logging.error(f"Failed to connect to Arduino on port {port}: {e}")
            self.serial_port = None

    def _serial_read_thread(self):
        """
        Continuously reads from the serial port and processes incoming data.
        """
        while True:
            try:
                with self.lock:
                    if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                        line = self.serial_port.readline().decode('utf-8').strip()
                        logging.debug(f"Received serial line: {line}")

                        if self.buffered_mode and line.startswith("Braille Signal (6-bit): "):
                            binary_str = line.replace("Braille Signal (6-bit): ", "")
                            if len(binary_str) == 6 and all(c in '01' for c in binary_str):
                                self.input_buffer.append(binary_str)
                                # Move cursor to the end after adding a new character
                                self.cursor_position = len(self.input_buffer) - 1
                                logging.info(f"Buffered Input Updated: {self.input_buffer}")
                                logging.debug(f"Cursor moved to position {self.cursor_position}")
                        
                        elif line.startswith("Control Signal: "):
                            control_signal = line.replace("Control Signal: ", "")
                            logging.info(f"Received Control Signal: {control_signal}")
                            try:
                                self.queue.put({
                                    'type': 'control',
                                    'data': control_signal
                                }, block=False)
                                logging.debug(f"Control signal '{control_signal}' queued successfully.")
                            except queue.Full:
                                logging.warning(f"Queue is full. Discarding control signal '{control_signal}'.")
            except Exception as e:
                logging.error(f"Unexpected error in serial read thread: {e}")
            time.sleep(0.1)  # Prevent tight loop

    def read_input(self):
        """
        Retrieve signals from the queue.
        Returns a dictionary containing signal type and data if available.
        """
        if not self.queue.empty():
            input_signal = self.queue.get()
            logging.debug(f"Input signal retrieved from queue: {input_signal}")
            return input_signal
        return None

    def get_current_input_buffer(self):
        """
        Return a copy of the current input buffer.
        """
        with self.lock:
            return list(self.input_buffer)
        
    def set_buffered_mode(self, buffered):
        """
        Set whether the keyboard should use buffered input mode.
        """
        with self.lock:
            previous_state = self.buffered_mode
            self.buffered_mode = buffered
            if not buffered:
                self.input_buffer.clear()
                self.cursor_position = 0
                logging.info("Buffered mode disabled. Input buffer cleared and cursor reset.")
            else:
                logging.info("Buffered mode enabled.")
            logging.debug(f"Buffered mode changed from {previous_state} to {self.buffered_mode} by {threading.current_thread().name}")

    def clear_input_buffer(self):
        """
        Clear the input buffer.
        """
        with self.lock:
            self.input_buffer.clear()
            self.cursor_position = 0
            logging.debug("Input buffer and cursor position cleared.")

    def peek_control_signal(self):
        """
        Peek at the next control signal without removing it from the queue.
        """
        with self.queue.mutex:
            for item in list(self.queue.queue):
                if item.get('type') == 'control':
                    return item.get('data')
        return None

    # Cursor Management Methods
    def move_cursor_left(self):
        """
        Move the cursor one position to the left.
        """
        with self.lock:
            logging.debug(f"Attempting to move cursor left from position {self.cursor_position}.")
            if self.cursor_position > 0:
                self.cursor_position -= 1
                logging.debug(f"Cursor successfully moved left to position {self.cursor_position}.")
            else:
                logging.debug("Cursor is already at the beginning of the input buffer.")

    def move_cursor_right(self):
        """
        Move the cursor one position to the right.
        """
        with self.lock:
            logging.debug(f"Attempting to move cursor right from position {self.cursor_position}.")
            if self.cursor_position < len(self.input_buffer) - 1:
                self.cursor_position += 1
                logging.debug(f"Cursor successfully moved right to position {self.cursor_position}.")
            else:
                logging.debug("Cursor is already at the end of the input buffer.")

    def delete_at_cursor(self):
        """
        Delete the character at the current cursor position.
        Returns True if deletion was successful, False otherwise.
        """
        with self.lock:
            logging.debug(f"Attempting to delete at cursor position: {self.cursor_position}")
            if 0 <= self.cursor_position < len(self.input_buffer):
                removed_item = self.input_buffer.pop(self.cursor_position)
                logging.debug(f"Removed item at position {self.cursor_position}: {removed_item}")
                # Adjust cursor position if necessary
                if self.cursor_position >= len(self.input_buffer) and self.cursor_position > 0:
                    self.cursor_position -= 1
                    logging.debug(f"Cursor position adjusted to: {self.cursor_position}")
                logging.debug(f"Input buffer after deletion: {self.input_buffer}")
                return True
            else:
                logging.debug("Cursor position is out of range. Nothing to delete.")
                return False

    def get_cursor_position(self):
        """
        Get the current cursor position.
        """
        with self.lock:
            return self.cursor_position

    def set_cursor_position(self, position):
        """
        Set the cursor position to a specific index.
        """
        with self.lock:
            if 0 <= position < len(self.input_buffer):
                self.cursor_position = position
                logging.debug(f"Cursor position set to {self.cursor_position}.")
            elif position >= len(self.input_buffer):
                self.cursor_position = len(self.input_buffer) - 1 if self.input_buffer else 0
                logging.debug(f"Cursor position adjusted to {self.cursor_position}.")
            else:
                self.cursor_position = 0
                logging.debug("Cursor position adjusted to start (0).")
#====================led관련 추가==================
    def send_led_command(self, led_numbers, action='ON'):
        """
        Sends LED control commands to Arduino.
        led_numbers: list of LED numbers (e.g., [1, 2, 3])
        action: 'ON' or 'OFF'
        """
        if self.serial_port and self.serial_port.is_open:
            command = f"{action}:{','.join(map(str, led_numbers))}\n"
            try:
                self.serial_port.write(command.encode())
                logging.debug(f"Sent LED command via serial: {command.strip()}")
            except Exception as e:
                logging.error(f"Failed to send LED command: {e}")
        else:
            logging.error("Serial port is not open. Cannot send LED command.")
