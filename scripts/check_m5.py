from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech import FeetechMotorsBus

motors = {f"m{i}": Motor(i, "sts3215", MotorNormMode.RANGE_M100_100) for i in range(1, 7)}
bus = FeetechMotorsBus(port="COM4", motors=motors)
bus.connect()
bus.disable_torque()

for reg in ["Operating_Mode", "Phase", "Min_Position_Limit", "Max_Position_Limit"]:
    print(f"{reg:20}", bus.sync_read(reg, normalize=False))

# Sett motor 5 i vanlig posisjonsmodus med samme innstillinger som motor 4
bus.write("Operating_Mode", "m5", 0, normalize=False)
bus.write("Min_Position_Limit", "m5", 0, normalize=False)
bus.write("Max_Position_Limit", "m5", 4095, normalize=False)

print("Etter fiks:")
print("Operating_Mode     ", bus.sync_read("Operating_Mode", normalize=False))
bus.disconnect()