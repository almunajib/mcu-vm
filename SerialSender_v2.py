import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import serial
import serial.tools.list_ports

# Variabel global untuk serial
ser = None

# Fungsi untuk memindai port serial yang tersedia
def scan_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def rescan_ports():
    serial_ports = scan_serial_ports()
    serial_dropdown["values"] = serial_ports
    if serial_ports:
        serial_var.set(serial_ports[0])  # Set default ke perangkat pertama jika ada
    else:
        serial_var.set("No Device")
        
# Fungsi untuk menghubungkan ke serial port
def connect_serial():
    global ser
    selected_port = serial_var.get()
    selected_baud = baudrate_var.get()
    try:
        ser = serial.Serial(selected_port, selected_baud, timeout=1)
        print(f"Connected to {selected_port} with baud rate {selected_baud}")
        text_status_rx.insert(tk.END, f"Connected to {selected_port} at {selected_baud}\n")
        text_status_rx.see(tk.END)
        read_serial_data()  # Mulai membaca data
    except serial.SerialException as e:
        print(f"Error: {e}")
        text_status_rx.insert(tk.END, f"Failed to connect to {selected_port}.\nError: {e}\n")
        text_status_rx.see(tk.END)

# Fungsi untuk mengirim karakter yang dipilih dari dua list
def send_selected():
    global ser
    # Pastikan ser sudah terhubung
    if ser is None or not ser.is_open:
        text_status_tx.insert(tk.END, "Please connect to a serial device first.\n")
        text_status_tx.see(tk.END)
        return

    list1_value = select_var1.get()
    list2_value = select_var_x.get() + select_var_y.get()  # Gabungkan X dan Y axis
    send_value = list1_value + list2_value

    # Jika tidak ada karakter yang dikirim, beri tahu user
    if not send_value:
        text_status_tx.insert(tk.END, "Tidak ada karakter yang dikirim.\n")
        text_status_tx.see(tk.END)
    else:
        try:
            ser.write(send_value.encode())
            print(f"Sent: {send_value}")
            text_status_tx.insert(tk.END, f"Sent: {send_value}\n")
            text_status_tx.see(tk.END)
        except serial.SerialException as e:
            print(f"Error: {e}")
            text_status_tx.insert(tk.END, f"Failed to send data.\nError: {e}\n")
            text_status_tx.see(tk.END)

# Fungsi untuk membaca data dari serial
def read_serial_data():
    if ser and ser.is_open:
        if ser.in_waiting > 0:
            received_data = ser.read(ser.in_waiting).decode('utf-8')
            text_status_rx.insert(tk.END, received_data)
            text_status_rx.see(tk.END)
        # Jadwalkan pembacaan data berikutnya
        window.after(500, read_serial_data)  # Pembacaan setiap 500ms

# Membuat window GUI
window = tk.Tk()
window.title("Serial Sender")
window.geometry("540x540")
style = ttk.Style()
style.theme_use("vista")
style.configure(
    "Kirim.TButton",
    padding=10,
    relief="flat",
    focusthickness=3,
    focuscolor="green",
    width=10
)
style.map(
    "Kirim.TButton", background=[("active", "#70e070"), ("pressed", "green")],
    bordercolor=[("active", "red"), ("pressed", "green")]
)
style.configure(
    "SButton.TButton",
    padding=1,
    relief="flat",
    focusthickness=3,
    focuscolor="green",
    width=10
)
style.map(
    "SButton.TButton", background=[("active", "#70e070"), ("pressed", "green")]
)

# Label "Pilih Serial Device & Baudrate" di atas kedua frame, rata tengah
label_serial = tk.Label(window, text="Pilih Serial Device & Baudrate", anchor="center", width=40)
label_serial.grid(row=0, column=0, columnspan=2, padx=2, pady=10, sticky="ew")

# Frame untuk Pilih Serial Device dan Baudrate (pakai grid untuk menempatkan berdampingan)
frame_serial = tk.Frame(window)
frame_serial.grid(row=1, column=0, padx=2, pady=2, sticky="ew")

serial_ports = scan_serial_ports()
serial_var = tk.StringVar(window)
serial_var.set(serial_ports[0] if serial_ports else "No Device")  # Nilai default

serial_dropdown = ttk.Combobox(frame_serial, textvariable=serial_var, values=serial_ports, state="readonly")
serial_dropdown.pack(side="left", expand=True)

frame_baud = tk.Frame(window)
frame_baud.grid(row=1, column=1, padx=2, pady=2, sticky="ew")

baudrate_options = ["9600", "19200", "38400", "57600", "115200"]
baudrate_var = tk.StringVar(window)
baudrate_var.set(baudrate_options[4])  # Nilai default BAUDRATE

baudrate_dropdown = ttk.Combobox(frame_baud, textvariable=baudrate_var, values=baudrate_options, state="readonly")
baudrate_dropdown.pack(side="left", expand=True)

button_rescan = ttk.Button(frame_serial, text="Rescan", style="SButton.TButton", command=rescan_ports)
button_rescan.pack(side="left", expand=True)

button_connect = ttk.Button(frame_baud, text="Connect", style="SButton.TButton", command=connect_serial)
button_connect.pack(side="left", expand=True)

