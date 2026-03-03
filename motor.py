import smbus
import time

# --- Configuration ---
# Change this to your HAT's I2C address found via i2cdetect
I2C_ADDR = 0x60 
bus = smbus.SMBus(1)

# PCA9685 Registers
MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06 # Base register for channels

# --- Motor Pin Mapping (Based on Adafruit/Waveshare HATs) ---
# Motors 1-4. Each motor uses 3 channels: PWM, DIR1, DIR2
# M1: PWM=8,  IN1=9,  IN2=10
# M2: PWM=13, IN1=12, IN2=11
# M3: PWM=2,  IN1=3,  IN2=4
# M4: PWM=7,  IN1=6,  IN2=5
MOTORS = {
    'M1': {'pwm': 8,  'dir1': 9,  'dir2': 10},
    'M2': {'pwm': 13, 'dir1': 12, 'dir2': 11},
    'M3': {'pwm': 2,  'dir1': 3,  'dir2': 4},
    'M4': {'pwm': 7,  'dir1': 6,  'dir2': 5},
}

# --- I2C & PCA9685 Functions ---
def write_reg(reg, val):
    bus.write_byte_data(I2C_ADDR, reg, val)

def set_pwm(channel, on, off):
    base = LED0_ON_L + 4 * channel
    write_reg(base, on & 0xFF)
    write_reg(base + 1, on >> 8)
    write_reg(base + 2, off & 0xFF)
    write_reg(base + 3, off >> 8)

def init_hat():
    # Wake up PCA9685
    write_reg(MODE1, 0x00)
    # Set Frequency to 1600Hz (typical for DC motors)
    # 50Hz for servos, ~1000-1600Hz for DC
    prescale = int(25000000.0 / (4096.0 * 1600.0) - 0.5)
    old_mode = bus.read_byte_data(I2C_ADDR, MODE1)
    new_mode = (old_mode & 0x7F) | 0x10
    write_reg(MODE1, new_mode)
    write_reg(PRESCALE, prescale)
    write_reg(MODE1, old_mode)
    time.sleep(0.005)
    write_reg(MODE1, old_mode | 0xA0)

def set_motor(motor_id, speed):
    """Speed: -255 to 255"""
    motor = MOTORS[motor_id]
    
    # Set direction
    if speed > 0: # Forward
        set_pwm(motor['dir1'], 4096, 0)
        set_pwm(motor['dir2'], 0, 0)
    elif speed < 0: # Backward
        set_pwm(motor['dir1'], 0, 0)
        set_pwm(motor['dir2'], 4096, 0)
    else: # Stop
        set_pwm(motor['dir1'], 0, 0)
        set_pwm(motor['dir2'], 0, 0)
    
    # Set speed (0-4095)
    duty = min(abs(speed) * 16, 4095)
    set_pwm(motor['pwm'], 0, duty)

def move(m1, m2, m3, m4):
    """Sets speed for all 4 motors. Positive=Forward, Negative=Backward"""
    set_motor('M1', m1)
    set_motor('M2', m2)
    set_motor('M3', m3)
    set_motor('M4', m4)

def stop():
    move(0, 0, 0, 0)

# --- Main Execution ---
try:
    init_hat()
    print("Moving Forward...")
    move(200, 200, 200, 200) # Speed 200
    time.sleep(2)
    
    print("Moving Backward...")
    move(-200, -200, -200, -200)
    time.sleep(2)
    
    print("Turning Right...")
    move(200, -200, 200, -200)
    time.sleep(2)
    
    print("Turning Left...")
    move(-200, 200, -200, 200)
    time.sleep(2)
    
    stop()
    print("Stopped.")

except KeyboardInterrupt:
    stop()
