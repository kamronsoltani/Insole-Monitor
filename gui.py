# import serial
# import tkinter as tk

# PORT = "COM4"
# BAUD = 115200

# labels = [
#     "p1","p2","p3","p4","p5","p6","p7",
#     "ax","ay","az","gx","gy","gz","temp"
# ]

# ser = serial.Serial(PORT, BAUD, timeout=0.01)

# root = tk.Tk()
# root.title("Insole Monitor")
# root.geometry("520x520")

# title = tk.Label(root, text="Insole Monitor Raw Values", font=("Arial", 22, "bold"))
# title.pack(pady=15)

# frame = tk.Frame(root)
# frame.pack(padx=20, pady=10, fill="both", expand=True)

# value_labels = {}

# for i, name in enumerate(labels):
#     row = tk.Frame(frame)
#     row.pack(fill="x", pady=4)

#     left = tk.Label(row, text=name, font=("Arial", 16), width=8, anchor="w")
#     left.pack(side="left")

#     val = tk.Label(row, text="---", font=("Consolas", 18, "bold"), anchor="e")
#     val.pack(side="right", fill="x", expand=True)

#     value_labels[name] = val

# status = tk.Label(root, text="Reading COM4", font=("Arial", 10))
# status.pack(pady=8)

# def update_values():
#     try:
#         while ser.in_waiting:
#             line = ser.readline().decode(errors="ignore").strip()
#             vals = line.split(",")

#             if len(vals) == 14:
#                 for name, value in zip(labels, vals):
#                     value_labels[name].config(text=value)

#     except Exception as e:
#         status.config(text=f"Error: {e}")

#     root.after(10, update_values)

# def on_close():
#     try:
#         ser.close()
#     except:
#         pass
#     root.destroy()

# root.protocol("WM_DELETE_WINDOW", on_close)
# update_values()
# root.mainloop()


import math
import serial
import tkinter as tk
from tkinter import ttk

PORT = "COM4"
BAUD = 115200

PRESSURE_MAX = 20000
UPDATE_MS = 20

sensor_names = [
    "Big Toe", "Side Toe", "Ball Left", "Ball Right",
    "Heel Left", "Heel Center", "Heel Right"
]

serial_cols = [
    "p1","p2","p3","p4","p5","p6","p7",
    "ax","ay","az","gx","gy","gz","temp"
]

# rough sensor locations on the foot canvas
sensor_xy = {
    "Big Toe": (150, 70),
    "Side Toe": (95, 95),
    "Ball Left": (130, 170),
    "Ball Right": (190, 175),
    "Heel Left": (125, 360),
    "Heel Center": (160, 380),
    "Heel Right": (195, 360),
}

root = tk.Tk()
root.title("Insole Pressure Monitor")
root.geometry("1120x720")
root.configure(bg="#eef5fb")

style = ttk.Style()
style.theme_use("clam")

ser = serial.Serial(PORT, BAUD, timeout=0.005)

latest = {name: 0 for name in sensor_names}
raw_latest = {col: "0" for col in serial_cols}

# ---------- layout ----------

header = tk.Frame(root, bg="#eef5fb")
header.pack(fill="x", pady=(18, 8))

tk.Label(
    header,
    text="UC BERKELEY MECHANICAL ENGINEERING",
    bg="#eef5fb",
    fg="#6b7685",
    font=("Segoe UI", 10, "bold")
).pack()

tk.Label(
    header,
    text="Insole Pressure Monitor",
    bg="#eef5fb",
    fg="#1f2937",
    font=("Segoe UI", 30, "bold")
).pack()

tk.Label(
    header,
    text="ME 292C Group 11 | Pressure Sensor Insole",
    bg="#eef5fb",
    fg="#6b7685",
    font=("Segoe UI", 12, "bold")
).pack()

main = tk.Frame(root, bg="#eef5fb")
main.pack(fill="both", expand=True, padx=35, pady=20)

left_card = tk.Frame(main, bg="#f8fbff", highlightthickness=1, highlightbackground="#ffffff")
left_card.pack(side="left", fill="both", expand=True, padx=(0, 18))

right_card = tk.Frame(main, bg="#f8fbff", highlightthickness=1, highlightbackground="#ffffff")
right_card.pack(side="right", fill="both", expand=True, padx=(18, 0))

tk.Label(
    left_card,
    text="Live Foot Pressure Map",
    bg="#f8fbff",
    fg="#1f2937",
    font=("Segoe UI", 17, "bold")
).pack(anchor="w", padx=24, pady=(22, 8))

canvas = tk.Canvas(left_card, width=430, height=520, bg="#f8fbff", highlightthickness=0)
canvas.pack(padx=20, pady=10)

tk.Label(
    right_card,
    text="Raw Sensor Data",
    bg="#f8fbff",
    fg="#1f2937",
    font=("Segoe UI", 17, "bold")
).pack(anchor="w", padx=24, pady=(22, 8))

raw_frame = tk.Frame(right_card, bg="#f8fbff")
raw_frame.pack(fill="both", expand=True, padx=24, pady=10)

value_labels = {}
bar_canvases = {}

