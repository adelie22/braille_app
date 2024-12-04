# hardware_keyboard.py

import threading
import queue
import logging
import serial
import time
# from flask import current_app

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
        self.control_queue = queue.Queue(maxsize=10)  # Queue for control signals
        self.command_queue = queue.Queue()  # Queue for LED commands
        self.vibration_queue = queue.Queue()  # **New** Queue for Vibration commands
        self.buffered_mode = False   # Determines if inputs are buffered
        self.cursor_position = 0     # Current cursor position within input_buffer
        self.lock = threading.Lock()
        self.serial_lock = threading.Lock()  # Lock for serial port access

        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout)
            logging.info(f"Connected to Arduino on port {port} at {baudrate} baud.")
            time.sleep(2)  # Allow time for the serial connection to initialize

            # Start a separate thread to read from the serial port continuously
            self.read_thread = threading.Thread(target=self._serial_read_thread, daemon=True)
            self.read_thread.start()

            # Start a separate thread to process LED commands
            self.command_thread = threading.Thread(target=self._process_commands, daemon=True)
            self.command_thread.start()
            
            # **New** Start a separate thread to process Vibration commands
            self.vibration_thread = threading.Thread(target=self._process_vibration_commands, daemon=True)
            self.vibration_thread.start()

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
                                self.control_queue.put({
                                    'type': 'control',
                                    'data': control_signal
                                }, block=False)
                                logging.debug(f"Control signal '{control_signal}' queued successfully.")
                            except queue.Full:
                                logging.warning(f"Queue is full. Discarding control signal '{control_signal}'.")
            except Exception as e:
                logging.error(f"Unexpected error in serial read thread: {e}")
            time.sleep(0.1)  # Prevent tight loop

    def _process_commands(self):
        """
        Continuously processes LED commands from the command queue and sends them to Arduino.
        """
        while True:
            try:
                command = self.command_queue.get()
                if command:
                    led_numbers = command['led_numbers']
                    action = command['action']
                    self._send_led_command_internal(led_numbers, action)
                self.command_queue.task_done()
            except Exception as e:
                logging.error(f"Error processing LED command: {e}")
                
    def _process_vibration_commands(self):
        """
        Continuously processes vibration commands from the vibration queue and sends them to Arduino.
        """
        while True:
            try:
                command = self.vibration_queue.get()
                if command:
                    duration = command.get('duration', 500)  # Default to 500ms
                    self._send_vibrate_command(duration)
                self.vibration_queue.task_done()
            except Exception as e:
                logging.error(f"Error processing vibration command: {e}")

    def _send_led_command_internal(self, led_numbers, action='ON'):
        """
        Internal method to send LED commands without involving Flask's app context.
        """
        with self.serial_lock:
            if self.serial_port and self.serial_port.is_open:
                command_str = f"{action}:{','.join(map(str, led_numbers))}\n"
                try:
                    self.serial_port.write(command_str.encode())
                    logging.debug(f"Sent LED command via serial: {command_str.strip()}")
                except Exception as e:
                    logging.error(f"Failed to send LED command: {e}")
            else:
                logging.error("Serial port is not open. Cannot send LED command.")
                
    def _send_vibrate_command(self, duration):
        """
        Sends a vibration command to the Arduino.
        duration: Duration in milliseconds for the vibration.
        """
        if self.serial_port and self.serial_port.is_open:
            command_str = f"VIBRATE:{duration}\n"
            try:
                with self.serial_lock:
                    self.serial_port.write(command_str.encode())
                logging.debug(f"Sent VIBRATE command via serial: {command_str.strip()}")
            except Exception as e:
                logging.error(f"Failed to send VIBRATE command: {e}")
        else:
            logging.error("Serial port is not open. Cannot send VIBRATE command.")

    def queue_vibrate(self, duration=500):
        """
        Enqueue a vibration command.
        duration: Duration in milliseconds for the vibration.
        """
        try:
            self.vibration_queue.put({
                'duration': duration
            }, block=True)  # block=True ensures the command is enqueued
            logging.debug(f"Queued VIBRATE command: duration={duration}ms")
        except queue.Full:
            logging.warning(f"Vibration queue is full. Discarding VIBRATE command: duration={duration}ms")

    def queue_led_command(self, led_numbers, action='ON'):
        """
        Enqueue an LED command to be processed by the command thread.
        led_numbers: list of LED numbers (e.g., [1, 2, 3])
        action: 'ON' or 'OFF'
        """
        try:
            self.command_queue.put({
                'led_numbers': led_numbers,
                'action': action
            }, block=True)  # block=True ensures the command is enqueued
            logging.debug(f"Queued LED command: {action} {led_numbers}")
        except queue.Full:
            logging.warning(f"Command queue is full. Discarding LED command: {action} {led_numbers}")

    def read_input(self):
        """
        Retrieve signals from the control queue.
        Returns a dictionary containing signal type and data if available.
        """
        if not self.control_queue.empty():
            input_signal = self.control_queue.get()
            logging.debug(f"Input signal retrieved from control queue: {input_signal}")
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
        with self.control_queue.mutex:
            for item in list(self.control_queue.queue):
                if item.get('type') == 'control':
                    return item.get('data')
        return None

    # Cursor Management Methods
    # def move_cursor_left(self):
    #     """
    #     Move the cursor one position to the left.
    #     """
    #     with self.lock:
    #         logging.debug(f"Attempting to move cursor left from position {self.cursor_position}.")
    #         if self.cursor_position > 0:
    #             self.cursor_position -= 1
    #             logging.debug(f"Cursor successfully moved left to position {self.cursor_position}.")
    #         else:
    #             logging.debug("Cursor is already at the beginning of the input buffer.")

    # def move_cursor_right(self):
    #     """
    #     Move the cursor one position to the right.
    #     """
    #     with self.lock:
    #         logging.debug(f"Attempting to move cursor right from position {self.cursor_position}.")
    #         if self.cursor_position < len(self.input_buffer) - 1:
    #             self.cursor_position += 1
    #             logging.debug(f"Cursor successfully moved right to position {self.cursor_position}.")
    #         else:
    #             logging.debug("Cursor is already at the end of the input buffer.")
    def move_cursor_left(self): # 이 코드 문제 발생하면 위에 주석 처리된걸로 대체하기

        with self.lock:
            logging.debug(f"Attempting to move cursor left from position {self.cursor_position}.")
            if self.cursor_position > 0:
                self.cursor_position -= 1
                logging.debug(f"Cursor successfully moved left to position {self.cursor_position}.")
                return True
            else:
                logging.debug("Cursor is already at the beginning of the input buffer.")
                return False

    def move_cursor_right(self):

        with self.lock:
            logging.debug(f"Attempting to move cursor right from position {self.cursor_position}.")
            if self.cursor_position < len(self.input_buffer) - 1:
                self.cursor_position += 1
                logging.debug(f"Cursor successfully moved right to position {self.cursor_position}.")
                return True
            else:
                logging.debug("Cursor is already at the end of the input buffer.")
                return False


    

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

    @classmethod
    def get_instance(cls, port='COM3', baudrate=9600, timeout=5):
        """
        Get the singleton instance of HardwareBrailleKeyboard.
        """
        return cls(port, baudrate, timeout)




      