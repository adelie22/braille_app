from flask import Flask, render_template, jsonify
import serial
import threading
import louis  # Import liblouis for Braille translation

# Configure the serial port (update the port name and baud rate as needed)
ser = serial.Serial('/dev/ttyACM0', 9600)  # Replace with your serial port

app = Flask(__name__)

accumulated_text = ''
text_lock = threading.Lock()

def braille_to_char(braille_code):
    # Ensure braille_code is 6 characters
    if len(braille_code) != 6:
        return None
    braille_value = 0
    for i in range(6):
        bit = braille_code[5 - i]  # Reverse order of bits
        if bit == '1':
            braille_value |= (1 << i)
    # Construct the Unicode Braille character
    braille_char = chr(0x2800 + braille_value)
    # Use liblouis to back-translate the Braille character to text
    try:
        # Use the appropriate table; adjust the table names/path as needed
        table = ["braille-patterns.cti","/home/guru/liblouis-3.21.0/tables/en-us-g1.ctb"]  # For English Grade 1 Braille
        translated_char = louis.backTranslateString(table, braille_char)
        print(f"Braille char: {braille_char}, Translated char: {translated_char}")
        return translated_char.strip()
    except louis.LouisError as e:
        print(f"Liblouis error: {e}")
        return None

def serial_reader():
    global accumulated_text
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            print(f"Received: {line}")
            if line.startswith('Braille Signal (6-bit):'):
                braille_code = line.split(':')[1].strip().replace(' ', '')
                char = braille_to_char(braille_code)
                if char is not None:
                    with text_lock:
                        accumulated_text += char
                else:
                    print(f"Unknown braille code: {braille_code}")
            elif line.startswith('Control Signal:'):
                control_signal = line.split(':')[1].strip()
                if control_signal == 'Back':
                    with text_lock:
                        accumulated_text = accumulated_text[:-1]
                elif control_signal == 'Space':
                    with text_lock:
                        accumulated_text += ' '
                elif control_signal == 'Enter':
                    with text_lock:
                        accumulated_text = ''  # Clear the text
                # Handle other control signals if needed

@app.route('/')
def index():
    return render_template('index.html')  # Use a separate HTML file

@app.route('/get_text')
def get_text():
    with text_lock:
        text_to_display = accumulated_text
    return jsonify({'text': text_to_display})

if __name__ == '__main__':
    serial_thread = threading.Thread(target=serial_reader)
    serial_thread.daemon = True
    serial_thread.start()
    app.run(host='0.0.0.0', port=5000)
