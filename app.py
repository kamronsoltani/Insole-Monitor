import json
import threading
import time
from pathlib import Path

import serial
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
import uvicorn

PORT = "COM4"
BAUD = 115200

PRESSURE_MAX = 20000.0

BASE_DIR = Path(__file__).parent
WEB_DIR = BASE_DIR / "web"

app = FastAPI()

latest = {
    "heel": 0,
    "big_toe": 0,
    "side_toe": 0,
    "heel_pct": 0,
    "big_toe_pct": 0,
    "side_toe_pct": 0,
    "total_pct": 0,
    "ax": 0,
    "ay": 0,
    "az": 0,
    "gx": 0,
    "gy": 0,
    "gz": 0,
    "temp": 0
}

body_weight_kg = 100
overall_limit_pct = 30

cols = ["p1","p2","p3","p4","p5","p6","p7","ax","ay","az","gx","gy","gz","temp"]

def to_pct(raw):
    return max(0.0, min(100.0, raw / PRESSURE_MAX * 100.0))

def serial_worker():
    global latest

    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=0.03)

            while True:
                line = ser.readline().decode(errors="ignore").strip()

                if not line:
                    continue

                vals = line.split(",")

                if len(vals) != 14:
                    continue

                try:
                    nums = [float(v) for v in vals]
                except ValueError:
                    continue

                data = dict(zip(cols, nums))

                # corrected frontend-only mapping
                big_toe_raw = max(0, data["p5"])
                side_toe_raw = max(0, data["p6"])

                ball_l_raw = max(0, data["p4"])
                ball_r_raw = max(0, data["p7"])

                heel_l_raw = max(0, data["p3"])
                heel_c_raw = max(0, data["p2"])
                heel_r_raw = max(0, data["p1"])

                heel_raw = heel_l_raw + heel_c_raw + heel_r_raw

                big_pct = to_pct(big_toe_raw)
                side_pct = to_pct(side_toe_raw)
                ball_l_pct = to_pct(ball_l_raw)
                ball_r_pct = to_pct(ball_r_raw)
                heel_l_pct = to_pct(heel_l_raw)
                heel_c_pct = to_pct(heel_c_raw)
                heel_r_pct = to_pct(heel_r_raw)
                heel_pct = min(100.0, heel_l_pct + heel_c_pct + heel_r_pct)

                total_pct = min(100.0, big_pct + side_pct + ball_l_pct + ball_r_pct + heel_pct)

                latest = {
                    "heel": heel_raw,
                    "big_toe": big_toe_raw,
                    "side_toe": side_toe_raw,
                    "ball_l": ball_l_raw,
                    "ball_r": ball_r_raw,
                    "heel_l": heel_l_raw,
                    "heel_c": heel_c_raw,
                    "heel_r": heel_r_raw,

                    "heel_pct": heel_pct,
                    "big_toe_pct": big_pct,
                    "side_toe_pct": side_pct,
                    "ball_l_pct": ball_l_pct,
                    "ball_r_pct": ball_r_pct,
                    "heel_l_pct": heel_l_pct,
                    "heel_c_pct": heel_c_pct,
                    "heel_r_pct": heel_r_pct,
                    "total_pct": total_pct,

                    "ax": data["ax"],
                    "ay": data["ay"],
                    "az": data["az"],
                    "gx": data["gx"],
                    "gy": data["gy"],
                    "gz": data["gz"],
                    "temp": data["temp"]
                }

        except Exception:
            time.sleep(1)

@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")

@app.get("/data")
def get_data():
    return JSONResponse(latest)

@app.post("/settings")
async def settings(request: Request):
    global body_weight_kg, overall_limit_pct

    try:
        cfg = await request.json()

        if "body_weight_kg" in cfg:
            body_weight_kg = float(cfg["body_weight_kg"])

        if "overall_limit_pct" in cfg:
            overall_limit_pct = float(cfg["overall_limit_pct"])

    except Exception:
        pass

    return {"ok": True}

if __name__ == "__main__":
    t = threading.Thread(target=serial_worker, daemon=True)
    t.start()
    uvicorn.run(app, host="127.0.0.1", port=8000)