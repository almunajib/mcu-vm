import gi
import serial
import serial.tools.list_ports
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

# Variabel global untuk serial
ser = None
selected_motor = "Null"  # Inisialisasi nomor motor yang terpilih secara default

# Fungsi untuk memindai port serial yang tersedia
def scan_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]
    
def rescan_ports(combo):
    combo.remove_all()
    serial_ports = scan_serial_ports()
    for port in serial_ports:
        combo.append_text(port)
    if serial_ports:
        combo.set_active(0)

# Fungsi untuk menggulir ke bawah pada TextView
def scroll_to_bottom(text_view):
    buffer = text_view.get_buffer()  # Mengambil buffer dari TextView
    end_iter = buffer.get_end_iter()  # Mengambil posisi akhir dari buffer
    text_view.scroll_to_iter(end_iter, 0.0, True, 0.0, 1.0)  # Menggulir ke posisi akhir

# Fungsi untuk menghubungkan ke serial port
def connect_serial(button):
    global ser
    selected_port = serial_var.get_active_text()
    selected_baud = baudrate_var.get_active_text()
    try:
        ser = serial.Serial(selected_port, selected_baud, timeout=1)
        print(f"Connected to {selected_port} with baud rate {selected_baud}")
        text_status_rx.get_buffer().insert_at_cursor(f"Connected to {selected_port} at {selected_baud}\n")
        scroll_to_bottom(text_status_rx)  # Scroll ke bawah setelah teks ditambahkan
        read_serial_data()  # Mulai membaca data
    except serial.SerialException as e:
        print(f"Error: {e}")
        text_status_rx.get_buffer().insert_at_cursor(f"Failed to connect to {selected_port}.\nError: {e}\n")
        scroll_to_bottom(text_status_rx)  # Scroll ke bawah setelah teks ditambahkan

# Fungsi untuk mengirim karakter yang dipilih dari dua list
def send_selected(button):
    global ser
    # Pastikan ser sudah terdefinisi (terhubung)
    if ser is None or not ser.is_open:
        text_status_tx.get_buffer().insert_at_cursor("Please connect to a serial device first.\n")
        scroll_to_bottom(text_status_tx)  # Scroll ke bawah setelah teks ditambahkan
        return

    list1_value = selected_perintah  # Ambil nilai dari radio button yang dipilih
    selected_row = listbox.get_selected_row()  # Mengambil baris yang dipilih dari listbox
    if selected_row:
        list2_value = selected_row.get_children()[0].get_text()  # Ambil teks dari label di dalam row
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
        text_status_tx.get_buffer().insert_at_cursor("Tidak ada karakter yang dikirim.\n")
    else:
        try:
            ser.write(send_value.encode())
            print(f"Sent: {send_value}")
            text_status_tx.get_buffer().insert_at_cursor(f"Sent: {send_value}\n")
        except serial.SerialException as e:
            print(f"Error: {e}")
            text_status_tx.get_buffer().insert_at_cursor(f"Failed to send data.\nError: {e}\n")

    scroll_to_bottom(text_status_tx)  # Scroll ke bawah setelah teks ditambahkan

# Fungsi untuk membaca data dari serial
def read_serial_data():
    if ser and ser.is_open:
        if ser.in_waiting > 0:
            received_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            text_status_rx.get_buffer().insert_at_cursor(received_data)
            print(f"Received: {received_data}")
            scroll_to_bottom(text_status_rx)  # Scroll ke bawah setelah teks diterima
        GLib.timeout_add(50, read_serial_data)  # Pembacaan setiap 50ms
    return False

# Fungsi untuk menangani perubahan pada radio button
def on_radio_button_toggled(button, user_data):
    global selected_perintah
    if button.get_active():
        selected_perintah = user_data
        print(f"Perintah terpilih: {selected_perintah}")

