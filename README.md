# Netatmo Weather Station → Python → MQTT

Fetches Netatmo station data and publishes telemetry via MQTT.

## Prerequisites
- Netatmo developer credentials
- `netatmo_settings.xml` filled with your tokens (**DO NOT commit secrets**)
- MQTT broker

## Run
bash
python get_station_data.py

Output

Publishes weather metrics (temperature, humidity, etc.) to MQTT.
(Optional) Example: home/netatmo/weather → {"temp":23.4,"humidity":41,"pressure":1012}

⸻

Notes
	•	Configure MQTT connection settings.
	•	Fill netatmo_settings.xml.
	•	This script fetches data for one Netatmo Weather Station at a time.

![alt text](https://github.com/taskma/Getting_Netatmo_weather_station_data/blob/master/netatmo.jpeg)
![alt text](https://github.com/taskma/Getting_Netatmo_weather_station_data/blob/master/mqtt-diagram.png)

