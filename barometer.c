#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c-dev.h>
#include <math.h>
#include <byteswap.h>
#include <i2c/smbus.h>

#define I2C_ADDR 0x77
#define I2C_DEV "/dev/i2c-1"
#define BMP180_OVERSAMPLING_SETTING 3 // 3 for Ultra High Resolution

// Calibration coefficients
short ac1, ac2, ac3, b1, b2, mb, mc, md;
unsigned short ac4, ac5, ac6;
long b5;
int fd;

// Helper function to read a 16-bit signed integer from a register
short i2c_read_short(int file, unsigned char addr) {
    __s32 res = i2c_smbus_read_word_data(file, addr);
    if (res < 0) {
        perror("I2C read error");
        exit(1);
    }
    // Convert little-endian to big-endian
    return (short)bswap_16(res);
}

// Function to read an unsigned 16-bit integer
unsigned short i2c_read_unsigned_short(int file, unsigned char addr) {
    __s32 res = i2c_smbus_read_word_data(file, addr);
    if (res < 0) {
        perror("I2C read error");
        exit(1);
    }
    return (unsigned short)bswap_16(res);
}

// Function to write a byte to a register
void i2c_write_byte(int file, unsigned char addr, unsigned char value) {
    if (i2c_smbus_write_byte_data(file, addr, value) < 0) {
        perror("I2C write error");
        exit(1);
    }
}

// Open I2C device
void open_i2c() {
    if ((fd = open(I2C_DEV, O_RDWR)) < 0) {
        perror("Failed to open I2C bus");
        exit(1);
    }
    if (ioctl(fd, I2C_SLAVE, I2C_ADDR) < 0) {
        perror("Failed to acquire bus access");
        exit(1);
    }
}

// Read calibration data from EEPROM
void read_calibration() {
    ac1 = i2c_read_short(fd, 0xAA);
    ac2 = i2c_read_short(fd, 0xAC);
    ac3 = i2c_read_short(fd, 0xAE);
    ac4 = i2c_read_unsigned_short(fd, 0xB0);
    ac5 = i2c_read_unsigned_short(fd, 0xB2);
    ac6 = i2c_read_unsigned_short(fd, 0xB4);
    b1 = i2c_read_short(fd, 0xB6);
    b2 = i2c_read_short(fd, 0xB8);
    mb = i2c_read_short(fd, 0xBA);
    mc = i2c_read_short(fd, 0xBC);
    md = i2c_read_short(fd, 0xBE);
}

// Read uncompensated temperature
long read_raw_temp() {
    i2c_write_byte(fd, 0xF4, 0x2E);
    usleep(5000); // Wait for 4.5ms conversion time
    return (long)i2c_read_short(fd, 0xF6);
}

// Read uncompensated pressure
long read_raw_pressure() {
    unsigned char cmd = 0x34 + (BMP180_OVERSAMPLING_SETTING << 6);
    i2c_write_byte(fd, 0xF4, cmd);
    usleep(2 + (3000 << BMP180_OVERSAMPLING_SETTING)); // Wait for conversion time

    unsigned char data[3];
    // Read 3 bytes from 0xF6
    if (read(fd, data, 3) != 3) {
        perror("I2C read block error");
        exit(1);
    }
    long up = ((long)data[0] << 16 | (long)data[1] << 8 | (long)data[2]) >> (8 - BMP180_OVERSAMPLING_SETTING);
    return up;
}

// Calculate true temperature in C
float calculate_temperature(long ut) {
    long x1 = ((ut - ac6) * ac5) >> 15;
    long x2 = (mc << 11) / (x1 + md);
    b5 = x1 + x2;
    float t = ((b5 + 8) >> 4) / 10.0;
    return t;
}

// Calculate true pressure in Pa
long calculate_pressure(long up) {
    long b6 = b5 - 4000;
    long x1 = (b2 * ((b6 * b6) >> 12)) >> 11;
    long x2 = (ac2 * b6) >> 11;
    long x3 = x1 + x2;
    long b3 = (((ac1 * 4 + x3) << BMP180_OVERSAMPLING_SETTING) + 2) >> 2;
    x1 = (ac3 * b6) >> 13;
    x2 = (b1 * ((b6 * b6) >> 12)) >> 16;
    x3 = ((x1 + x2) + 2) >> 2;
    unsigned long b4 = (ac4 * (unsigned long)(x3 + 32768)) >> 15;
    unsigned long b7 = ((unsigned long)up - b3) * (50000 >> BMP180_OVERSAMPLING_SETTING);
    long p;
    if (b7 < 0x80000000) {
        p = (b7 * 2) / b4;
    } else {
        p = (b7 / b4) * 2;
    }
    x1 = (p >> 8) * (p >> 8);
    x1 = (x1 * 3038) >> 16;
    x2 = (-7357 * p) >> 16;
    p = p + ((x1 + x2 + 3791) >> 4);
    return p;
}

// Calculate altitude in meters (uses standard sea level pressure 101325 Pa)
float calculate_altitude(long pressure) {
    float altitude;
    float sea_level_pa = 101325.0; // Standard atmosphere pressure
    altitude = 44330.0 * (1.0 - pow(pressure / sea_level_pa, (1.0/5.255)));
    return altitude;
}

int main() {
    printf("BMP180 Sensor Reading\n");
    open_i2c();
    read_calibration();

    while(1) {
        long ut = read_raw_temp();
        float temp = calculate_temperature(ut);
        long up = read_raw_pressure();
        long pressure = calculate_pressure(up);
        float altitude = calculate_altitude(pressure);

        printf("\nTemperature: %.2f C\n", temp);
        printf("Pressure: %lu Pa (%.2f hPa)\n", pressure, pressure / 100.0);
        printf("Altitude: %.2f m\n", altitude);
        
        sleep(2); // Read every 2 seconds
    }

    close(fd);
    return 0;
}
