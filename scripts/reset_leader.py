from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

motors = {f"m{i}": Motor(i, "sts3215", MotorNormMode.RANGE_M100_100) for i in range(1, 7)}
bus = FeetechMotorsBus(port="COM4", motors=motors)
bus.connect()

print("Offset før:  ", bus.sync_read("Homing_Offset", normalize=False))
bus.disable_torque()
for m in motors:
    bus.write("Homing_Offset", m, 0, normalize=False)
print("Offset etter:", bus.sync_read("Homing_Offset", normalize=False))
print("Posisjon:    ", bus.sync_read("Present_Position", normalize=False))
bus.disconnect()
