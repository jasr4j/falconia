import time
import board
import adafruit_dht

# Initialize DHT device, using GPIO 4
dhtDevice = adafruit_dht.DHT22(board.D4) # Use DHT11 if you have that model

while True:
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        print("Temp: {:.1f} C    Humidity: {}% ".format(temperature_c, humidity))

    except RuntimeError as error:
        # Errors happen fairly often, DHT sensors are hard to read
        print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error

    time.sleep(2.0)
