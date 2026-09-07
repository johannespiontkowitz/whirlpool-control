import time
from machine import Pin, ADC
import onewire, ds18x20

from config import WATER_TEMP_SENSOR_PIN, PUMP1_RELAY_PIN, TARGET_TEMP, HEATER_RELAY_PIN, BUBBLES_POTI_PIN
from logic import pump_should_run

# Initialize sensors
ow = onewire.OneWire(Pin(WATER_TEMP_SENSOR_PIN))
ds = ds18x20.DS18X20(ow)
sensors = ds.scan()

# Initialize relays (pumps)
pump1 = Pin(PUMP1_RELAY_PIN, Pin.OUT)
heater = Pin(HEATER_RELAY_PIN, Pin.OUT)
bubbles = ADC(Pin(BUBBLES_POTI_PIN))
bubbles.atten(ADC.ATTN_11DB)  # full 0–3.3 V range

while True:
    ds.convert_temp()
    time.sleep_ms(750)  # DS18B20 needs time to read values
    for sensor in sensors:
        temp = ds.read_temp(sensor)
        print("temp:", temp, "°C")

        bubble_level = bubbles.read()  # 0–4095 -> potential need to normalize

        print("Bubble level: ", bubble_level)

        if pump_should_run(temp, TARGET_TEMP):
            heater.on()
            pump1.on()
            print("Pump 1 running")
            print("Heater on")
        else:
            pump1.off()
            heater.off()
            print("Pump 1 stopped")
            print("Heater off")

    time.sleep(2)