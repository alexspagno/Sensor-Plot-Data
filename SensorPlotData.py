import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont

import serial
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from collections import deque
import sys  
import json
import os
from tkinter import filedialog
import csv

recording = False
recorded_data = []

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
CONFIG_FILE = "config.json"

# === VARIABILI GLOBALI ===
max_points = 200
counter = 0
serial_conn = None
data_updated = False
is_live_plotting = True
data_ready = False


data_y = [deque(maxlen=10000) for _ in range(5)]
x_data = deque(maxlen=10000)

colors = ['g', 'b', 'r', 'orange', 'purple']
labels = ['Y1', 'Y2', 'Y3', 'Y4', 'Y5']
label_entries = []  
unit_entries = []
scale_entries = []

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print("Config file not found.")
        return
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return
    for i in range(min(len(config.get("labels", [])), len(label_entries))):
        label_entries[i].delete(0, tk.END)
        label_entries[i].insert(0, config["labels"][i])
    for i in range(min(len(config.get("units", [])), len(unit_entries))):
        unit_entries[i].delete(0, tk.END)
        unit_entries[i].insert(0, config["units"][i])
    for i in range(min(len(config.get("scales", [])), len(scale_entries))):
        scale_entries[i].delete(0, tk.END)
        scale_entries[i].insert(0, config["scales"][i])
    if "port" in config:
        port_entry.delete(0, tk.END)
        port_entry.insert(0, config["port"])
    if "baud" in config:
        baud_entry.delete(0, tk.END)
        baud_entry.insert(0, config["baud"])
    if "points" in config:
        points_entry.delete(0, tk.END)
        points_entry.insert(0, config["points"])
    print("Config load success.")