# Fungsi untuk menangani perubahan pada pemilihan nomor motor
def on_motor_selected(listbox, row):
    global selected_motor
    if row:
        selected_motor = row.get_children()[0].get_text()  # Ambil teks dari label di dalam row
        print(f"Nomor motor terpilih: {selected_motor}")
    else:
        selected_motor = "Null"  # Jika tidak ada item yang dipilih
        print("Nomor motor terpilih: Null")

# CSS Styling
css_provider = Gtk.CssProvider()
css_provider.load_from_data(b"""
window {
    background-color: #f5fff5;
}
button {
    background-color: #f5fff5;
    color: black;
    min-width: 22px;
    min-height: 18px;
    border-radius: 7px;
    border: 2px solid #a0e0a0;
}
button:hover {
    background-color: #a0e0a0;
    border-color: darkgreen;
}
combobox menu {
    background-color: #f5fff5;
    border: 2px solid #a0e0a0;
}
combobox menu item {
    padding: 5px;
    background-color: #f5fff5;
    color: black;
}
list row:hover {
    background-color: #f5fff5;
    color: black;
}
list row:selected {
    background-color: #a0e0a0;
    color: white;
    font-weight: bold;
}
scrolledwindow {
    background-color: #f5fff5;
}
scrollbar {
    min-width: 20px;
    min-height: 20px;
}
scrollbar slider {
    background-color: #f5fff5;
    border-radius: 5px;
    min-width: 20px;
    min-height: 20px;
}
scrollbar slider:hover {
    background-color: #a0e0a0;
}
""")

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    css_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

# Membuat window GUI menggunakan Gtk
window = Gtk.Window(title="Serial Sender")
window.set_size_request(500, 500)
window.connect("destroy", Gtk.main_quit)

# Membuat Box Layout utama
main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
window.add(main_box)
label_serial = Gtk.Label(label="Pilih Serial Port & Baudrate")
main_box.pack_start(label_serial, False, False, 2)

# Box untuk memilih Serial Device dan Baudrate
select_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
main_box.pack_start(select_box, False, False, 2)


# Kolom kiri untuk Serial Device
serial_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
serial_ports = scan_serial_ports()
serial_var = Gtk.ComboBoxText()
for port in serial_ports:
    serial_var.append_text(port)
serial_var.set_active(0)  # Set default value
serial_box.pack_start(serial_var, False, False, 1)
serial_box.set_halign(Gtk.Align.CENTER)

button_rescan = Gtk.Button(label="Rescan")
button_rescan.connect("clicked", lambda x: rescan_ports(serial_combo))
serial_box.pack_start(button_rescan, False, False, 2)

# Kolom kanan untuk Baud Rate
baud_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
baudrate_options = ["9600", "19200", "38400", "57600", "115200"]
baudrate_var = Gtk.ComboBoxText()
for option in baudrate_options:
    baudrate_var.append_text(option)
baudrate_var.set_active(0)  # Set default value
baud_box.pack_start(baudrate_var, False, False, 2)
baud_box.set_halign(Gtk.Align.CENTER)

button_connect = Gtk.Button(label="Connect")
button_connect.connect("clicked", connect_serial)
baud_box.pack_start(button_connect, False, False, 2)
button_connect.set_halign(Gtk.Align.CENTER)

# Gabungkan semua ke dalam select_box
select_box.pack_start(serial_box, True, True, 2)
select_box.pack_start(baud_box, True, True, 2)


# Box untuk memilih Perintah dan Nomor Motor
command_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
main_box.pack_start(command_box, False, False, 6)

# Kolom untuk Pilih Perintah
perintah_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
label_perintah = Gtk.Label(label="Pilih Perintah")
perintah_box.pack_start(label_perintah, False, False, 2)

# Buat box vertikal untuk radio button
radio_button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
perintah_box.pack_start(radio_button_box, True, True, 2)

# Buat grup radio button
radio_group = None
radio_buttons = []

