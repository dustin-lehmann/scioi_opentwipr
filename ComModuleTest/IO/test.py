import cobs.cobs as cobs


buffer = b"\x01\x00\x02\x03\x04\x05\x00"

x = cobs.encode(buffer)
y = cobs.decode(x)

print("stop")