def save_config():
    config = {
        "labels": [entry.get() for entry in label_entries],
        "units": [entry.get() for entry in unit_entries],
        "scales": [entry.get() for entry in scale_entries],
        "port": port_entry.get(),
        "baud": baud_entry.get(),
        "points": points_entry.get()
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    print("Config Update.")

def close_app():
    global serial_conn
    if serial_conn and serial_conn.is_open:
        serial_conn.close()
    plt.close('all')
    root.destroy()
    sys.exit(0)

def create_labeled_entry(label, default, row, col):
    ttk.Label(controls, text=label).grid(row=row, column=col, sticky='e', padx=5, pady=2)
    entry = ttk.Entry(controls, width=10)
    entry.insert(0, str(default))
    entry.grid(row=row, column=col + 1, padx=5, pady=2)
    return entry

def update_axes_scale():
    for i in range(5):
        try:
            y_min, y_max = map(float, scale_entries[i].get().split(','))
            ax_list[i].set_ylim(y_min, y_max)
            label = label_entries[i].get()
            unit = unit_entries[i].get()
            ax_list[i].set_ylabel(f"{label} ({unit})")
        except Exception as e:
            print(f"Axis Error {i+1}:", e)

def connect_serial():
    global serial_conn, is_live_plotting, counter, data_ready
    try:
        serial_conn = serial.Serial(port_entry.get(), int(baud_entry.get()), timeout=1)
        print("Connected to", serial_conn.port)

        # Reset dati
        counter = 0
        x_data.clear()
        for i in range(5):
            data_y[i].clear()
            lines[i].set_data([], [])

        # Reset slider
        scroll_slider.config(to=0)
        scroll_slider.set(0)

        # Reset asse X
        ax_base.set_xlim(0, int(points_entry.get()))
        canvas.draw_idle()

        is_live_plotting = True 
        data_ready = False
        ani.event_source.start()
        threading.Thread(target=read_serial, daemon=True).start()
    except Exception as e:
        print("Connection Error:", e)



def disconnect_serial():
    global serial_conn
    if serial_conn:
        serial_conn.close()
        serial_conn = None
        print("Disconnected")

        
def toggle_connection():
    global serial_conn
    if serial_conn and serial_conn.is_open:
        disconnect_serial()
        connect_button.config(text="Connect")
    else:
        connect_serial()
        if serial_conn and serial_conn.is_open:
            connect_button.config(text="Disconnect")        

def start_recording():
    global recording, recorded_data
    recorded_data = []
    recording = True
    print("Start Recording.")

def stop_recording():
    global recording
    recording = False
    print("Stop Recording.")
    if not recorded_data:
        print("No data to save.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                             filetypes=[("CSV files", "*.csv")],
                                             title="Save CSV file")
    if file_path:
        try:
            with open(file_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                header = [entry.get() for entry in label_entries]
                writer.writerow(header)
                writer.writerows(recorded_data)
            print(f"Data saved in {file_path}")
        except Exception as e:
            print(f"Error saving CSV: {e}")

def load_csv_file():
    global counter, is_live_plotting
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return
    try:
        with open(file_path, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            print("Empty file.")
            return
        header = rows[0]
        data_rows = rows[1:]
        if len(header) != 5:
            print("The CSV file must contain exactly 5 columns.")
            return
        for i in range(5):
            label_entries[i].delete(0, tk.END)
            label_entries[i].insert(0, header[i])
        for i in range(5):
            data_y[i].clear()
        x_data.clear()
        for idx, row in enumerate(data_rows):
            try:
                values = [float(val) for val in row]
            except ValueError:
                print(f"Line not valid {idx + 2}: {row}")
                continue
            for i in range(5):
                data_y[i].append(values[i])
            x_data.append(idx * 50)
        counter = len(x_data)        
        scroll_slider.config(to=max(0, len(x_data) - int(points_entry.get())))
        scroll_slider.set(0)
        ani.event_source.stop()
        is_live_plotting = False
        update_axes_scale()  # <-- forza l'applicazione delle scale definite dall'utente
        update_plot_from_slider(0)
        print(f"✅ File '{file_path}' Load success.")       
        
    except Exception as e:
        print(f"Error loading file: {e}")

def update_plot_from_slider(start_idx):
    try:
        window = int(points_entry.get())
        end_idx = start_idx + window
        x_vals = list(x_data)[start_idx:end_idx]
        for idx in range(5):
            y_vals = list(data_y[idx])[start_idx:end_idx]
            if len(x_vals) == len(y_vals):
                lines[idx].set_data(x_vals, y_vals)
            else:
                print(f"Mismatch x/y: {len(x_vals)} vs {len(y_vals)} (asse {idx+1})")
        if x_vals:
            ax_base.set_xlim(x_vals[0], x_vals[-1])
        else:
            ax_base.set_xlim(0, window)
        canvas.draw_idle()
    except Exception as e:
        print("Error updating chart:", e)


def read_serial():
    global counter, data_updated
    while serial_conn and serial_conn.is_open:
        try:
            line = serial_conn.readline().decode('utf-8').strip()
            parts = line.split(',')
            if len(parts) == 5:
                try:
                    values = [float(p) for p in parts]
                except ValueError:
                    print(f"Non-convertible data: {parts}")
                    continue
                for i in range(5):
                    data_y[i].append(values[i])
                x_data.append(counter * 50)
                counter += 1
                data_updated = True
                global data_ready
                if not data_ready:
                    data_ready = True
                if recording:
                    recorded_data.append(values)
            else:
                print("Incomplete data:", line)
        except Exception as e:
            print("Error Serial Read:", e)

def animate(i):
    global data_updated
    if not is_live_plotting or not data_updated or not data_ready:
        return
        
    
        
    data_updated = False
    try:
        update_axes_scale()
        window = int(points_entry.get())
        x_vals = list(x_data)[-window:]
        for idx in range(5):
            y_vals = list(data_y[idx])[-window:]
            if len(x_vals) == len(y_vals):
                lines[idx].set_data(x_vals, y_vals)
            else:
                print(f"Mismatch x/y: {len(x_vals)} vs {len(y_vals)} (asse {idx+1})")
        if len(x_vals) >= window:
            ax_base.set_xlim(x_vals[0], x_vals[-1])
        else:
            ax_base.set_xlim(0, window)
        canvas.draw_idle()
    except Exception as e:
        print("Plot Error:", e)

root = tk.Tk()
root.protocol("WM_DELETE_WINDOW", close_app)
root.geometry("1200x900")
root.title("Sensor Plot Data V1.0")
root.configure(bg="#2b2b2b")  # sfondo scuro del root

# (modifica stile)
style = ttk.Style(root)
style.theme_use('default')
style.configure("TButton", background="#444444", foreground="white", padding=6)
style.map("TButton", background=[("active", "#666666")])
style.configure("TEntry", fieldbackground="#444444", foreground="white")
style.configure("TLabel", background="#2b2b2b", foreground="white")

# Personalizzazione cursore dello slider (verde e rotondeggiante)
style.configure("TScale",
    troughcolor="#cccccc",         # colore della barra dello slider
    background="#2b2b2b",          # colore sfondo slider
    sliderthickness=14             # spessore cursore
)

style.map("TScale",
    background=[("!disabled", "#00cc44")],  # verde cursore
    foreground=[("!disabled", "#00cc44")]
)


# Matplotlib figure
fig, ax_base = plt.subplots()
fig.subplots_adjust(right=0.65)
fig.patch.set_facecolor("#2b2b2b")      # sfondo esterno figura
ax_base.set_facecolor("#3c3f41")        # sfondo area grafico
ax_base.get_yaxis().set_visible(False)  # nasconde Y sinistro

# 👉 Colore asse X bianco
ax_base.tick_params(axis='x', colors='white')
ax_base.spines['bottom'].set_color('white')
ax_base.xaxis.label.set_color('white')
ax_base.set_xlabel("Time (ms)", color='white')

ax_list = []
for i in range(5):
    ax = ax_base.twinx()
    ax.spines["right"].set_position(("axes", 1.0 + i * 0.12))
    ax.spines["right"].set_color(colors[i])
    ax.tick_params(axis='y', colors=colors[i])
    ax.yaxis.label.set_color(colors[i])
    ax.set_autoscale_on(False)
    ax_list.append(ax)

lines = []
for i in range(5):
    line, = ax_list[i].plot([], [], color=colors[i], label=labels[i])
    lines.append(line)

# === HEADER FRAME con titolo e grafico colori ===
header_frame = tk.Frame(root, bg="#2b2b2b")
header_frame.pack(fill='x', pady=(10, 0), padx=10)

# Sottocontenitore centrato per titolo + rettangoli
title_container = tk.Frame(header_frame, bg="#2b2b2b")
title_container.pack(side='top', pady=5)

# Titolo
title_label = tk.Label(
    title_container,
    text="SENSOR PLOT DATA",
    font=("Helvetica", 20, "bold"),
    bg="#2b2b2b",
    fg="white"
)
title_label.pack(side='left', padx=(0, 20))  # Spazio tra titolo e rettangoli

# Canvas per rettangoli colorati accanto al titolo
legend_canvas = tk.Canvas(
    title_container,
    width=100,
    height=30,
    bg="#2b2b2b",
    highlightthickness=0
)
legend_canvas.pack(side='left')

# Colori Matplotlib mappati per Tkinter
legend_colors = ['green', 'blue', 'red', 'orange', 'purple']
for i, color in enumerate(legend_colors):
    x0 = i * 18 + 2
    legend_canvas.create_rectangle(x0, 8, x0 + 15, 25, fill=color, outline='')

canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.configure(bg="#2b2b2b")  # colore background del widget
canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

scroll_slider = ttk.Scale(root, from_=0, to=0, orient='horizontal',
                          command=lambda val: update_plot_from_slider(int(float(val))))
scroll_slider.pack(fill='x', padx=10, pady=5)

controls = tk.Frame(root, bg="#2b2b2b")

controls.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

port_entry   = create_labeled_entry("Port", "COM3",     0, 0)
baud_entry   = create_labeled_entry("Baud",  115200,     0, 2)
points_entry = create_labeled_entry("Number of point", 200,        0, 4)

# === Pulsanti principali ===
connect_button = ttk.Button(controls, text="Connect", command=toggle_connection)
connect_button.grid(row=0, column=6, padx=5)
ttk.Label(controls, text="").grid(row=0, column=8, padx=100)  # spazio vuoto
ttk.Button(controls, text="Record", command=start_recording).grid(row=0, column=9, padx=5)
ttk.Button(controls, text="Stop", command=stop_recording).grid(row=0, column=10, padx=5)
ttk.Button(controls, text="Open CSV", command=load_csv_file).grid(row=0, column=11, padx=5)

bold_font = tkfont.Font(weight="bold")
ttk.Label(controls, text="Y-Axis Config:", font=bold_font).grid(row=1, column=0, columnspan=3, pady=10)


for i in range(5):
    row = i + 2
    label_entry = create_labeled_entry(f"Name {labels[i]}", labels[i], row, 0)
    scale_entry = create_labeled_entry("min,max", "0,100", row, 2)
    unit_entry  = create_labeled_entry("Unit:", "U", row, 4)
    label_entries.append(label_entry)
    scale_entries.append(scale_entry)
    unit_entries.append(unit_entry)

save_button = ttk.Button(controls, text="Save Config", command=save_config)
save_button.grid(row=7, column=0, columnspan=6, pady=10)


load_config()
ani = animation.FuncAnimation(fig, animate, interval=50)
root.mainloop()
