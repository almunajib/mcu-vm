from machine import Pin, UART
import time
import neopixel
import onewire, ds18x20

# Pengaturan pembacaan serial UART
uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
# Pengaturan pinout Neopixel, enable pin lock_12v, lock_trigger, enable ir_trigger, Shift Register, & pembacaan suhu
led_neopixel = Pin(16, Pin.OUT)
lock_12v = Pin(14, Pin.OUT)
lock_12v.value(1)
lock_trigger = Pin(13, Pin.OUT)
ir_trigger = Pin(10, Pin.OUT)
SH_CP = Pin(26, Pin.OUT)  # Clock pin
ST_CP = Pin(15, Pin.OUT)  # Latch pin
DS = Pin(27, Pin.OUT)     # Data pin
DS.value(0)
SH_CP.value(0)
ST_CP.value(0)
ds_pin = machine.Pin(12)
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
    for value in values:
        shift_out(value)
    ST_CP.value(1)
# Pengaturan kondisi awal motor mati
motor_state = [0b00000000, 0b00000000]
def initialize_74hc595():
    initial_state = [0b00000000, 0b00000000]
    write_to_74hc595(initial_state)
initialize_74hc595()
# Pengaturan durasi motor menyala
test_duration = 5
run_duration = 7
IR_detection = 5
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
# Pengaturan Pembuatan Motor Code berakhir

# Pengaturan interupt berawal
# Digunakan untuk menghentikan motor saat mendeteksi Offset Motor (GPIO 0,1,2,3,6,7) atau barang sudah terbaca oleh sensor IR (GPIO 11)
interrupt_gpio = [0, 1, 2, 3, 6, 7]
interrupt_gpio_status = {p: False for p in interrupt_gpio}
interrupt_gpio11 = False
interrupt_enabled = False

set_interrupt_gpio = [Pin(p, Pin.IN, Pin.PULL_DOWN) for p in interrupt_gpio]
gpio11 = Pin(11, Pin.IN, Pin.PULL_DOWN)

# Callback untuk GPIO selain GPIO 11
def make_interrupt_handler(pin_num):
    def handler(pin):
        global interrupt_gpio_status
        if interrupt_enabled:
            interrupt_gpio_status[pin_num] = True
            print(f"Interrupt triggered on GPIO {pin_num}")
    return handler

# Callback untuk GPIO 11
def interrupt_handler_gpio11(pin):
    global interrupt_gpio11
    if interrupt_enabled:
        interrupt_gpio11 = True
        print("Interrupt triggered on GPIO 11")

# Daftarkan interrupt untuk setiap GPIO
interrupt_handlers = {p: make_interrupt_handler(p) for p in interrupt_gpio}
for p in interrupt_gpio:
    pin_obj = Pin(p, Pin.IN, Pin.PULL_DOWN)
    pin_obj.irq(trigger=Pin.IRQ_RISING, handler=interrupt_handlers[p])

# Daftarkan interrupt untuk GPIO 11
gpio11.irq(trigger=Pin.IRQ_RISING, handler=interrupt_handler_gpio11)

def enable_interrupt_for_bar(baris):
    global set_interrupt_gpio
    for pin in set_interrupt_gpio:
        pin.irq(handler=None)
    if baris in interrupt_gpio:
        set_interrupt_gpio[baris].irq(trigger=Pin.IRQ_RISING, handler=make_interrupt_handler(baris))
        print(f"Interrupt open for GPIO {baris}")
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
            elif char == 'opn':
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
            elif char.startswith('t'):
                state_key = char[1:]
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
                    motor_state = [0b00000000, 0b00000000]
                    write_to_74hc595(motor_state)
                    print(f"Motor Berhenti")
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
                    motor_state = [0b00000000, 0b00000000]
                    write_to_74hc595(motor_state)
                else:
                    uart.write("salah perintah")
            elif char in motor_code:
                motor_state = motor_code[char]
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
                    if interrupt_gpio11:
                        uart.write("<sensor IR bekerja>")
                        time.sleep(0.4)
                        break  
                    elif any(interrupt_gpio_status.values()):
                        uart.write("<Offset [MP Stop]>")
                        time.sleep(0.4)
                        break
                interrupt_enabled = False
                motor_state = [0b00000000, 0b00000000]
                write_to_74hc595(motor_state)
                print(f"Motor Berhenti")
                ir_trigger.value(0)
                interrupt_gpio11 = False
                interrupt_gpio_status = {p: False for p in interrupt_gpio}
            else:
                uart.write("salah perintah")
