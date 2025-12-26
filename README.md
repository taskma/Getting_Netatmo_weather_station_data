# Netatmo Weather Station → Python → MQTT

Fetch Netatmo Weather Station data via the Netatmo API and publish telemetry to an MQTT broker.

This project is intentionally **simple and automation-friendly**: run it on a schedule (cron/systemd timer), and your MQTT consumers (Home Assistant, Node-RED, custom apps) will always have fresh sensor values.

---

## What it publishes

The script publishes each metric to a dedicated MQTT topic (retained by default):

- `netatmo/outTemperature`
- `netatmo/outHumidity`
- `netatmo/outtime_utc`
- `netatmo/outtime_utc_str`
- `netatmo/outMinTemp`
- `netatmo/outMaxTemp`
- `netatmo/inTemperature`
- `netatmo/inHumidity`
- `netatmo/inPressure`
- `netatmo/inCO2`
- `netatmo/intime_utc`
- `netatmo/intime_utc_str`

> If you prefer a single JSON payload topic (e.g., `home/netatmo/weather`), you can easily wrap/aggregate these topics in Node-RED/Home Assistant, or add a small optional “publish JSON” feature.

---

## Architecture

```mermaid
flowchart LR
  N["Python Script\\nnetatmo_mqtt.py"] -->|HTTPS| A["Netatmo API"]
  N -->|MQTT publish (retained)| B["MQTT Broker"]
  HA["Home Assistant / Node-RED"] <--> B
  APP["CLI / Custom Apps"] <--> B
```

---

## Features

- ✅ **Python 3** refactor (clean structure, typing, logging, CLI)
- ✅ Netatmo **OAuth token management** (request + refresh)
- ✅ Token stored locally in `token.xml`
- ✅ Simple **caching** to reduce API calls (`measures.xml` with TTL)
- ✅ MQTT publish **retained** (so dashboards/automations immediately see the latest values)
- ✅ Optional `--insecure` mode for TLS troubleshooting (not recommended for real use)

---

## Prerequisites

- Netatmo Developer credentials:
  - `client_id`
  - `client_secret`
  - Netatmo account `username` + `password`
- An MQTT broker (e.g., Mosquitto)
- Python 3.9+ and `paho-mqtt`

Install dependency:

```bash
pip install paho-mqtt
```

---

## Configuration

### 1) Create settings file

Copy the example:

```bash
cp netatmo_settings.xml.example netatmo_settings.xml
```

Edit `netatmo_settings.xml` and fill your real credentials:

```xml
<settings>
  <authentication client_id="YOUR_CLIENT_ID"
                  client_secret="YOUR_CLIENT_SECRET"
                  username="YOUR_NETATMO_USERNAME"
                  password="YOUR_NETATMO_PASSWORD" />
</settings>
```

### 2) Files created/used by the script

- `netatmo_settings.xml` → **your credentials** (you create/edit this)
- `token.xml` → cached OAuth token (auto-generated)
- `measures.xml` → cached measures (auto-generated)

> Recommended: **do not commit** `netatmo_settings.xml`, `token.xml`, or `measures.xml`.

---

## Run

Basic:

```bash
python3 netatmo_mqtt.py
```

Specify MQTT broker:

```bash
python3 netatmo_mqtt.py --mqtt-host 192.168.1.10 --mqtt-port 1883
```

Debug logging:

```bash
python3 netatmo_mqtt.py --log-level DEBUG
```

Cache TTL (seconds):

```bash
python3 netatmo_mqtt.py --cache-ttl 150
```

TLS troubleshooting only (disables certificate verification):

```bash
python3 netatmo_mqtt.py --insecure
```

---

## Scheduling

### Cron (example: every 5 minutes)

```cron
*/5 * * * * /usr/bin/python3 /path/to/netatmo_mqtt.py --mqtt-host 127.0.0.1 >> /var/log/netatmo_mqtt.log 2>&1
```

### systemd timer (recommended)

Create a service + timer to run every N minutes (keeps logs in journal).  
*(If you want, I can generate the `.service` and `.timer` files for you.)*

---

## Notes / Behavior

- The script fetches data for **one Netatmo station** at a time.
- It currently uses:
  - the **first** station device in the response (`devices[0]`)
  - the **first** module as “outdoor” (`modules[0]`)
- Timestamps are marked as `"outofdate"` if the reading is older than a threshold (default: 3000 seconds).

---

## Troubleshooting

- **Settings not configured**
  - The script will create a skeleton `netatmo_settings.xml` if missing, but it must be edited with real credentials.
- **MQTT connection issues**
  - Verify broker address/port and that your firewall allows it.
  - Try `--log-level DEBUG`.
- **Netatmo API errors**
  - Check your credentials and that your Netatmo developer app is set up correctly.
  - If token refresh fails, you can delete `token.xml` and rerun.

---

## Security

- By default, TLS verification is **enabled** for Netatmo API calls.
- Avoid `--insecure` unless you’re diagnosing certificate issues on a trusted network.
- Keep `netatmo_settings.xml` and `token.xml` private (do not commit to GitHub).

---

## License

Add a `LICENSE` file (MIT/Apache-2.0/etc.) and mention it here.

![alt text](https://github.com/taskma/Getting_Netatmo_weather_station_data/blob/master/netatmo.jpeg)
![alt text](https://github.com/taskma/Getting_Netatmo_weather_station_data/blob/master/mqtt-diagram.png)

