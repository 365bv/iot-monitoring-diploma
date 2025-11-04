import paho.mqtt.client as mqtt
import json
import influxdb_client
import os
import logging
from dotenv import load_dotenv
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Optional, Dict, Any

# Load environment variables from .env file
load_dotenv()

# --- Settings ---
BROKER_ADDRESS = "mqtt_broker"
PORT = 1883
MQTT_TOPIC = "norway/energy/wind-turbine/+/status"

# InfluxDB Settings
INFLUX_URL = "http://database:8086"
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# --- Logic ---

def parse_payload(payload: bytes) -> Optional[Dict[str, Any]]:
    """
    Parses the raw byte payload into a Python dictionary.
    Returns None if parsing fails due to invalid JSON or decoding errors.
    """
    try:
        payload_str = payload.decode("utf-8")
        data = json.loads(payload_str)
        return data
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logging.warning(f"⚠️ Failed to parse payload: {e}. Payload: {payload}")
        return None
    except Exception as e:
        logging.error(f"🔥 An unexpected error occurred in parse_payload: {e}")
        return None

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Callback for when the client connects."""
    if rc == 0:
        logging.info(f"✅ Successfully connected to broker {BROKER_ADDRESS}")
        # Subscribing in on_connect ensures we re-subscribe if connection is lost
        client.subscribe(MQTT_TOPIC)
    else:
        logging.error(f"❌ Connection failed with code: {rc}")

def on_subscribe(client: mqtt.Client, userdata, mid, granted_qos):
    """Callback for when the client successfully subscribes."""
    logging.info(f"🔔 Subscribed to topic: {MQTT_TOPIC}")

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """
    Callback for when a message is received.
    This is the core logic of the collector.
    """
    data = parse_payload(msg.payload)
    
    if data:
       write_to_influxdb(userdata['influx_write_api'], data)
    else:
        # The error is already logged inside parse_payload
        pass

def write_to_influxdb(write_api: influxdb_client.WriteApi, data: Dict[str, Any]):
    """Formats and writes a data point to InfluxDB."""
    try:
        point = (
            influxdb_client.Point("turbine_status")
            .tag("turbine_id", data.get("turbine_id", "Unknown"))
            .field("wind_speed_ms", data.get("wind_speed_ms"))
            .field("rotor_speed_rpm", data.get("rotor_speed_rpm"))
            .field("power_output_kw", data.get("power_output_kw"))
            .field("gearbox_temp_c", data.get("gearbox_temp_c"))
            .time(data.get("timestamp"), write_precision="s") # 's' for seconds
        )
        
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        logging.debug(f"✅ [InfluxDB] Wrote data for {data.get('turbine_id')}")

    except Exception as e:
        logging.error(f"🔥 [InfluxDB] Error writing to database: {e}")


def setup_mqtt_client(influx_write_api: influxdb_client.WriteApi) -> Optional[mqtt.Client]:
    """Creates, configures, and connects the MQTT client."""
    
    # We will pass the InfluxDB client object into the MQTT client's 'userdata'
    # This makes it accessible inside the on_message callback
    client = mqtt.Client(userdata={"influx_write_api": influx_write_api})
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    
    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
    except Exception as e:
        logging.error(f"🔥 [MQTT] Failed to connect to broker: {e}")
        return None
    return client 

def run_collector():
    """Starts the data collector."""
    
    # 1. Set up InfluxDB Client
    try:
        influx_client = influxdb_client.InfluxDBClient(
            url=INFLUX_URL,
            token=INFLUX_TOKEN,
            org=INFLUX_ORG
        )
        # Create a "Write API" client
        # SYNCHRONOUS means we write one point at a time
        write_api = influx_client.write_api(write_options=SYNCHRONOUS)
        logging.info("✅ [InfluxDB] Successfully connected")
    except Exception as e:
        logging.critical(f"🔥 [InfluxDB] Failed to connect to InfluxDB: {e}")
        return

    # 2. Set up MQTT Client (and give it the InfluxDB writer)
    mqtt_client = setup_mqtt_client(write_api)
    
    if mqtt_client is None:
        logging.critical("Exiting program, MQTT client setup failed.")
        return

    logging.info("🎧 Data collector is now listening for messages...")
    mqtt_client.loop_forever()

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (data_collector) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    try:
        run_collector()
    except KeyboardInterrupt:
        logging.info("\n🛑 Collector stopped by user.")