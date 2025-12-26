#!/usr/bin/env python3
"""
netatmo_mqtt.py


Requirements
- Python 3.9+
- paho-mqtt (pip install paho-mqtt)

Configuration
- netatmo_settings.xml in the same folder (auto-generated skeleton if missing)

Security note
- TLS verification is enabled by default.
  Use --insecure only for debugging on trusted networks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import paho.mqtt.client as mqtt

# -----------------------------
# Constants / Defaults
# -----------------------------
NETATMO_TOKEN_URL = "https://api.netatmo.com/oauth2/token"
NETATMO_GETSTATIONSDATA_URL = "https://api.netatmo.com/api/getstationsdata"

DEFAULT_MQTT_HOST = "localhost"
DEFAULT_MQTT_PORT = 1883

DEFAULT_CACHE_TTL_SECONDS = 150  # old code: minNetatmoServerConnect
STALE_READING_SECONDS = 3000     # old code: difOutTime/difInTime > 3000 => outofdate

TOKEN_XML = "token.xml"
MEASURES_XML = "measures.xml"
SETTINGS_XML = "netatmo_settings.xml"

# XML node names (kept for compatibility with your original repo)
SETTINGS_ROOT = "settings"
NODE_AUTH = "authentication"
ATTR_AUTH_CLIENT_ID = "client_id"
ATTR_AUTH_CLIENT_SECRET = "client_secret"
ATTR_AUTH_USERNAME = "username"
ATTR_AUTH_PASSWORD = "password"


# -----------------------------
# Data Models
# -----------------------------
@dataclass(frozen=True)
class Authentication:
    client_id: str
    client_secret: str
    username: str
    password: str


@dataclass
class Token:
    access_token: str
    refresh_token: str
    expires_in: int
    expired_at: dt.datetime

    @property
    def is_expiring_soon(self) -> bool:
        # Refresh if expires within 30 seconds
        return self.expired_at <= dt.datetime.now() + dt.timedelta(seconds=30)


@dataclass
class Measures:
    # Outdoor (module)
    out_temperature: str
    out_humidity: str
    out_time_utc: str
    out_time_utc_str: str
    out_min_temp: str
    out_max_temp: str

    # Indoor (main device)
    in_temperature: str
    in_humidity: str
    in_pressure: str
    in_co2: str
    in_time_utc: str
    in_time_utc_str: str

    def to_mqtt_payloads(self) -> Dict[str, str]:
        return {
            "netatmo/outTemperature": self.out_temperature,
            "netatmo/outHumidity": self.out_humidity,
            "netatmo/outtime_utc": self.out_time_utc,
            "netatmo/outtime_utc_str": self.out_time_utc_str,
            "netatmo/outMinTemp": self.out_min_temp,
            "netatmo/outMaxTemp": self.out_max_temp,
            "netatmo/inTemperature": self.in_temperature,
            "netatmo/inHumidity": self.in_humidity,
            "netatmo/inPressure": self.in_pressure,
            "netatmo/inCO2": self.in_co2,
            "netatmo/intime_utc": self.in_time_utc,
            "netatmo/intime_utc_str": self.in_time_utc_str,
        }


# -----------------------------
# Utils
# -----------------------------
def working_dir() -> Path:
    return Path(__file__).resolve().parent


def build_ssl_context(insecure: bool) -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def http_post_form(url: str, form: Dict[str, str], ctx: ssl.SSLContext, timeout: int = 20) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def http_get(url: str, params: Dict[str, str], ctx: ssl.SSLContext, timeout: int = 20) -> str:
    q = urllib.parse.urlencode(params)
    full = f"{url}?{q}"
    req = urllib.request.Request(full, method="GET")
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def parse_timestamp(ts: int) -> Tuple[str, str]:
    # Returns (utc_ts_str, human_str)
    human = dt.datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d_%H:%M:%S")
    return str(ts), human


# -----------------------------
# Settings
# -----------------------------
class SettingsStore:
    def __init__(self, path: Path):
        self.path = path

    def load_or_create(self) -> Authentication:
        if not self.path.exists():
            logging.warning("Settings file not found: %s. Creating a skeleton.", self.path)
            self._create_skeleton()

        try:
            root = ET.parse(self.path).getroot()
        except Exception as e:
            raise RuntimeError(f"Failed to parse settings XML: {self.path}") from e

        auth_node = root.find(f".//{NODE_AUTH}")
        if auth_node is None:
            raise RuntimeError(f"Missing <{NODE_AUTH}> section in {self.path}")

        def get_attr(name: str) -> str:
            v = auth_node.get(name, "").strip()
            if not v or v in ("CLIENT_ID", "CLIENT_SECRET", "USERNAME", "PASSWORD"):
                raise RuntimeError(
                    f"Settings value '{name}' is not configured in {self.path}. "
                    f"Edit the file and set real credentials."
                )
            return v

        return Authentication(
            client_id=get_attr(ATTR_AUTH_CLIENT_ID),
            client_secret=get_attr(ATTR_AUTH_CLIENT_SECRET),
            username=get_attr(ATTR_AUTH_USERNAME),
            password=get_attr(ATTR_AUTH_PASSWORD),
        )

    def _create_skeleton(self) -> None:
        root = ET.Element(SETTINGS_ROOT)
        auth = ET.SubElement(root, NODE_AUTH)
        auth.set(ATTR_AUTH_CLIENT_ID, "CLIENT_ID")
        auth.set(ATTR_AUTH_CLIENT_SECRET, "CLIENT_SECRET")
        auth.set(ATTR_AUTH_USERNAME, "USERNAME")
        auth.set(ATTR_AUTH_PASSWORD, "PASSWORD")
        ET.ElementTree(root).write(self.path, encoding="utf-8", xml_declaration=True)


# -----------------------------
# Token persistence (XML, compatible)
# -----------------------------
class TokenStoreXML:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Optional[Token]:
        if not self.path.exists():
            return None
        try:
            root = ET.parse(self.path).getroot()
            access_token = root.get("access_token", "")
            refresh_token = root.get("refresh_token", "")
            expires_in = int(root.get("expires_in", "0"))
            expired_at_raw = root.get("expired_at", "")
            if not access_token or not refresh_token or not expired_at_raw:
                return None
            expired_at = dt.datetime.strptime(expired_at_raw, "%Y-%m-%d %H:%M:%S")
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=expires_in,
                expired_at=expired_at,
            )
        except Exception:
            logging.exception("Failed to load token file: %s", self.path)
            return None

    def save(self, token: Token) -> None:
        root = ET.Element("token")
        root.set("access_token", token.access_token)
        root.set("refresh_token", token.refresh_token)
        root.set("expires_in", str(token.expires_in))
        root.set("expired_at", token.expired_at.strftime("%Y-%m-%d %H:%M:%S"))
        ET.ElementTree(root).write(self.path, encoding="utf-8", xml_declaration=True)

    def delete(self) -> None:
        try:
            if self.path.exists():
                self.path.unlink()
        except Exception:
            logging.exception("Failed to delete token file: %s", self.path)


# -----------------------------
# Measures cache (XML, compatible)
# -----------------------------
class MeasuresCacheXML:
    def __init__(self, path: Path, ttl_seconds: int):
        self.path = path
        self.ttl_seconds = ttl_seconds

    def is_fresh(self) -> bool:
        if not self.path.exists():
            return False
        age = time.time() - self.path.stat().st_mtime
        return age <= self.ttl_seconds

    def load(self) -> Optional[Measures]:
        if not self.path.exists():
            return None
        try:
            root = ET.parse(self.path).getroot()
            # Stored as attributes on <measures .../>
            def g(name: str, default: str = "") -> str:
                return (root.get(name) or default).strip()

            return Measures(
                out_temperature=g("out_temperature"),
                out_humidity=g("outHumidity"),
                out_time_utc=g("outtime_utc"),
                out_time_utc_str=g("outtime_utc_str"),
                out_min_temp=g("outMinTemp"),
                out_max_temp=g("outMaxTemp"),
                in_temperature=g("inTemperature"),
                in_humidity=g("inHumidity"),
                in_pressure=g("inPressure"),
                in_co2=g("inCO2"),
                in_time_utc=g("intime_utc"),
                in_time_utc_str=g("intime_utc_str"),
            )
        except Exception:
            logging.exception("Failed to load measures cache: %s", self.path)
            return None

    def save(self, measures: Measures) -> None:
        root = ET.Element("measures")
        # Keep old attribute keys for backward compatibility
        root.set("out_temperature", measures.out_temperature)
        root.set("outHumidity", measures.out_humidity)
        root.set("outtime_utc", measures.out_time_utc)
        root.set("outtime_utc_str", measures.out_time_utc_str)
        root.set("outMinTemp", measures.out_min_temp)
        root.set("outMaxTemp", measures.out_max_temp)

        root.set("inTemperature", measures.in_temperature)
        root.set("inHumidity", measures.in_humidity)
        root.set("inPressure", measures.in_pressure)
        root.set("inCO2", measures.in_co2)
        root.set("intime_utc", measures.in_time_utc)
        root.set("intime_utc_str", measures.in_time_utc_str)

        ET.ElementTree(root).write(self.path, encoding="utf-8", xml_declaration=True)


# -----------------------------
# Netatmo API client
# -----------------------------
class NetatmoClient:
    def __init__(self, auth: Authentication, ssl_ctx: ssl.SSLContext, token_store: TokenStoreXML):
        self.auth = auth
        self.ssl_ctx = ssl_ctx
        self.token_store = token_store

    def get_token(self) -> Token:
        token = self.token_store.load()
        if token is None:
            logging.info("No token found, requesting a new token.")
            token = self._request_token()
            self.token_store.save(token)
            return token

        if token.is_expiring_soon:
            logging.info("Token expiring soon, refreshing.")
            token = self._refresh_token(token.refresh_token)
            self.token_store.save(token)
        return token

    def _request_token(self) -> Token:
        payload = {
            "grant_type": "password",
            "client_id": self.auth.client_id,
            "client_secret": self.auth.client_secret,
            "username": self.auth.username,
            "password": self.auth.password,
        }
        raw = http_post_form(NETATMO_TOKEN_URL, payload, self.ssl_ctx)
        return self._token_from_json(raw)

    def _refresh_token(self, refresh_token: str) -> Token:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.auth.client_id,
            "client_secret": self.auth.client_secret,
        }
        raw = http_post_form(NETATMO_TOKEN_URL, payload, self.ssl_ctx)
        return self._token_from_json(raw)

    @staticmethod
    def _token_from_json(raw: str) -> Token:
        try:
            data = json.loads(raw)
            expires_in = int(data["expires_in"])
            expired_at = dt.datetime.now() + dt.timedelta(seconds=expires_in)
            return Token(
                access_token=data["access_token"],
                refresh_token=data["refresh_token"],
                expires_in=expires_in,
                expired_at=expired_at,
            )
        except Exception as e:
            raise RuntimeError("Failed to parse token response from Netatmo.") from e

    def get_station_measures(self, access_token: str) -> Measures:
        params = {"access_token": access_token}
        raw = http_get(NETATMO_GETSTATIONSDATA_URL, params, self.ssl_ctx)
        try:
            payload = json.loads(raw)
        except Exception as e:
            raise RuntimeError("Failed to decode Netatmo station data JSON.") from e

        if payload.get("status") != "ok":
            raise RuntimeError(f"Netatmo API error: status={payload.get('status')} body={payload.get('error')}")

        devices = (payload.get("body") or {}).get("devices") or []
        if not devices:
            raise RuntimeError("No Netatmo devices found in response.")

        main = devices[0]
        modules = main.get("modules") or []
        if not modules:
            raise RuntimeError("No Netatmo modules found under main device.")

        # Your old script used modules[0] as outdoor and main device as indoor
        outdoor = modules[0]

        m_dash = outdoor.get("dashboard_data") or {}
        in_dash = main.get("dashboard_data") or {}

        # Extract timestamps and staleness markers
        out_time_utc = int(m_dash.get("time_utc", 0))
        in_time_utc = int(in_dash.get("time_utc", 0))
        out_time_utc_str_val = parse_timestamp(out_time_utc)[1] if out_time_utc else "unknown"
        in_time_utc_str_val = parse_timestamp(in_time_utc)[1] if in_time_utc else "unknown"

        now_ts = int(time.time())
        if out_time_utc and (now_ts - out_time_utc) > STALE_READING_SECONDS:
            out_time_utc_str_val = "outofdate"
        if in_time_utc and (now_ts - in_time_utc) > STALE_READING_SECONDS:
            in_time_utc_str_val = "outofdate"

        # All values stored as strings for MQTT payload simplicity
        return Measures(
            out_temperature=str(m_dash.get("Temperature", "")),
            out_humidity=str(m_dash.get("Humidity", "")),
            out_time_utc=str(out_time_utc),
            out_time_utc_str=out_time_utc_str_val,
            out_min_temp=str(m_dash.get("min_temp", "")),
            out_max_temp=str(m_dash.get("max_temp", "")),
            in_temperature=str(in_dash.get("Temperature", "")),
            in_humidity=str(in_dash.get("Humidity", "")),
            in_pressure=str(in_dash.get("Pressure", "")),
            in_co2=str(in_dash.get("CO2", "")),
            in_time_utc=str(in_time_utc),
            in_time_utc_str=in_time_utc_str_val,
        )


# -----------------------------
# MQTT publisher
# -----------------------------
class MqttPublisher:
    def __init__(self, host: str, port: int, client_id: str = "netatmo-publisher"):
        self.host = host
        self.port = port
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect

    @staticmethod
    def _on_connect(client: mqtt.Client, userdata, flags, rc):
        logging.info("MQTT connected rc=%s", rc)

    def publish_many(self, payloads: Dict[str, str], retain: bool = True) -> None:
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

        try:
            for topic, value in payloads.items():
                if value is None:
                    continue
                self.client.publish(topic, payload=str(value), qos=0, retain=retain)
                logging.debug("MQTT publish %s => %s", topic, value)
            # give the network loop a moment to flush publishes
            time.sleep(1.0)
        finally:
            self.client.loop_stop()
            self.client.disconnect()


# -----------------------------
# Main
# -----------------------------
def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Publish Netatmo station measures to MQTT.")
    p.add_argument("--mqtt-host", default=DEFAULT_MQTT_HOST)
    p.add_argument("--mqtt-port", type=int, default=DEFAULT_MQTT_PORT)
    p.add_argument("--cache-ttl", type=int, default=DEFAULT_CACHE_TTL_SECONDS, help="API cache TTL seconds")
    p.add_argument("--insecure", action="store_true", help="Disable TLS verification (debug only)")
    p.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    base = working_dir()
    settings_path = base / SETTINGS_XML
    token_path = base / TOKEN_XML
    measures_path = base / MEASURES_XML

    ssl_ctx = build_ssl_context(args.insecure)

    auth = SettingsStore(settings_path).load_or_create()
    token_store = TokenStoreXML(token_path)
    measures_cache = MeasuresCacheXML(measures_path, ttl_seconds=args.cache_ttl)

    netatmo = NetatmoClient(auth=auth, ssl_ctx=ssl_ctx, token_store=token_store)
    publisher = MqttPublisher(host=args.mqtt_host, port=args.mqtt_port)

    try:
        # Token
        token = netatmo.get_token()

        # Measures with cache
        measures: Optional[Measures]
        if measures_cache.is_fresh():
            measures = measures_cache.load()
            logging.info("Using cached measures (%s).", measures_path.name)
        else:
            measures = None

        if measures is None:
            logging.info("Fetching measures from Netatmo.")
            measures = netatmo.get_station_measures(token.access_token)
            measures_cache.save(measures)

        # Publish
        payloads = measures.to_mqtt_payloads()
        publisher.publish_many(payloads, retain=True)
        logging.info("Published %d topics to MQTT.", len(payloads))
        return 0

    except Exception:
        logging.exception("Fatal error.")
        # If token issues occur, allow clean re-auth on next run
        # (but do NOT delete token on every random error)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
