"""Sensor drivers. MOCK=1 gives fake values so the app runs without a Pi."""
import os
import random
import time

MOCK = os.getenv("MOCK", "0") == "1"


def mhz19_checksum(packet: bytes) -> int:
    # MH-Z19 datasheet: 0xFF - sum(bytes 1..7) + 1
    return (0xFF - (sum(packet[1:8]) & 0xFF) + 1) & 0xFF


def parse_mhz19(resp: bytes):
    if len(resp) != 9 or resp[0] != 0xFF or resp[1] != 0x86 or mhz19_checksum(resp) != resp[8]:
        return None
    return resp[2] * 256 + resp[3]


class MockSensors:
    def __init__(self):
        self._motion_until = 0

    def read(self):
        if random.random() < 0.05:  # someone walks by now and then
            self._motion_until = time.time() + 5
        return {
            "temperature": round(21 + random.uniform(-1, 1), 1),
            "humidity": round(45 + random.uniform(-5, 5), 1),
            "co2": random.randint(450, 1300),
            "motion": time.time() < self._motion_until,
        }

    def set_light(self, on: bool):
        pass


class PiSensors:
    """DHT22 on GPIO4, MH-Z19B on UART /dev/serial0, PIR on GPIO17, light relay/LED on GPIO27."""

    def __init__(self):
        import adafruit_dht
        import board
        import serial
        from gpiozero import LED, MotionSensor

        self.dht = adafruit_dht.DHT22(board.D4)
        self.uart = serial.Serial("/dev/serial0", 9600, timeout=1)
        self.pir = MotionSensor(17)
        self.light = LED(27)
        self.last = {"temperature": None, "humidity": None}

    def _co2(self):
        self.uart.reset_input_buffer()
        self.uart.write(bytes([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0x79]))
        return parse_mhz19(self.uart.read(9))

    def read(self):
        try:
            self.last = {"temperature": self.dht.temperature, "humidity": self.dht.humidity}
        except RuntimeError:
            pass  # DHT22 read failures are normal, keep the last good value
        return {**self.last, "co2": self._co2(), "motion": self.pir.motion_detected}

    def set_light(self, on: bool):
        self.light.on() if on else self.light.off()


def get_sensors():
    return MockSensors() if MOCK else PiSensors()