# Frame untuk List1 (Pilih Perintah) di kiri dan kanan
frame_list1 = tk.Frame(window)
frame_list1.grid(row=3, column=0, padx=15, pady=15, sticky="ew")

label_list1 = tk.Label(frame_list1, text="Pilih Perintah", anchor="center", width=15)
label_list1.grid(row=0, column=0, columnspan=2, sticky="ew")

# Membuat dua kolom dalam frame_list1
frame_list1_left = tk.Frame(frame_list1)
frame_list1_left.grid(row=1, column=0, sticky="w")

frame_list1_right = tk.Frame(frame_list1)
frame_list1_right.grid(row=1, column=1, sticky="w")

# List1 options untuk kolom kiri (Kolom pertama)
list1_options_left = [
    ("Nyalakan motor", "mp"),
    ("Autoset Motor", "ts"),
    ("Manualset Motor", "m"),
]
select_var1 = tk.StringVar(window)
select_var1.set(list1_options_left[0][1])

for label, value in list1_options_left:
    radio_button = tk.Radiobutton(frame_list1_left, text=label, variable=select_var1, value=value, padx=0)
    radio_button.pack(side="top", anchor="w")

# List1 options untuk kolom kanan (Kolom kedua)
list1_options_right = [
    ("Nyalakan LED", "led"),
    ("Buka Kunci", "open"),
    ("Cek suhu", "suhu")
]

for label, value in list1_options_right:
    radio_button = tk.Radiobutton(frame_list1_right, text=label, variable=select_var1, value=value, padx=0)
    radio_button.pack(side="top", anchor="w")

# Frame untuk List2 (Pilih Motor: X axis dan Y axis)
frame_list2 = tk.Frame(window)
frame_list2.grid(row=3, column=1, padx=10, pady=15, sticky="ns")

# Label utama di atas kedua kolom
label_motor = tk.Label(frame_list2, text="Pilih Motor")
label_motor.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

# Frame untuk X dan Y
frame_xy = tk.Frame(frame_list2)
frame_xy.grid(row=1, column=0, columnspan=2)

# --- X axis control ---
label_x = tk.Label(frame_xy, text="Nomer Rak", anchor="n")
label_x.grid(row=0, column=0, padx=(0, 30), sticky="ew")

# Menambahkan "Null" sebagai opsi pertama dalam list2_options
list2_options = [""] + [str(i) for i in range(10)]
select_var_x = tk.StringVar(window)
select_var_x.set("")  # Default ke "Null"
dropdown_x = ttk.Combobox(frame_xy, textvariable=select_var_x, values=list2_options, state="readonly", width=10)
dropdown_x.grid(row=1, column=0, padx=(0, 30), pady=2)

# --- Y axis Line Out ---
label_y = tk.Label(frame_xy, text="Nomer Slot", anchor="n")
label_y.grid(row=0, column=1, sticky="ew")

select_var_y = tk.StringVar(window)
select_var_y.set("")  # Default ke "Null"
dropdown_y = ttk.Combobox(frame_xy, textvariable=select_var_y, values=list2_options, state="readonly", width=10)
dropdown_y.grid(row=1, column=1, pady=2)

# Label untuk preview hasil gabungan X + Y
label_preview = tk.Label(frame_list2, text="Preview Motor")
label_preview.grid(row=2, column=0, columnspan=2, pady=(10, 0))

# Fungsi untuk update label preview secara real-time
def update_motor_preview(*args):
    motor_number = select_var_x.get() + select_var_y.get()
    label_preview.config(text=f"Motor Terpilih: {motor_number}")

# Fungsi untuk update list2_options ketika perintah tertentu dipilih
def update_list2_options(*args):
    list1_value = select_var1.get()

    if list1_value in ["led", "open", "suhu"]:
        select_var_x.set("")
        select_var_y.set("")
        dropdown_x['values'] = [""]
        dropdown_y['values'] = [""]
    else:
        select_var_x.set("")
        select_var_y.set("")
        dropdown_x['values'] = list2_options
        dropdown_y['values'] = list2_options

# Setelah membuat select_var_x dan select_var_y, tambahkan trace ini sekali saja
select_var_x.trace_add("write", update_motor_preview)
select_var_y.trace_add("write", update_motor_preview)

# Tambahkan juga ini setelah select_var1 dibuat
select_var1.trace_add("write", update_list2_options)


# Tombol untuk mengirim karakter dari kedua list
button_send = ttk.Button(window, text="Kirim", style="Kirim.TButton", command=send_selected)
button_send.grid(row=4, column=0, columnspan=2, pady=10)

# Frame untuk status RX dan TX
frame_status = tk.Frame(window)
frame_status.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

label_status_rx = tk.Label(frame_status, text="Status RX Serial", anchor="w")
label_status_rx.grid(row=0, column=0, sticky='w')

label_status_tx = tk.Label(frame_status, text="Status TX Serial", anchor="e")
label_status_tx.grid(row=0, column=1, sticky='e')

text_status_rx = scrolledtext.ScrolledText(frame_status, height=14, width=30)
text_status_rx.grid(row=1, column=0, pady=5)

text_status_tx = scrolledtext.ScrolledText(frame_status, height=14, width=30)
text_status_tx.grid(row=1, column=1, pady=5)

# Start GUI event loop
window.mainloop()
