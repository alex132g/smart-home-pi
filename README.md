# Smart Home on a Raspberry Pi

A Raspberry Pi reads room sensors, turns the light on when someone is in the room, and shows everything on a web dashboard. It all runs inside a Docker container.

**Status: prototype (about 2 hours of work).** The software runs in mock mode (fake sensor values). It has not been tested on real hardware yet.

## What it does

| Function | Sensor / part | How it works |
|---|---|---|
| Temperature, humidity, pressure | Enviro+ HAT (BME280) | Read every 2 s. Temperature is corrected for heat from the Pi's CPU |
| Gases (CO, NO₂, NH₃) | Enviro+ HAT (MICS6814) | Shown as sensor resistance. Lower value = more gas |
| Particles PM2.5 (optional) | PMS5003, plugs into the Enviro+ | Above 25 µg/m³ the dashboard says "open a window" |
| Presence ("location") | PIR motion sensor HC-SR501 | Motion detected = someone is in the room |
| Light level | Enviro+ HAT (LTR559) | Brightness in the room in lux, shown on the dashboard |
| Lamp | LED, or a relay module for a real lamp | ON when there is motion, OFF after 30 s with no motion |

## Architecture

```
 Enviro+ HAT ──I2C/UART──> Raspberry Pi <──GPIO── PIR + LED
                         └─ Docker container "smarthome"
                              ├─ main.py      loop: read sensors -> decide light -> save state
                              ├─ sensors.py   drivers (real Pi or MOCK)
                              └─ web server :8000 -> dashboard.html + /api/state (JSON)
 Phone/PC browser ──WiFi──> http://<pi-ip>:8000
```

## Wiring (BCM pin numbers)

The Enviro+ sits on top of the Pi's 40-pin header. It covers all the pins, so use a **stacking header or GPIO extender** to reach the PIR and the LED.

| Part | Pi pin |
|---|---|
| Enviro+ HAT | the whole 40-pin header (uses I2C, UART, GPIO22/24/27 and others) |
| PMS5003 (optional) | the cable connector on the Enviro+ |
| PIR OUT | GPIO17 (pin 11), PIR powered from 5 V |
| LED / relay IN | GPIO26 (pin 37), LED needs a 330 Ω resistor. **Not GPIO27**, the PMS5003 uses it |
| All GND | GND (pin 6, 9, 14...) |

Set up the Pi first:
1. `sudo raspi-config` → Interface Options → **I2C: Yes**.
2. Only with a PMS5003: Serial Port → login shell **No**, hardware **Yes**, set `PMS5003=1` and uncomment `/dev/serial0` in `docker-compose.yml`. On a Pi 4 or older, also add `dtoverlay=pi3-miniuart-bt` to `/boot/firmware/config.txt` (frees the good UART from Bluetooth).
3. `sudo reboot`

## Run it

**On a laptop without hardware (demo):**
```
cd app
MOCK=1 python3 main.py          # open http://localhost:8000
python3 test_logic.py           # run the tests
```

**On the Raspberry Pi:**
```
curl -fsSL https://get.docker.com | sh    # install Docker (only once)
git clone https://github.com/alex132g/smart-home-pi.git
cd smart-home-pi
sudo docker compose up -d --build    # open http://<pi-ip>:8000
```

Settings in `docker-compose.yml`: `PMS5003` (1 if you have it), `TEMP_FACTOR` (raise it if the temperature reads too low, lower it if too high), `LIGHT_TIMEOUT` (seconds), `PM25_LIMIT` (µg/m³). If port 8000 is already taken on your laptop, run with `PORT=8090`.

## Shopping list

- Raspberry Pi 4 or 5 + power supply + SD card
- Pimoroni Enviro+ HAT
- PMS5003 particulate sensor (optional)
- 2x20 stacking header or GPIO extender
- HC-SR501 PIR motion sensor
- LED + 330 Ω resistor (later: 5 V relay module)
- Breadboard + jumper wires

## Next steps

- [ ] Mount the Enviro+, wire up the PIR and LED and test on the real Pi
- [ ] Calibrate `TEMP_FACTOR` against a normal thermometer
- [ ] Show the readings on the Enviro+ LCD screen
- [ ] Save readings to a database (SQLite or InfluxDB) and show graphs
- [ ] Only turn the light on when it is dark (the Enviro+ already has a light sensor, LTR559)
- [ ] Several rooms: one PIR per room gives "which room is the person in"
- [ ] Use a relay to switch a real lamp (careful: 230 V, get a teacher to check it)
