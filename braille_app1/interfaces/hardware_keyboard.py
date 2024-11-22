import threading
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

class HardwareBrailleKeyboard:
    def __init__(self, port, baudrate=9600, timeout=5):
        self.input_buffer = []  # List to store Braille binary strings until Enter is pressed
        self.queue = queue.Queue()  # Queue to pass final inputs and control signals to the application
        self.buffered_mode = False  # Initialize buffered_mode
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
                        if line.startswith("Braille Signal (6-bit): "):
                            binary_str = line.replace("Braille Signal (6-bit): ", "")
                            if len(binary_str) == 6 and all(c in '01' for c in binary_str):
                                self.input_buffer.append(binary_str)
                                logging.info(f"Buffered Input Updated: {self.input_buffer}")
                        # Handle Control Signals
                        elif line.startswith("Control Signal: "):
                            control_signal = line.replace("Control Signal: ", "")
                            logging.info(f"Received Control Signal: {control_signal}")

                            if control_signal == "Enter":
                                if self.buffered_mode:
                                    # Put the Braille input first
                                    self.queue.put({
                                        'type': 'braille_input',
                                        'data': self.input_buffer.copy()
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

    def send_feedback(self, message):
        """
        Send feedback to the Braille keyboard.
        """
        if not self.serial_port or not self.serial_port.is_open:
            logging.error("Serial port not available. Cannot send feedback.")
            return

        try:
            self.serial_port.write(f"{message}\n".encode('utf-8'))
            logging.info(f"Sent feedback to hardware: {message}")
        except serial.SerialException as e:
            logging.error(f"Failed to send feedback to Arduino: {e}")
            
    def get_current_input_buffer(self):
        """
        Return the current input buffer without consuming it.
        """
        with self.lock:
            return self.input_buffer.copy()

    def set_buffered_mode(self, buffered):
        """
        Set whether the keyboard should use buffered input mode.
        """
        self.buffered_mode = buffered
        if not buffered:
            self.input_buffer.clear()  # Clear the buffer when disabling buffered mode
            logging.info("Buffered mode disabled. Input buffer cleared.")
        else:
            logging.info("Buffered mode enabled.")
            
    def peek_control_signal(self):
        """
        Peek at the next control signal without removing it from the queue.
        """
        with self.queue.mutex:
            for item in list(self.queue.queue):
                if item.get('type') == 'control':
                    return item['data']
        return None

    def get_braille_input(self):
        """
        Get the Braille input from the queue.
        """
        braille_inputs = []
        while not self.queue.empty():
            item = self.queue.get()
            if item.get('type') == 'braille_input':
                braille_inputs.extend(item['data'])
            elif item.get('type') == 'control':
                if item['data'] == 'Enter':
                    # Stop reading inputs when Enter is encountered
                    break
            else:
                # If other types, ignore or handle accordingly
                pass
        return braille_inputs
