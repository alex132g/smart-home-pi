"""Sensor drivers. MOCK=1 gives fake values so the app runs without a Pi."""
import os
import random
import time

MOCK = os.getenv("MOCK", "0") == "1"
HAS_PMS5003 = os.getenv("PMS5003", "0") == "1"  # particulate sensor is sold separately from the Enviro+
TEMP_FACTOR = float(os.getenv("TEMP_FACTOR", "2.25"))  # tune by comparing with a room thermometer


def compensate_temperature(raw: float, cpu: float) -> float:
    # The Pi's CPU heats the BME280 on the HAT; Pimoroni's correction from their examples
    return round(raw - (cpu - raw) / TEMP_FACTOR, 1)


class MockSensors:
    def __init__(self):
        self._motion_until = 0

    def read(self):
        if random.random() < 0.05:  # someone walks by now and then
            self._motion_until = time.time() + 5
        return {
            "temperature": round(21 + random.uniform(-1, 1), 1),
            "humidity": round(45 + random.uniform(-5, 5), 1),
            "pressure": round(1013 + random.uniform(-3, 3), 1),
            "pm25": random.randint(2, 40) if HAS_PMS5003 else None,
            "oxidising": round(random.uniform(10, 30), 1),
            "reducing": round(random.uniform(200, 400), 1),
            "nh3": round(random.uniform(50, 150), 1),
            "lux": round(random.uniform(100, 400), 1),
            "motion": time.time() < self._motion_until,
        }

    def set_light(self, on: bool):
        pass


class PiSensors:
    """Pimoroni Enviro+ HAT (BME280, MICS6814 gas, LTR559 light, optional PMS5003), PIR on GPIO17, light on GPIO26."""

    def __init__(self):
        import gpiod
        import gpiodevice
        from bme280 import BME280
        from enviroplus import gas
        from gpiod.line import Direction, Value
        from ltr559 import LTR559
        from smbus2 import SMBus

        self.bme280 = BME280(i2c_dev=SMBus(1))
        self.gas = gas
        self.ltr559 = LTR559()
        self.Value = Value
        self.pir = gpiodevice.get_pin("GPIO17", "smarthome-pir", gpiod.LineSettings(direction=Direction.INPUT))
        # GPIO27 is taken by the PMS5003 reset pin
        self.light = gpiodevice.get_pin("GPIO26", "smarthome-light", gpiod.LineSettings(direction=Direction.OUTPUT))
        self.pms = None
        if HAS_PMS5003:
            from pms5003 import PMS5003
            self.pms = PMS5003(device="/dev/serial0")

    def _cpu_temp(self):
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read()) / 1000

    def _pm25(self):
        if not self.pms:
            return None
        try:
            return self.pms.read().pm_ug_per_m3(2.5)
        except Exception:  # pms5003 raises its own timeout/checksum errors; skip one bad frame
            return None

    def read(self):
        g = self.gas.read_all()  # gas values are resistance in ohms; shown in kΩ
        return {
            "temperature": compensate_temperature(self.bme280.get_temperature(), self._cpu_temp()),
            "humidity": round(self.bme280.get_humidity(), 1),
            "pressure": round(self.bme280.get_pressure(), 1),
            "pm25": self._pm25(),
            "oxidising": round(g.oxidising / 1000, 1),
            "reducing": round(g.reducing / 1000, 1),
            "nh3": round(g.nh3 / 1000, 1),
            "lux": round(self.ltr559.get_lux(), 1),
            "motion": self.pir[0].get_value(self.pir[1]) == self.Value.ACTIVE,
        }

    def set_light(self, on: bool):
        lines, offset = self.light
        lines.set_value(offset, self.Value.ACTIVE if on else self.Value.INACTIVE)


def get_sensors():
    return MockSensors() if MOCK else PiSensors()
