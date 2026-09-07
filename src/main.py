import time
import network
import machine
import ubinascii
from machine import Pin, ADC
import onewire, ds18x20
import umqtt.robust as mqtt

from configs.config import (
    WATER_TEMP_SENSOR_PIN,
    PUMP1_RELAY_PIN,
    HEATER_RELAY_PIN,
    BUBBLES_POTI_PIN,
    COVER_BUTTON_PIN,
)

from configs.network_config import WIFI_SSID, WIFI_PASSWORD
from configs.mqtt_config import MQTT_BROKER, MQTT_CLIENT_ID, MQTT_USER, MQTT_USER_PASSWORD

from controllers.pump_control import pump_should_run
from controllers.bubble_control import control_bubble_level, get_bubble_level_text

# Generate a unique Client ID based on the ESP chip MAC address
UNIQUE_CLIENT_ID = MQTT_CLIENT_ID + "_" + ubinascii.hexlify(machine.unique_id()).decode()

KEEPALIVE = 60
PING_INTERVAL = 15
SENSOR_INTERVAL_MS = 2500

TARGET_TEMP = 30.0
client = None

def on_message(topic, msg):
    global TARGET_TEMP
    topic_str = topic.decode("utf-8")
    
    if topic_str == "whirlpool/target_temp":
        try:
            val_str = msg.decode("utf-8").strip().strip('"').strip("'")
            TARGET_TEMP = float(val_str)
            print("Successfully updated TARGET_TEMP to:", TARGET_TEMP, "°C")
            
            if client:
                client.publish(b"whirlpool/target_temp/state", f"{TARGET_TEMP:.1f}".encode(), retain=True)
        except Exception as e:
            print("Error parsing target temp:", e)

def connect_mqtt():
    c = mqtt.MQTTClient(
        UNIQUE_CLIENT_ID,  # <--- Using unique MAC-based Client ID
        MQTT_BROKER,
        user=MQTT_USER,
        password=MQTT_USER_PASSWORD,
        keepalive=KEEPALIVE,
    )
    c.set_callback(on_message)
    c.connect()
    c.subscribe(b"whirlpool/target_temp")
    
    # Send retained initial states
    c.publish(b"whirlpool/target_temp/state", f"{TARGET_TEMP:.1f}".encode(), retain=True)
    c.publish(b"whirlpool/mode/state", b"heat", retain=True)
    
    print("MQTT connected as ID:", UNIQUE_CLIENT_ID)
    return c

# Network Setup
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

print("Connecting to WLAN...")
timeout = 15
start = time.time()
while not wlan.isconnected():
    if time.time() - start > timeout:
        print("WLAN connection failed")
        break
    time.sleep(0.5)

if wlan.isconnected():
    print("WLAN connected, IP:", wlan.ifconfig()[0])

# Hardware Setup
ow = onewire.OneWire(Pin(WATER_TEMP_SENSOR_PIN))
ds = ds18x20.DS18X20(ow)
sensors = ds.scan()

pump1 = Pin(PUMP1_RELAY_PIN, Pin.OUT)
heater = Pin(HEATER_RELAY_PIN, Pin.OUT)

bubbles = ADC(Pin(BUBBLES_POTI_PIN))
bubbles.atten(ADC.ATTN_11DB)
cover_button = Pin(COVER_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Connect to MQTT
client = connect_mqtt()

last_ping = time.time()
last_run_ms = time.ticks_ms()
ds.convert_temp()

while True:
    try:
        # Check messages safely
        client.check_msg()

        # Keepalive ping
        if time.time() - last_ping > PING_INTERVAL:
            client.ping()
            last_ping = time.time()

        # Sensor update loop
        if time.ticks_diff(time.ticks_ms(), last_run_ms) >= SENSOR_INTERVAL_MS:
            for sensor in sensors:
                temp = ds.read_temp(sensor)
                temp_str = f"{temp:.1f}"
                
                print(f"Target: {TARGET_TEMP:.1f}°C | Current: {temp_str}°C")

                cover_closed = not cover_button.value()
                bubble_level = bubbles.read()
                bubble_level = control_bubble_level(bubble_level, cover_closed)

                bubble_level_text = get_bubble_level_text(bubble_level)

                # Publish current temperature retained
                client.publish(b"whirlpool/current_temp", temp_str.encode(), retain=True)

                print("Bubble intensity: ", bubble_level_text)

                if pump_should_run(temp, TARGET_TEMP):
                    heater.on()
                    pump1.on()
                    print("Pump and heater running.")
                else:
                    pump1.off()
                    heater.off()
                    print("Pump and heater stopped.")
                    
            ds.convert_temp()
            last_run_ms = time.ticks_ms()

        time.sleep_ms(20)

    except Exception as e:
        print("MQTT network loop exception:", e, "- reconnecting...")
        time.sleep(2)
        try:
            client = connect_mqtt()
            last_ping = time.time()
        except Exception as e2:
            print("Reconnect failed:", e2)
            time.sleep(5)