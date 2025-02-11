from machine import Pin, UART
import time
import neopixel

# Pengaturan pinout LED, lock_12v lock, dan suplai tegangan ke sensor IR barang jatuh (VFB)
led_neopixel = Pin(16, Pin.OUT)
lock_12v = Pin(14, Pin.OUT)
lock_12v.value(1)
lock_trigger = Pin(13, Pin.OUT)
ir_trigger = Pin(10, Pin.OUT)

# Define neopixel
np = neopixel.NeoPixel(led_neopixel, 1)

def set_color(r, g, b):
    np[0] = (r, g, b)
    np.write()

def led1_on():
    set_color(255, 0, 0)
    time.sleep(1)
    set_color(0, 255, 0)
    time.sleep(1)
    set_color(0, 0, 255)
    time.sleep(1)
    set_color(0, 0, 0)

# Define pin & initial state Shift Register
SH_CP = Pin(26, Pin.OUT)  # Clock pin
ST_CP = Pin(15, Pin.OUT)  # Latch pin
DS = Pin(27, Pin.OUT)     # Data pin
DS.value(0)
SH_CP.value(0)
ST_CP.value(0)

# Pengaturan IC Register 74HC595
def shift_out(value):
    for i in range(8):
        bit = (value >> (7 - i)) & 1
        DS.value(bit)
        SH_CP.value(1)
        SH_CP.value(0)

def write_to_74hc595(values):
    ST_CP.value(0)
    for value in values:
        shift_out(value)
    ST_CP.value(1)

uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# Mapping angka ke nilai biner yang sesuai
digit_to_binary = {
    0: 0b10000000,
    1: 0b01000000,
    2: 0b00100000,
    3: 0b00010000,
    4: 0b00001000,
    5: 0b00000100,
    6: 0b00000010,
    7: 0b00000001
}

# Fungsi untuk mengonversi angka ke biner
def convert_to_binary(digit):
    return digit_to_binary.get(digit, 0b00000000)

# Fungsi untuk menghasilkan motor_code secara dinamis
def generate_motor_code():
    motor_code = {}
    for x in range(8):
        for y in range(8):
            reg1 = convert_to_binary(x)
            reg2 = convert_to_binary(y)
            motor_code[f'{x}{y}'] = [reg1, reg2]
    return motor_code

# Menghasilkan motor_code
motor_code = generate_motor_code()

# Fungsi untuk menghitung motor_code berdasarkan baris dan kolom
def calculate_motor_code(baris, kolom):
    reg1 = convert_to_binary(baris)
    reg2 = convert_to_binary(kolom)
    return [reg1, reg2]

# Initialize state
motor_state = [0b00000000, 0b00000000]

def initialize_74hc595():
    initial_state = [0b00000000, 0b00000000]
    write_to_74hc595(initial_state)

initialize_74hc595()

test_duration = 0.1
run_duration = 6
interrupt_triggered = False
interrupt_enabled = False

def interrupt_handler(pin):
    global interrupt_triggered
    if interrupt_enabled:
        interrupt_triggered = True

# Set up interrupts on GPIO11
gpio11 = Pin(11, Pin.IN, Pin.PULL_DOWN)
gpio11.irq(trigger=Pin.IRQ_RISING, handler=interrupt_handler)

while True:
    if uart.any():
        received = uart.read(4)  # Read up to 4 bytes
        if received:
            char = received.decode('utf-8').strip()
            print(f"({char})")
            uart.write(f"\n({char})=>")
            if char == 'led':
                led1_on()
                uart.write("tes led status")
            elif char == 'opn':
                lock_12v.value(0)
                lock_trigger.value(1)
                time.sleep(3)
                lock_12v.value(1)
                lock_trigger.value(0)
                uart.write("kunci terbuka")
            elif char.startswith('t'):
                state_key = char[1:]
                if state_key in motor_code:
                    motor_state = motor_code[state_key]
                    write_to_74hc595(motor_state)
                    time.sleep(test_duration)
                    motor_state = [0b00000000, 0b00000000]
                    write_to_74hc595(motor_state)
                    uart.write("test motor")
                else:
                    uart.write("salah perintah")
            elif char in motor_code:
                motor_state = motor_code[char]
                write_to_74hc595(motor_state)
                ir_trigger.value(1)
                time.sleep(0.3)
                interrupt_enabled = True
                for _ in range(run_duration):
                    print("Motor running, second:", _ + 1)
                    uart.write("<MP>")
                    if interrupt_triggered:
                        print("Interrupt triggered!")
                        uart.write("sensor IR bekerja")
                        break
                    time.sleep(0.5)
                interrupt_enabled = False
                motor_state = [0b00000000, 0b00000000]
                write_to_74hc595(motor_state)
                ir_trigger.value(0)
                interrupt_triggered = False
            else:
                uart.write("salah perintah")

