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
    # Pastikan ser sudah terdefinisi (terhubung)
    if ser is None or not ser.is_open:
        text_status_tx.insert(tk.END, "Please connect to a serial device first.\n")
        text_status_tx.see(tk.END)
        return

    list1_value = select_var1.get()
    list2_index = listbox.curselection()  # Mengambil indeks yang dipilih dari listbox
    if list2_index:
        list2_value = listbox.get(list2_index[0])
    else:
        list2_value = "Null"  # Jika tidak ada item yang dipilih

    # Gabungkan list1 dan list2, abaikan 'Null' (tanpa karakter)
    send_value = ""
    if list1_value != "Null":
        send_value += list1_value
    if list2_value != "Null":
        send_value += list2_value

    # Jika tidak ada karakter yang dikirim, beri tahu user
    if send_value == "":
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
window.geometry("540x600")
style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Kirim.TButton",
    padding=10,
    relief="flat",
    background="#c0e0c0",
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
    background="#c0e0c0",
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
baudrate_var.set(baudrate_options[0])  # Nilai default 9600

baudrate_dropdown = ttk.Combobox(frame_baud, textvariable=baudrate_var, values=baudrate_options, state="readonly")
baudrate_dropdown.pack(side="left", expand=True)

button_rescan = ttk.Button(frame_serial, text="Rescan", style="SButton.TButton", command=rescan_ports)
button_rescan.pack(side="left", expand=True)

button_connect = ttk.Button(frame_baud, text="Connect", style="SButton.TButton", command=connect_serial)
button_connect.pack(side="left", expand=True)

# Frame untuk List1 dan List2 di kiri dan kanan
frame_list1 = tk.Frame(window)
frame_list1.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

label_list1 = tk.Label(frame_list1, text="Pilih Perintah", anchor="w", width=15)
label_list1.pack(side="top", anchor="w")

list1_options = [
    ("Nyalakan motor", "Null"),
    ("Autoset Motor", "t"),
    ("Manualset Motor", "m"),
    ("Nyalakan LED", "led"),
    ("Buka Kunci", "opn")
]
select_var1 = tk.StringVar(window)
select_var1.set(list1_options[0][1])  # Nilai default 'Null'

for label, value in list1_options:
    radio_button = tk.Radiobutton(frame_list1, text=label, variable=select_var1, value=value, padx=0)
    radio_button.pack(side="top", anchor="w")

# Frame untuk List2 (di kanan frame_list1)
frame_list2 = tk.Frame(window)
frame_list2.grid(row=3, column=1, padx=10, pady=10, sticky="ew")

label_list2 = tk.Label(frame_list2, text="Pilih Nomor Motor", anchor="w", width=20)
label_list2.pack(side="top", anchor="w")

list2_options = [
    "Null", "00", "02", "04", "06",
    "10", "12", "14", "16", "17",
    "20", "21", "22", "23", "24", "25", "26", "27",
    "30", "31", "32", "33", "34", "35", "36", "37",
    "40", "41", "42", "43", "44", "45", "46", "47",
    "50", "51", "52", "53", "54", "55", "56", "57",
]

# Membuat Listbox dengan scrollbar lebar
listbox = tk.Listbox(frame_list2, height=6)
for item in list2_options:
    listbox.insert(tk.END, item)

# Scrollbar dengan lebar yang lebih besar
scrollbar = tk.Scrollbar(frame_list2, orient="vertical", width=30)  # Menambahkan lebar scrollbar
scrollbar.pack(side="right", fill="y")
listbox.pack(side="right", fill='x', expand=True)

# Menghubungkan scrollbar ke listbox
listbox.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=listbox.yview)

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

text_status_rx = scrolledtext.ScrolledText(frame_status, wrap="word", height=15, width=30, state="normal")
text_status_rx.grid(row=1, column=0, sticky='nsew')

text_status_tx = scrolledtext.ScrolledText(frame_status, wrap="word", height=15, width=30, state="normal")
text_status_tx.grid(row=1, column=1, sticky='nsew')

frame_status.grid_columnconfigure(0, weight=1)
frame_status.grid_columnconfigure(1, weight=1)
frame_status.grid_rowconfigure(1, weight=1)

# Menjalankan loop GUI
window.mainloop()

# Jangan lupa untuk menutup serial ketika selesai
try:
    if ser and ser.is_open:
        ser.close()
except NameError:
    pass
except serial.SerialException:
    pass
