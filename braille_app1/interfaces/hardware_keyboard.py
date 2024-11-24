import threading
from collections import deque
import queue
import logging
import serial
import time

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

class SingletonMeta(type):
    _instances = {}
    _lock: threading.Lock = threading.Lock()  # Ensures thread-safe singleton

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class HardwareBrailleKeyboard(metaclass=SingletonMeta):
    def __init__(self, port, baudrate=9600, timeout=5):
        self.input_buffer = deque(maxlen=100)        # Bounded buffer for processing
        self.display_buffer = deque(maxlen=100)      # Bounded buffer for display
        self.queue = queue.Queue()
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
        """ Continuously read from the serial port and put data into the input queue or buffer. """
        while True:
            try:
                with self.lock:
                    if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                        line = self.serial_port.readline().decode('utf-8').strip()
                        logging.debug(f"Received serial line: {line}")

                        # Process Braille signals
                        if self.buffered_mode and line.startswith("Braille Signal (6-bit): "):
                            binary_str = line.replace("Braille Signal (6-bit): ", "")
                            if len(binary_str) == 6 and all(c in '01' for c in binary_str):
                                self.input_buffer.append(binary_str)
                                self.display_buffer.append(binary_str)
                                logging.info(f"Buffered Input Updated: {list(self.input_buffer)}")
                        # Handle Control Signals
                        elif line.startswith("Control Signal: "):
                            control_signal = line.replace("Control Signal: ", "")
                            logging.info(f"Received Control Signal: {control_signal}")

                            if control_signal == "Enter":
                                if self.buffered_mode:
                                    # Put the Braille input first
                                    self.queue.put({
                                        'type': 'braille_input',
                                        'data': list(self.input_buffer)  # Convert deque to list
                                    })
                                    self.input_buffer.clear()
                                # Then put the Enter control signal
                                self.queue.put({
                                    'type': 'control',
                                    'data': control_signal
                                })
                            else:
                                self.queue.put({
                                    'type': 'control',
                                    'data': control_signal
                                })
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
        Return the current display buffer without consuming it.
        """
        with self.lock:
            return list(self.display_buffer)  # Convert deque to list for safe access

    def set_buffered_mode(self, buffered):
        """
        Set whether the keyboard should use buffered input mode.
        """
        self.buffered_mode = buffered
        if not buffered:
            with self.lock:
                self.input_buffer.clear()        # Clear the processing buffer
                self.display_buffer.clear()      # Clear the display buffer
            logging.info("Buffered mode disabled. Input buffer and display buffer cleared.")
        else:
            logging.info("Buffered mode enabled.")

    def clear_display_buffer(self):
        """
        Clear the display buffer. Call this after processing an input.
        """
        with self.lock:
            self.display_buffer.clear()
            logging.debug("Display buffer cleared.")

    def peek_control_signal(self):
        """
        Peek at the next control signal without removing it from the queue.
        """
        with self.queue.mutex:
            for item in list(self.queue.queue):
                if item.get('type') == 'control':
                    return item.get('data')
        return None