for i, name in enumerate(sensor_names):
    row = tk.Frame(raw_frame, bg="#f8fbff")
    row.pack(fill="x", pady=8)

    tk.Label(
        row,
        text=name,
        bg="#f8fbff",
        fg="#4b5563",
        font=("Segoe UI", 12, "bold"),
        width=12,
        anchor="w"
    ).pack(side="left")

    val = tk.Label(
        row,
        text="0",
        bg="#f8fbff",
        fg="#111827",
        font=("Consolas", 16, "bold"),
        width=8,
        anchor="e"
    )
    val.pack(side="left", padx=(8, 18))
    value_labels[name] = val

    bar = tk.Canvas(row, width=230, height=18, bg="#f8fbff", highlightthickness=0)
    bar.pack(side="left", fill="x", expand=True)
    bar_canvases[name] = bar

imu_title = tk.Label(
    right_card,
    text="IMU / Temperature",
    bg="#f8fbff",
    fg="#1f2937",
    font=("Segoe UI", 15, "bold")
)
imu_title.pack(anchor="w", padx=24, pady=(12, 4))

imu_frame = tk.Frame(right_card, bg="#f8fbff")
imu_frame.pack(fill="x", padx=24, pady=(0, 12))

imu_labels = {}
for col in ["ax", "ay", "az", "gx", "gy", "gz", "temp"]:
    box = tk.Frame(imu_frame, bg="#ffffff", highlightthickness=1, highlightbackground="#e5edf6")
    box.pack(side="left", padx=4, pady=6, ipadx=8, ipady=8)

    tk.Label(
        box,
        text=col,
        bg="#ffffff",
        fg="#6b7280",
        font=("Segoe UI", 9, "bold")
    ).pack()

    lab = tk.Label(
        box,
        text="0",
        bg="#ffffff",
        fg="#111827",
        font=("Consolas", 10, "bold"),
        width=8
    )
    lab.pack()
    imu_labels[col] = lab

status = tk.Label(
    right_card,
    text=f"Live Monitoring Active | {PORT}",
    bg="#f8fbff",
    fg="#10b981",
    font=("Segoe UI", 11, "bold")
)
status.pack(anchor="w", padx=24, pady=(0, 18))


# ---------- drawing ----------

def pressure_color(percent):
    # soft apple-health-ish blue to red
    if percent < 35:
        return "#5aa9f8"
    if percent < 70:
        return "#54d6a7"
    return "#f26b7a"


def draw_round_rect(c, x1, y1, x2, y2, r, fill, outline=""):
    points = [
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
        x2, y2-r, x2, y2, x2-r, y2, x1+r, y2,
        x1, y2, x1, y2-r, x1, y1+r, x1, y1
    ]
    return c.create_polygon(points, smooth=True, fill=fill, outline=outline)


def draw_foot():
    canvas.delete("all")

    # soft glass backing
    draw_round_rect(canvas, 40, 20, 390, 500, 35, "#ffffff", "#e8f0f8")

    # foot silhouette
    canvas.create_oval(92, 45, 220, 145, fill="#e4edf8", outline="")
    canvas.create_oval(68, 87, 140, 155, fill="#e4edf8", outline="")
    canvas.create_oval(112, 120, 250, 290, fill="#e4edf8", outline="")
    canvas.create_oval(98, 230, 230, 460, fill="#e4edf8", outline="")

    # inner highlight
    canvas.create_oval(122, 150, 226, 270, outline="#ffffff", width=5)
    canvas.create_oval(118, 290, 215, 435, outline="#ffffff", width=5)

    for name in sensor_names:
        x, y = sensor_xy[name]
        raw = latest[name]
        percent = max(0, min(100, raw / PRESSURE_MAX * 100))

        r = 13 + percent * 0.45
        color = pressure_color(percent)

        canvas.create_oval(
            x-r-7, y-r-7, x+r+7, y+r+7,
            fill=color,
            outline="",
            stipple="gray25"
        )

        canvas.create_oval(
            x-r, y-r, x+r, y+r,
            fill=color,
            outline="#ffffff",
            width=3
        )

        canvas.create_text(
            x, y,
            text=f"{percent:.0f}%",
            fill="#111827",
            font=("Segoe UI", 10, "bold")
        )

        canvas.create_text(
            x, y + r + 18,
            text=name,
            fill="#4b5563",
            font=("Segoe UI", 9, "bold")
        )


def draw_bar(name):
    bar = bar_canvases[name]
    bar.delete("all")

    raw = latest[name]
    percent = max(0, min(100, raw / PRESSURE_MAX * 100))
    width = 230
    fill_w = int(width * percent / 100)
    color = pressure_color(percent)

    draw_round_rect(bar, 0, 2, width, 16, 8, "#e8eef7")
    if fill_w > 4:
        draw_round_rect(bar, 0, 2, fill_w, 16, 8, color)


# ---------- data update ----------

def read_serial():
    global latest

    try:
        last_good = None

        while ser.in_waiting:
            line = ser.readline().decode(errors="ignore").strip()
            vals = line.split(",")

            if len(vals) == 14:
                last_good = vals

        if last_good is not None:
            vals = last_good
            raw_latest.update(dict(zip(serial_cols, vals)))

            nums = [float(v) for v in vals]

            for name, raw in zip(sensor_names, nums[:7]):
                latest[name] = max(0, raw)

            for name in sensor_names:
                value_labels[name].config(text=str(int(latest[name])))
                draw_bar(name)

            for col in ["ax", "ay", "az", "gx", "gy", "gz", "temp"]:
                imu_labels[col].config(text=raw_latest[col])

            draw_foot()

    except Exception as e:
        status.config(text=f"Error: {e}", fg="#ef4444")

    root.after(UPDATE_MS, read_serial)


def on_close():
    try:
        ser.close()
    except Exception:
        pass
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)
draw_foot()
read_serial()
root.mainloop()