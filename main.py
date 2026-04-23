from machine import I2C, Pin, PWM
import time
import math

# Servo settings
NEUTRAL_ANGLE = 90
ACTIVE_ANGLE = 180
ACTIVE_DURATION = 2.0

servo = PWM(Pin(20), freq=50)

# Accelerometer settings
ACCELERATION_THRESHOLD = 0.06
N_ACCELERATION_RESULTS = 5

accelerometer = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
MPU_ADDRESS = 0x68
accelerometer.writeto_mem(MPU_ADDRESS, 0x6B, b'\x00')

acceleration_results = []

def set_servo_angle(angle):
    min_duty = 1638
    max_duty = 8192

    duty = int(min_duty + (angle / 180) * (max_duty - min_duty))
    servo.duty_u16(duty)

def read_accelerometer_value(address):
    data = accelerometer.readfrom_mem(MPU_ADDRESS, address, 2)
    value = (data[0] << 8) | data[1]
    
    if value > 32767:
        value -= 65536
    return value / 16384

def record_acceleration_result():
    ax = read_accelerometer_value(0x3B) 
    ay = read_accelerometer_value(0x3D)
    az = read_accelerometer_value(0x3F)
    
    l = math.sqrt(ax**2 + ay**2 + az**2)
    l = max(l - 1.03, 0.0) # account for gravity
    acceleration_results.append(l)
    
    if len(acceleration_results) > N_ACCELERATION_RESULTS:
        acceleration_results.pop(0)

def clear_acceleration_results():
    acceleration_results.clear()
    for _ in range(N_ACCELERATION_RESULTS):
        acceleration_results.append(0.0)

def get_mean_acceleration():
    r = 0.0
    for l in acceleration_results:
        r += l
    return r / len(acceleration_results)

clear_acceleration_results()
set_servo_angle(NEUTRAL_ANGLE)
    
while True:
    record_acceleration_result()
    
    l = get_mean_acceleration()
    print(l)
    
    if l > ACCELERATION_THRESHOLD:
        print("Keys! (Magnitude: {:.2f})".format(l))
        clear_acceleration_results()
        
        set_servo_angle(ACTIVE_ANGLE)
        time.sleep(ACTIVE_DURATION)
        
        set_servo_angle(NEUTRAL_ANGLE)
    else:
        time.sleep(0.05)
