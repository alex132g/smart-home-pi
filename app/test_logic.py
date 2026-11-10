import os

import main
from main import LIGHT_TIMEOUT, light_should_be_on
from sensors import GASES, TEMP_FACTOR, compensate_temperature, gas_estimates, gas_ppm

# light stays on during timeout, turns off after
assert light_should_be_on(True, 0, 1000)
assert light_should_be_on(False, 1000, 1000 + LIGHT_TIMEOUT - 1)
assert not light_should_be_on(False, 1000, 1000 + LIGHT_TIMEOUT + 1)

# hot CPU pulls the reading down; same temp as CPU means no correction
assert compensate_temperature(30.0, 30.0 + TEMP_FACTOR * 5) == 25.0
assert compensate_temperature(22.0, 22.0) == 22.0
# at the clean-air baseline each gas gives its curve offset
clean = {key: r0 for key, r0, _, _ in GASES.values()}
assert gas_estimates(clean) == {"co_ppm": 4.37, "no2_ppm": 0.15, "nh3_ppm": 0.69}
# CO and NH3 lower the resistance, NO2 raises it
assert gas_ppm(205, 410, -1.25, 0.64) > gas_ppm(410, 410, -1.25, 0.64)
assert gas_ppm(14.8, 7.4, 1, -0.8129) > gas_ppm(7.4, 7.4, 1, -0.8129)
assert gas_ppm(0, 410, -1.25, 0.64) is None  # bad reading must not crash the loop

# a crash in the sensor loop must end the process so Docker restarts it
exits = []
def crash():
    raise RuntimeError("expected in this test: Gas sensor not connected.")
main.loop, os._exit = crash, exits.append
main.loop_or_exit()
assert exits == [1]
print("all tests passed")
