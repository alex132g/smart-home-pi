"""Smart home loop: read sensors, control the light, serve a dashboard on :8000."""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from sensors import get_sensors

LIGHT_TIMEOUT = int(os.getenv("LIGHT_TIMEOUT", "30"))  # seconds of no motion before light turns off
PM25_LIMIT = int(os.getenv("PM25_LIMIT", "25"))  # µg/m³ (EU yearly limit), above this the room needs fresh air

state = {}
DASHBOARD = (Path(__file__).parent / "dashboard.html").read_bytes()


def light_should_be_on(motion: bool, last_motion: float, now: float) -> bool:
    return motion or now - last_motion < LIGHT_TIMEOUT


def loop():
    sensors = get_sensors()
    last_motion = 0.0
    while True:
        now = time.time()
        reading = sensors.read()
        if reading["motion"]:
            last_motion = now
        light = light_should_be_on(reading["motion"], last_motion, now)
        sensors.set_light(light)
        state.update(reading, light=light, ventilate=(reading["pm25"] or 0) > PM25_LIMIT, time=now)
        time.sleep(2)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            body, ctype = json.dumps(state).encode(), "application/json"
        else:
            body, ctype = DASHBOARD, "text/html"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=loop, daemon=True).start()
    port = int(os.getenv("PORT", "9000"))
    print(f"Dashboard on http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
