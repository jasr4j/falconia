import smbus
import time
import atexit

# I2C address of the PCA9685
PCA9685_ADDRESS = 0x60

# Register addresses
MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06
LED0_ON_H = 0x07
LED0_OFF_L = 0x08
LED0_OFF_H = 0x09
ALL_LED_ON_L = 0xFA
ALL_LED_ON_H = 0xFB
ALL_LED_OFF_L = 0xFC
ALL_LED_OFF_H = 0xFD

# Motor control pins (mapped to PCA9685 channels)
MOTOR_PINS = {
    1: {'PWM': 8, 'IN1': 10, 'IN2': 9},
    2: {'PWM': 13, 'IN1': 11, 'IN2': 12},
    3: {'PWM': 2, 'IN1': 4, 'IN2': 3},
    4: {'PWM': 7, 'IN1': 5, 'IN2': 6}
}

# Directions
FORWARD = 1
BACKWARD = 2
RELEASE = 3

bus = smbus.SMBus(1) # Use i2c bus 1

def set_pwm_freq(freq_hz):
    """Sets the PWM frequency."""
    prescaleval = 25000000.0    # 25MHz
    prescaleval /= 4096.0       # 12-bit
    prescaleval /= float(freq_hz)
    prescaleval -= 1.0
    prescale = int(prescaleval)

    old_mode = bus.read_byte_data(PCA9685_ADDRESS, MODE1)
    new_mode = (old_mode & 0x7F) | 0x10 # sleep
    bus.write_byte_data(PCA9685_ADDRESS, MODE1, new_mode) # go to sleep
    bus.write_byte_data(PCA9685_ADDRESS, PRESCALE, prescale) # set prescale value
    bus.write_byte_data(PCA9685_ADDRESS, MODE1, old_mode)
    time.sleep(0.005)
    bus.write_byte_data(PCA9685_ADDRESS, MODE1, old_mode | 0xa0) # turn on auto increment

def set_pwm(channel, on, off):
    """Sets a single PWM channel."""
    bus.write_byte_data(PCA9685_ADDRESS, LED0_ON_L + 4 * channel, on & 0xFF)
    bus.write_byte_data(PCA9685_ADDRESS, LED0_ON_H + 4 * channel, on >> 8)
    bus.write_byte_data(PCA9685_ADDRESS, LED0_OFF_L + 4 * channel, off & 0xFF)
    bus.write_byte_data(PCA9685_ADDRESS, LED0_OFF_H + 4 * channel, off >> 8)

def set_pin(pin, value):
    """Sets a single pin value (HIGH or LOW) using PWM full-on/off."""
    if value == 0:
        set_pwm(pin, 0, 4096) # Off
    else:
        set_pwm(pin, 4096, 0) # On

def set_motor_speed(motor_num, speed):
    """Sets the speed for a specific motor (0-255)."""
    if 0 <= speed <= 255:
        # Map speed from 0-255 to PWM duty cycle range 0-4095
        pwm_val = int(speed * 4095 / 255)
        set_pwm(MOTOR_PINS[motor_num]['PWM'], 0, pwm_val)

def run_motor(motor_num, direction):
    """Controls the direction of a specific motor."""
    pins = MOTOR_PINS[motor_num]
    if direction == FORWARD:
        set_pin(pins['IN2'], 0)
        set_pin(pins['IN1'], 1)
    elif direction == BACKWARD:
        set_pin(pins['IN1'], 0)
        set_pin(pins['IN2'], 1)
    elif direction == RELEASE:
        set_pin(pins['IN1'], 0)
        set_pin(pins['IN2'], 0)

def stop_all_motors():
    """Stops all four motors immediately."""
    for i in range(1, 5):
        run_motor(i, RELEASE)

# Initialize the HAT and register the stop function for exit
set_pwm_freq(1600) # Default frequency for DC motors is 1.6KHz
atexit.register(stop_all_motors)

# --- Example Usage ---

def move_forward_all(speed):
    """Move all motors forward at a given speed."""
    print(f"All motors forward at speed {speed}")
    for i in range(1, 5):
        set_motor_speed(i, speed)
        run_motor(i, FORWARD)

def move_backward_all(speed):
    """Move all motors backward at a given speed."""
    print(f"All motors backward at speed {speed}")
    for i in range(1, 5):
        set_motor_speed(i, speed)
        run_motor(i, BACKWARD)

def pivot_left(speed):
    """Pivot left by running left motors backward and right motors forward."""
    print(f"Pivoting left at speed {speed}")
    set_motor_speed(1, speed)
    run_motor(1, BACKWARD)
    set_motor_speed(2, speed)
    run_motor(2, BACKWARD)
    set_motor_speed(3, speed)
    run_motor(3, FORWARD)
    set_motor_speed(4, speed)
    run_motor(4, FORWARD)

def pivot_right(speed):
    """Pivot right by running left motors forward and right motors backward."""
    print(f"Pivoting right at speed {speed}")
    set_motor_speed(1, speed)
    run_motor(1, FORWARD)
    set_motor_speed(2, speed)
    run_motor(2, FORWARD)
    set_motor_speed(3, speed)
    run_motor(3, BACKWARD)
    set_motor_speed(4, speed)
    run_motor(4, BACKWARD)

if __name__ == '__main__':
    try:
        move_forward_all(150)
        time.sleep(2)
        stop_all_motors()
        time.sleep(1)

        move_backward_all(100)
        time.sleep(2)
        stop_all_motors()
        time.sleep(1)
        
        pivot_left(200)
        time.sleep(2)
        stop_all_motors()
        time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        stop_all_motors()
