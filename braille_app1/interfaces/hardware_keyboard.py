# hardware_keyboard.py

import threading
from collections import deque
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
    _lock: threading.Lock = threading.Lock()  # Ensures thread-safe singleton

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
        self.input_buffer = deque(maxlen=100)        # Single buffer for processing and display
        self.queue = queue.Queue(maxsize=10)        # Limit queue size to prevent overflow
        self.buffered_mode = False
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
        Continuously read from the serial port and put data into the input queue or buffer.
        """
        while True:
            try:
                with self.lock:
                    if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                        line = self.serial_port.readline().decode('utf-8').strip()
                        logging.debug(f"Received serial line: {line}")

                        # Log the current state of buffered_mode
                        logging.debug(f"Current buffered_mode: {self.buffered_mode}")

                        # Process Braille signals only if buffered_mode is enabled
                        if self.buffered_mode and line.startswith("Braille Signal (6-bit): "):
                            binary_str = line.replace("Braille Signal (6-bit): ", "")
                            if len(binary_str) == 6 and all(c in '01' for c in binary_str):
                                self.input_buffer.append(binary_str)
                                logging.info(f"Buffered Input Updated: {list(self.input_buffer)}")
                        
                        # Handle Control Signals
                        elif line.startswith("Control Signal: "):
                            control_signal = line.replace("Control Signal: ", "")
                            logging.info(f"Received Control Signal: {control_signal}")

                            if control_signal == "Enter":
                                if self.buffered_mode and self.input_buffer:
                                    # Check if there's already an unprocessed braille_input
                                    with self.queue.mutex:
                                        queue_list = list(self.queue.queue)
                                        existing_braille = any(
                                            item.get('type') == 'braille_input' for item in queue_list
                                        )
                                    if not existing_braille:
                                        try:
                                            self.queue.put({
                                                'type': 'braille_input',
                                                'data': list(self.input_buffer)  # Convert deque to list
                                            }, block=False)
                                            logging.debug("Braille input queued successfully.")
                                        except queue.Full:
                                            logging.warning("Queue is full. Discarding new braille input.")
                                        self.input_buffer.clear()
                                # Then put the Enter control signal
                                try:
                                    self.queue.put({
                                        'type': 'control',
                                        'data': control_signal
                                    }, block=False)
                                    logging.debug("Control signal 'Enter' queued successfully.")
                                except queue.Full:
                                    logging.warning("Queue is full. Discarding control signal.")
                            else:
                                try:
                                    self.queue.put({
                                        'type': 'control',
                                        'data': control_signal
                                    }, block=False)
                                    logging.debug(f"Control signal '{control_signal}' queued successfully.")
                                except queue.Full:
                                    logging.warning(f"Queue is full. Discarding control signal '{control_signal}'.")
            except serial.SerialException as e:
                logging.error(f"Serial exception: {e}")
                if self.serial_port:
                    self.serial_port.close()
                self.serial_port = None
            except Exception as e:
                logging.error(f"Unexpected error in serial read thread: {e}")
            time.sleep(0.1)

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
        Return the current input buffer without consuming it.
        """
        with self.lock:
            return list(self.input_buffer)  # Convert deque to list for safe access

    def set_buffered_mode(self, buffered):
        """
        Set whether the keyboard should use buffered input mode.
        """
        with self.lock:
            previous_state = self.buffered_mode
            self.buffered_mode = buffered
            if not buffered:
                self.input_buffer.clear()        # Clear the processing buffer
                logging.info("Buffered mode disabled. Input buffer cleared.")
            else:
                logging.info("Buffered mode enabled.")
            # Log the change with the new state and thread name
            logging.debug(f"Buffered mode changed from {previous_state} to {self.buffered_mode} by {threading.current_thread().name}")


    def clear_input_buffer(self):
        """
        Clear the input buffer. Call this after processing an input.
        """
        with self.lock:
            self.input_buffer.clear()
            logging.debug("Input buffer cleared.")

    def peek_control_signal(self):
        """
        Peek at the next control signal without removing it from the queue.
        """
        with self.queue.mutex:
            for item in list(self.queue.queue):
                if item.get('type') == 'control':
                    return item.get('data')
        return None