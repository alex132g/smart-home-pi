from main import LIGHT_TIMEOUT, light_should_be_on
from sensors import TEMP_FACTOR, compensate_temperature

# light stays on during timeout, turns off after
assert light_should_be_on(True, 0, 1000)
assert light_should_be_on(False, 1000, 1000 + LIGHT_TIMEOUT - 1)
assert not light_should_be_on(False, 1000, 1000 + LIGHT_TIMEOUT + 1)

# hot CPU pulls the reading down; same temp as CPU means no correction
assert compensate_temperature(30.0, 30.0 + TEMP_FACTOR * 5) == 25.0
assert compensate_temperature(22.0, 22.0) == 22.0
print("all tests passed")
