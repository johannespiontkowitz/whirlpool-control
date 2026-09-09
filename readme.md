# Whirlpool Controller
## __Open Todos__
- Target temp control currently available only via home assistant - needs manual control as well
- Home assistant does show values (current and target) even when esp32 is not reachable -> should show unavailable
- LEDs strips not implemented
- Virtual ESP does not reach WIFI (only it's own) -> expected behaviour for virtual ESP. Will try again with physical device.
- Homeassistant only available locally
- Display relevant information on a physical screen ([https://animator.wokwi.com/](https://animator.wokwi.com/) might come in handy)
- Add on/off switch for pumps 2 and 3
- ...? 

## Overview
This project contains code to run a ESP32 as a electronic control unit for a whirlpool. 

__The (real life) whirlpool currently features__
- 2 Pumps that control the waterflow (and start pumping once the temperature drops below a target)
- a turbine to produce bubbles
- a temperature sensor that monitors the water temp
- a heater that must only run when the pumps are pumping
- LEDs
- Radio / music
- manual cover

__For the future, there are some changes planned to the (physical) pool__
- replace the current heater with an instantaneous water heater
- add Smart-Home compatibility to monitor and control the pool remotely (current and target temp, bubbles, LED color and brightness)
- a motor powered cover (that triggers sensors when it's closed to stop bubbling and dim / turn off the LEDs)

__Possible extensions to the planned setup__  
Since the whirlpool is included in a sauna house, maybe controlling the sauna remotely would be a nice next project

## Project setup & execution
### Clone the project
1. Git must be installed on the system. (Check in terminal by typing `git --version`. If not, download installer [here](https://git-scm.com/install/windows))
2. Make sure python 3.14.x is installed. (Check in terminal by typing `python3 --version`. If not, download installer [here](https://www.python.org/downloads/))
3. Create a local folder and navigate into that folder. Open a terminal window there. Clone the project by running the following command in the terminal: `git clone https://github.com/johannespiontkowitz/whirlpool-control`  
4. Setup the virtual environment `python3 -m venv venv`  
5. Activate the venv (see *Important commands* section below).  
6. Install esp toolboxes: `pip install esptool mpremote`  
7. In your src/configs folder, make a copy of both network_config.example.py and mqtt_config.example.py, remove the .example section and fill in values (for mqtt values, see *Home assistant setup & connection* section below).

### Install Wokwi simulator
1. Install the [Wokwi extension](https://marketplace.visualstudio.com/items?itemName=Wokwi.wokwi-vscode) for VS Code.
2. Create an account at [wokwi.com](https://wokwi.com/) (needed for license).
3. Open the simulator (Ctrl + Shift + P -> select *Wokwi: Start simulator*). It should prompt you to insert the license, follow instructions.

### Run the project
Open the simulator with CTRL+SHIFT+P -> select *Wokwi: Start Simulator*. A simulator tab is opened. Keep the window open and select your terminal with venv active. Paste `python -m mpremote connect port:rfc2217://localhost:4000 mount src run src/main.py` and run.

## Important commands
### Activate venv
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`  
`venv\Scripts\Activate`

### Upload code to the esp simulator (wokwi)
`python -m mpremote connect port:rfc2217://localhost:4000 mount src run src/main.py`

### Upload code to the physical esp
The following is a sample on how all files need to be transferred.  
__erase_flash__ and __write_flash__ are not necessary in all cases. If you feel the esp32 is faulty, use these lines to flash the software completely.

py -m pip install esptool mpremote

py -m esptool --chip esp32 --port COM3 erase_flash
py -m esptool --chip esp32 --port COM3 --baud 460800 write_flash -z 0x1000 .\esp32\ESP32_GENERIC-20251209-v1.27.0.bin

mpremote connect COM3 fs mkdir :components
mpremote connect COM3 fs mkdir :components/oled

mpremote connect COM3 fs mkdir :configs
mpremote connect COM3 fs mkdir :controllers

mpremote connect COM3 fs cp .\src\components\oled\ssd1306.py :components/oled/ssd1306.py
mpremote connect COM3 fs cp .\src\components\limit_switch.py :components/limit_switch.py
mpremote connect COM3 fs cp .\src\configs\config.py :configs/config.py
mpremote connect COM3 fs cp .\src\configs\mqtt_config.py :configs/mqtt_config.py
mpremote connect COM3 fs cp .\src\configs\network_config.py :configs/network_config.py

mpremote connect COM3 fs cp .\src\controllers\bubble_control.py :controllers/bubble_control.py
mpremote connect COM3 fs cp .\src\controllers\pump_control.py :controllers/pump_control.py
mpremote connect COM3 fs cp .\src\main.py :main.py

mpremote connect COM3 reset
mpremote connect COM3 repl


### GitHub
`git init`  
`git add .`  
`git commit -m "Commit message"`  
`git push -u origin main`  
`git branch -M main`  
`git fetch`  
`git pull`  

## Home assistant setup & connection
### Network config
Inside src/configs, use the *_config.example.py to files withut the .example and fill with real values.
`WIFI_SSID = "YourNetworkName"`  
`WIFI_PASSWORD = "YourNetworkPassword"`  
`MQTT_BROKER = "homeassistant.local"` #IP of home assistant broker

### Home assistant setup
To test the home assistant implementation, we set up a VM that runs Home Assistant virtually in the network.  
Follow [http://home-assistant.io/installation/windows/](http://home-assistant.io/installation/windows/).
When done, this will enable us to reach [http://homeassistant.local/](homeassistant.local) on the host machine.
