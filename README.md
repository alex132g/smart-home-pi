# Smart Home on a Raspberry Pi

A Raspberry Pi reads room sensors, turns the light on when someone is in the room, and shows everything on a web dashboard. It all runs inside a Docker container.

**Status: prototype (about 2 hours of work).** The software runs in mock mode (fake sensor values). It has not been tested on real hardware yet.

## What it does

| Function | Sensor / part | How it works |
|---|---|---|
| Temperature + humidity | DHT22 | Read every 2 s, shown on the dashboard |
| CO₂ (air quality) | MH-Z19B | Read over UART. Above 1000 ppm the dashboard says "open a window" |
| Presence ("location") | PIR motion sensor HC-SR501 | Motion detected = someone is in the room |
| Light | LED, or a relay module for a real lamp | ON when there is motion, OFF after 30 s with no motion |

## Architecture

```
 Sensors ──GPIO/UART──> Raspberry Pi
                         └─ Docker container "smarthome"
                              ├─ main.py      loop: read sensors -> decide light -> save state
                              ├─ sensors.py   drivers (real Pi or MOCK)
                              └─ web server :8000 -> dashboard.html + /api/state (JSON)
 Phone/PC browser ──WiFi──> http://<pi-ip>:8000
```

## Wiring (BCM pin numbers)

| Part | Pi pin |
|---|---|
| DHT22 data | GPIO4 (pin 7), 10 kΩ pull-up to 3.3 V |
| MH-Z19B TX → Pi RX | GPIO15 (pin 10) |
| MH-Z19B RX → Pi TX | GPIO14 (pin 8) |
| MH-Z19B Vin | 5 V (pin 2) |
| PIR OUT | GPIO17 (pin 11), PIR powered from 5 V |
| LED / relay IN | GPIO27 (pin 13), LED needs a 330 Ω resistor |
| All GND | GND (pin 6, 9, 14...) |

Enable the UART on the Pi first: `sudo raspi-config` → Interface Options → Serial Port → login shell **No**, hardware **Yes**.

## Run it

**On a laptop without hardware (demo):**
```
cd app
MOCK=1 python3 main.py          # open http://localhost:8000
python3 test_logic.py           # run the tests
```

**On the Raspberry Pi:**
```
docker compose up -d --build    # open http://<pi-ip>:8000
```

Settings in `docker-compose.yml`: `LIGHT_TIMEOUT` (seconds), `CO2_LIMIT` (ppm). If port 8000 is already taken on your laptop, run with `PORT=8090`.

## Shopping list (about 350 kr)

- Raspberry Pi 4 or 5 + power supply + SD card
- DHT22 temperature/humidity sensor
- MH-Z19B CO₂ sensor
- HC-SR501 PIR motion sensor
- LED + 330 Ω resistor (later: 5 V relay module)
- Breadboard + jumper wires

## Next steps

- [ ] Wire up the sensors and test on the real Pi
- [ ] Check the CO₂ sensor values against outside air (about 420 ppm)
- [ ] Save readings to a database (SQLite or InfluxDB) and show graphs
- [ ] Only turn the light on when it is dark (add a light sensor)
- [ ] Several rooms: one PIR per room gives "which room is the person in"
- [ ] Use a relay to switch a real lamp (careful: 230 V, get a teacher to check it)
