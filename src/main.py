import time
import network
import machine
import ubinascii

import components.oled.ssd1306 as ssd1306
#from components.oled.animations import CIRCLES_MENU_3


from machine import Pin, ADC, I2C
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
MQTT_RECONNECT_INTERVAL = 10  # seconds between reconnect attempts once disconnected

TARGET_TEMP = 30.0
client = None

# screen setup
SCREEN_WIDTH = 128 # OLED width,  in pixels
SCREEN_HEIGHT = 64 # OLED height, in pixels

i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, i2c)

oled.fill(0)
oled.text_scaled("Whirlpool", 0, 12)
oled.text_scaled("Booting...", 0, 24)
oled.show()

# CIRCLES_MENU_3.play_loop(oled) # this obviously blocks everything else!!

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


def try_connect_mqtt():
    """Attempt an MQTT connection, returning None instead of raising on failure."""
    try:
        return connect_mqtt()
    except Exception as e:
        print("MQTT connect failed:", e)
        return None


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

# CIRCLES_MENU_3.stop(oled)

# Hardware Setup
ow = onewire.OneWire(Pin(WATER_TEMP_SENSOR_PIN))
ds = ds18x20.DS18X20(ow)
sensors = ds.scan()

pump1 = Pin(PUMP1_RELAY_PIN, Pin.OUT)
heater = Pin(HEATER_RELAY_PIN, Pin.OUT)

bubbles = ADC(Pin(BUBBLES_POTI_PIN))
bubbles.atten(ADC.ATTN_11DB)
cover_button = Pin(COVER_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

# Connect to MQTT (non-fatal if broker is unreachable, we retry in the main loop)
client = try_connect_mqtt()
mqtt_last_attempt = time.time()

last_ping = time.time()
last_run_ms = time.ticks_ms()
ds.convert_temp()

while True:
    try:
        if client is None:
            # Broker unreachable at some point - retry periodically without blocking the loop
            if time.time() - mqtt_last_attempt > MQTT_RECONNECT_INTERVAL:
                mqtt_last_attempt = time.time()
                client = try_connect_mqtt()
                if client is not None:
                    last_ping = time.time()
        else:
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

                # Publish current temperature retained (skipped while MQTT is disconnected)
                if client is not None:
                    try:
                        client.publish(b"whirlpool/current_temp", temp_str.encode(), retain=True)
                    except Exception as e:
                        print("MQTT publish failed:", e, "- will reconnect")
                        client = None
                        mqtt_last_attempt = time.time()

                print("Bubble intensity: ", bubble_level_text)

                if pump_should_run(temp, TARGET_TEMP):
                    heater.on()
                    pump1.on()
                    print("Pump and heater running.")
                else:
                    pump1.off()
                    heater.off()
                    print("Pump and heater stopped.")

                oled.fill(0)
                oled.text_scaled("Target: {:.1f}C".format(TARGET_TEMP), 0, 0)
                oled.text_scaled("Temp:   {:.1f}C".format(temp), 0, 9)
                oled.text_scaled("Bubble: {}".format(bubble_level_text), 0, 18)
                oled.text_scaled("Cover: {}".format("closed" if cover_closed else "open"), 0, 27)
                oled.text_scaled("Heat:  {}".format("on" if heater.value() else "off"), 0, 36)
                oled.text_scaled("Pump:  {}".format("on" if pump1.value() else "off"), 0, 45)
                oled.text_scaled("MQTT:  {}".format("connected" if client is not None else "disconnected"), 0, 54)
                oled.show()
                    
            ds.convert_temp()
            last_run_ms = time.ticks_ms()

        time.sleep_ms(20)

    except Exception as e:
        # Heater/pump/sensor logic above keeps running even if MQTT drops here
        print("MQTT network loop exception:", e, "- will retry connecting")
        client = None
        mqtt_last_attempt = time.time()
        time.sleep(1)