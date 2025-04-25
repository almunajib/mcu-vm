from machine import Pin, UART
import time
import sys
import neopixel
import onewire, ds18x20

# Pengaturan pembacaan serial UART
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
# Pengaturan pinout Neopixel, enable pin lock_12v, lock_trigger, enable ir_trigger, Shift Register, pembacaan suhu & interrupt pin
led_neopixel = Pin(16, Pin.OUT)
#lock_12v = Pin(8, Pin.OUT)
#lock_12v.value(1)
lock_trigger = Pin(7, Pin.OUT)
ir_trigger = Pin(2, Pin.OUT)
ir_fb = Pin(3, Pin.IN, Pin.PULL_DOWN)
interrupt_gpio = [12]
SH_CP = Pin(10, Pin.OUT)  # Clock pin
ST_CP = Pin(9, Pin.OUT)  # Latch pin
DS = Pin(11, Pin.OUT)     # Data pin
DS.value(0)
SH_CP.value(0)
ST_CP.value(0)
ds_pin = machine.Pin(6)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

# Pengaturan test Neopixel berawal
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
# Pengaturan test Neopixel berakhir

# Pengaturan IC Register 74HC595 berawal
def shift_out(value):
    for i in range(8):
        bit = (value >> (7 - i)) & 1
        DS.value(bit)
        SH_CP.value(1)
        SH_CP.value(0)

def write_to_74hc595(values):
    ST_CP.value(0)
    for value in (values):
        shift_out(value)
    ST_CP.value(1)
# Pengaturan kondisi awal motor mati
motor_state = [0b00000000, 0b00000000, 0b00000000]
def initialize_74hc595():
    global motor_state
    motor_state = [0b00000000, 0b00000000, 0b00000000]
    write_to_74hc595(motor_state)
initialize_74hc595()
# Pengaturan IC Register 74HC595 berakhir

# Pengaturan Pembuatan Motor Code berawal
digit_to_binary = {
    0: 0b10000000,
    1: 0b01000000,
    2: 0b00100000,
    3: 0b00010000,
    4: 0b00001000,
    5: 0b00000100,
    6: 0b00000010,
    7: 0b00000001,
    8: 0b01000000,
    9: 0b10000000
}

# Fungsi untuk mengonversi angka ke biner
def convert_to_binary(digit):
    return digit_to_binary.get(digit, 0b00000000)

# Fungsi untuk menghasilkan motor_code secara dinamis
def generate_motor_code():
    motor_code = {}
    for x in range(10):  # baris 0–9
        for y in range(10):  # kolom 0–9
            reg1 = convert_to_binary(x if x < 8 else 0)  # reg1 tetap
            reg2 = convert_to_binary(y if y < 8 else 0)  # kolom <8 di reg2
            reg3 = 0b00000000

            # Kolom 8 dan 9 → Q6 dan Q7
            if y == 8:
                reg3 |= 0b01000000
            elif y == 9:
                reg3 |= 0b10000000

            # Baris 8 dan 9 → Q1 dan Q0
            if x == 8:
                reg3 |= 0b00000010
            elif x == 9:
                reg3 |= 0b00000001

            motor_code[f'{x}{y}'] = [reg3, reg1, reg2]
    return motor_code


# Menghasilkan motor_code
motor_code = generate_motor_code()

# Fungsi untuk menghitung motor_code berdasarkan baris dan kolom
def calculate_motor_code(baris, kolom):
    reg1 = convert_to_binary(baris if baris < 8 else 0)
    reg2 = convert_to_binary(kolom if kolom < 8 else 0)
    reg3 = 0b00000000

    if kolom == 8:
        reg3 |= 0b01000000
    elif kolom == 9:
        reg3 |= 0b10000000

    if baris == 8:
        reg3 |= 0b00000010
    elif baris == 9:
        reg3 |= 0b00000001

    return [reg3, reg1, reg2]
# Pengaturan Pembuatan Motor Code berakhir

# Pengaturan interupt berawal
# Pemetaan baris ke GPIO interrupt
interrupt_ir_fb = False
interrupt_enabled = False
baris_to_gpio = {
    0: 12,
    1: 12,
    2: 12,
    3: 12,
    4: 12,
    5: 12,
    6: 12,
    7: 12,
    8: 12,
    9: 12
}

# Inisialisasi semua GPIO interrupt sebagai input dengan pull-down
interrupt_gpio_status = {gpio: False for gpio in baris_to_gpio.values()}
set_interrupt_gpio = {baris: Pin(gpio, Pin.IN, Pin.PULL_DOWN) for baris, gpio in baris_to_gpio.items()}

