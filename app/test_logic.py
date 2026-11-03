from main import LIGHT_TIMEOUT, light_should_be_on
from sensors import mhz19_checksum, parse_mhz19

# light stays on during timeout, turns off after
assert light_should_be_on(True, 0, 1000)
assert light_should_be_on(False, 1000, 1000 + LIGHT_TIMEOUT - 1)
assert not light_should_be_on(False, 1000, 1000 + LIGHT_TIMEOUT + 1)

# MH-Z19: 0x02 0x58 = 600 ppm
resp = bytearray([0xFF, 0x86, 0x02, 0x58, 0, 0, 0, 0, 0])
resp[8] = mhz19_checksum(resp)
assert parse_mhz19(bytes(resp)) == 600
resp[8] ^= 1
assert parse_mhz19(bytes(resp)) is None  # bad checksum rejected
assert parse_mhz19(b"") is None  # timeout rejected
# the read command from the datasheet must have checksum 0x79
assert mhz19_checksum(bytes([0xFF, 0x01, 0x86, 0, 0, 0, 0, 0, 0])) == 0x79
print("all tests passed")
