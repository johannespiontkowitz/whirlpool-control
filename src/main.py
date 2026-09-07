import time
from machine import Pin
import onewire, ds18x20

from config import TEMP_SENSOR_PIN, PUMP1_RELAY_PIN, TARGET_TEMP
from logic import pump_should_run

# Initialize sensors
ow = onewire.OneWire(Pin(TEMP_SENSOR_PIN))
ds = ds18x20.DS18X20(ow)
sensors = ds.scan()

# Initialize relays (pumps)
pump1 = Pin(PUMP1_RELAY_PIN, Pin.OUT)

while True:
    ds.convert_temp()
    time.sleep_ms(750)  # DS18B20 needs time to read values
    for sensor in sensors:
        temp = ds.read_temp(sensor)
        print("Temperatur:", temp, "°C")

        if pump_should_run(temp, TARGET_TEMP):
            pump1.on()
            print("Pumpe AN")
        else:
            pump1.off()
            print("Pumpe AUS")

    time.sleep(2)