# Whirlpool Controller
## __Open Todos__
- Home assistant does show values (current and target) even when esp32 is not reachable -> should show unavailable
- LEDs not implemented
- ESP does not reach WIFI (only it's own)
- Homeassistant only available locally
- ...? 

## Overview
This project contains code to run a ESP32 as a electronic control unit for a whirlpool. 

__The (real life) whirlpool currently features__
- 2 Pumps that control the waterflow (and start pumping once the temperature drops below a target)
- a turbine to produce bubbles
- a temperature sensor that monitors the water temp
- a heater that must only run when the pumps are pumping
- LEDs

__For the future, there are some changes planned to the pool__
- replace the current heater with an instantaneous water heater
- add Smart-Home compatibility to monitor and control the pool remotely
- a motor powered cover (that triggers sensors when it's closed to stop bubbling and dim / turn off the LEDs)

## Project setup
After cloning the project, make sure python 3.14.x is installed (`python3 --version`)  
Setup the virtual environment `python3 -m venv venv`  
Activate the venv (see commands below).  
Lastly, install esp toolboxes:
`pip install esptool mpremote`

## Important commands
### Activate venv
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`  
`venv\Scripts\Activate.ps1`

### Upload code to the esp (below is the code for WOKWI simulator)
`python -m mpremote connect port:rfc2217://localhost:4000 mount src run src/main.py`

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