# List opsi perintah
list1_options = [
    ("Nyalakan motor", "Null"),
    ("Autoset Motor", "t"),
    ("Manualset Motor", "m"),
    ("Nyalakan LED", "led"),
    ("Buka Kunci", "opn")
]

# Tambahkan radio button untuk setiap opsi
for label, value in list1_options:
    radio_button = Gtk.RadioButton.new_with_label_from_widget(radio_group, label)
    radio_button.connect("toggled", on_radio_button_toggled, value)
    if radio_group is None:
        radio_group = radio_button  # Set grup pertama
    radio_button_box.pack_start(radio_button, False, False, 2)
    radio_buttons.append(radio_button)
radio_button_box.set_halign(Gtk.Align.CENTER)

# Set perintah yang dipilih secara default
selected_perintah = "Null"  # Perintah default

# Kolom untuk Pilih Nomor Motor
nomor_motor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
label_nomor_motor = Gtk.Label(label="Pilih Nomor Motor")
nomor_motor_box.pack_start(label_nomor_motor, False, False, 2)

# Pilih Nomor Motor
list2_options = [
    "Null", "00", "02", "04", "06", "10", "12", "14", "15", "16", "17", "20", "21", "22", "23", "24", "25", "26", "27",
    "30", "31", "32", "33", "34", "35", "36", "37", "40", "41", "42", "43", "44", "45", "46", "47", "50", "51", "52", "53", "54", "55", "56", "57"
]
listbox = Gtk.ListBox()
for item in list2_options:
    row = Gtk.ListBoxRow()
    row.add(Gtk.Label(label=item))
    listbox.add(row)

scrolled_window = Gtk.ScrolledWindow()
scrolled_window.add(listbox)
nomor_motor_box.pack_start(scrolled_window, True, True, 4)
nomor_motor_box.set_halign(Gtk.Align.CENTER)

# Gabungkan kedua box ini ke dalam command_box
command_box.pack_start(perintah_box, True, True, 2)
command_box.pack_start(nomor_motor_box, True, True, 2)

# Hubungkan sinyal 'row-selected' dari listbox ke fungsi on_motor_selected
listbox.connect("row-selected", on_motor_selected)

# Tombol untuk mengirim karakter dari kedua list
button_send = Gtk.Button(label="Kirim")
button_send.connect("clicked", send_selected)
button_send.set_size_request(100, 40)
main_box.pack_start(button_send, False, False, 4)
button_send.set_halign(Gtk.Align.CENTER)

# Box untuk status RX dan TX
status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
main_box.pack_start(status_box, True, True, 4)

# Status RX
status_rx_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
label_status_rx = Gtk.Label(label="Status RX Serial")
status_rx_box.pack_start(label_status_rx, False, False, 2)

# Membuat TextView untuk Status RX
text_status_rx = Gtk.TextView()
text_status_rx.set_wrap_mode(Gtk.WrapMode.WORD)

scrolled_window_rx = Gtk.ScrolledWindow()
scrolled_window_rx.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
scrolled_window_rx.add(text_status_rx)

status_rx_box.pack_start(scrolled_window_rx, True, True, 4)
status_box.pack_start(status_rx_box, True, True, 2)

# Status TX
status_tx_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
label_status_tx = Gtk.Label(label="Status TX Serial")
status_tx_box.pack_start(label_status_tx, False, False, 2)
text_status_tx = Gtk.TextView()
text_status_tx.set_wrap_mode(Gtk.WrapMode.WORD)

scrolled_window_tx = Gtk.ScrolledWindow()
scrolled_window_tx.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
scrolled_window_tx.add(text_status_tx)

status_tx_box.pack_start(scrolled_window_tx, True, True, 4)
status_box.pack_start(status_tx_box, True, True, 2)

# Menjalankan loop GUI
window.show_all()
Gtk.main()

# Jangan lupa untuk menutup serial ketika selesai
try:
    if ser and ser.is_open:
        ser.close()
except NameError:
    pass
except serial.SerialException:
    pass