# interrupt offset motor
def make_interrupt_handler(pin_num):
    def handler(pin):
        global interrupt_gpio_status
        if interrupt_enabled:
            interrupt_gpio_status[pin_num] = True
            print(f"Interrupt triggered on GPIO {pin_num}")
    return handler
# Daftarkan interupsi untuk setiap GPIO yang terkait dengan baris
for baris, gpio in baris_to_gpio.items():
    set_interrupt_gpio[baris].irq(trigger=Pin.IRQ_RISING, handler=make_interrupt_handler(gpio))
# Fungsi untuk mengaktifkan interupsi hanya pada baris tertentu
def enable_interrupt_for_bar(baris):
    global set_interrupt_gpio
    for pin in set_interrupt_gpio.values():
        pin.irq(handler=None)  # Nonaktifkan semua interupsi
    if baris in baris_to_gpio:
        gpio = baris_to_gpio[baris]
        set_interrupt_gpio[baris].irq(trigger=Pin.IRQ_RISING, handler=make_interrupt_handler(gpio))
        print(f"Interrupt enabled for GPIO {gpio}")

# interrupt sensor IR
def interrupt_handler_ir_fb(pin):
    global interrupt_ir_fb
    if interrupt_enabled:
        interrupt_ir_fb = True
        print("Interrupt IR sensor triggered")
# Daftarkan interrupt sensor IR
ir_fb.irq(trigger=Pin.IRQ_RISING, handler=interrupt_handler_ir_fb)
# Pengaturan interupt berakhir

while True:
    if uart.any():
        received = uart.read(4)
        if received:
            char = received.decode('utf-8').strip()
            print(f"({char})")
            uart.write(f"\n({char})=")
            if char == 'led':
                led1_on()
                uart.write("<tes led>")
            elif char == 'open':
                lock_12v.value(0)
                lock_trigger.value(1)
                time.sleep(3)
                lock_12v.value(1)
                lock_trigger.value(0)
                uart.write("<kunci terbuka>")
            elif char == 'suhu':
                roms = ds_sensor.scan()
                print('Found DS devices:', roms)
                ds_sensor.convert_temp()
                time.sleep_ms(750)  # Tunggu konversi suhu selesai
                for index, rom in enumerate(roms, start=1):
                    tempC = ds_sensor.read_temp(rom)
                    tempF = tempC * (9/5) + 32
                    suhu_c = "{:.1f}".format(tempC)
                    suhu_f = "{:.1f}".format(tempF)
                    output_suhu = f"S{index}: {suhu_c} °C"
                    print(output_suhu + "\n")
                    uart.write(output_suhu + "\n")
            elif char.startswith('ts'):
                state_key = char[2:]
                if state_key in motor_code:
                    motor_state = motor_code[state_key]
                    write_to_74hc595(motor_state)
                    baris = int(state_key[0])
                    enable_interrupt_for_bar(baris)
                    time.sleep(0.4)
                    interrupt_enabled = True                
                    for _ in range(10):
                        time.sleep(0.2)
                        print("test")
                        if any(interrupt_gpio_status.values()):
                            uart.write("<Offset [MP Stop]>")
                            time.sleep(0.4)
                            break
                    interrupt_enabled = False
                    initialize_74hc595()
                    print(f"Motor Berhenti")
                    interrupt_gpio_status = {p: False for p in interrupt_gpio}
                else:
                    uart.write("salah perintah")
            elif char.startswith('mp'):
                state_key = char[2:]
                if state_key in motor_code:
                    motor_state = motor_code[state_key]
                    write_to_74hc595(motor_state)
                    ir_trigger.value(1)
                    time.sleep(0.4)
                    baris = int(state_key[0])
                    enable_interrupt_for_bar(baris)
                    interrupt_enabled = True                    
                    for _ in range(12):
                        time.sleep(0.2)
                        print("Running on:", _ + 1)
                        uart.write("<MP>")
                        if interrupt_ir_fb:
                            uart.write("<sensor IR bekerja>")
                            time.sleep(0.4)
                            break  
                        elif any(interrupt_gpio_status.values()):
                            uart.write("<Offset [MP Stop]>")
                            time.sleep(0.4)
                            break
                    interrupt_enabled = False
                    initialize_74hc595()
                    print(f"Motor Berhenti")
                    ir_trigger.value(0)
                    interrupt_gpio11 = False
                    interrupt_gpio_status = {p: False for p in interrupt_gpio}
                else:
                    uart.write("salah perintah")
            elif char.startswith('m'):
                state_key = char[1:]
                if state_key in motor_code:
                    motor_state = motor_code[state_key]
                    write_to_74hc595(motor_state)
                    time.sleep(0.05)
                    uart.write("<set>")
                    initialize_74hc595()
                else:
                    uart.write("salah perintah")

