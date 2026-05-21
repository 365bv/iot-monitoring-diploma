import os
import paho.mqtt.client as mqtt
import json
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# --- Settings ---
BROKER_ADDRESS = "mqtt_broker"
PORT = 1883
MQTT_TOPIC = "norway/energy/wind-turbine/+/status"
CONTROL_TOPIC = "sim/control/turbine_count"

# Read QoS setting from environment variable
current_qos = int(os.getenv("MQTT_QOS", "0"))

# --- Constants ---
CRITICAL_TEMP_THRESHOLD = 90.0

# --- Logic ---


def parse_payload(payload: bytes) -> Optional[Dict[str, Any]]:
    """
    Parses the raw byte payload into a Python dictionary.
    Returns None if parsing fails.
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
    global current_qos
    if rc == 0:
        logging.info(f"✅ [MQTT] Successfully connected to broker {BROKER_ADDRESS}")
        
        client.subscribe(MQTT_TOPIC, qos=current_qos)
        client.subscribe(CONTROL_TOPIC, qos=1)
    else:
        logging.error(f"❌ [MQTT] Connection failed with code: {rc}")


def on_subscribe(client: mqtt.Client, userdata, mid, granted_qos):
    pass

def check_for_anomalies(client: mqtt.Client, data: Dict[str, Any], qos_level: int):
    """Checks incoming data against predefined rules and publishes alerts."""
    try:
        turbine_id = data.get("turbine_id", "Unknown")
        alert_msg = None


        if data.get("is_anomaly"):
            alert_msg = f"Critical Sensor Anomaly detected for {turbine_id}!"
            logging.critical(f"🚨 CRITICAL ALERT (from sensor): {alert_msg} [Running at QoS {qos_level}]")
        elif (
            data.get("gearbox_temp_c") is not None
            and data.get("gearbox_temp_c") > CRITICAL_TEMP_THRESHOLD
        ):
            alert_msg = f"Gearbox overheating on {turbine_id}! Temp: {data.get('gearbox_temp_c')}°C"
            logging.critical(f"🚨 CRITICAL ALERT (rule breach): {alert_msg} [Running at QoS {qos_level}]")
        if alert_msg:
            alert_payload = json.dumps({
                "turbine_id": turbine_id,
                "message": alert_msg,
                "timestamp": data.get("timestamp_ns", 0)
            })
            client.publish("norway/energy/alerts", alert_payload, qos=1)

    except Exception as e:
        logging.error(f"🔥 Error processing rules: {e}")

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """Callback for when a message is received."""
    global current_qos
    
    if msg.topic == CONTROL_TOPIC:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            if "qos" in payload:
                new_qos = int(payload["qos"])
                if new_qos != current_qos:
                    current_qos = new_qos
                    client.subscribe(MQTT_TOPIC, qos=current_qos)
                    logging.info(f"🔄 Alerter dynamically updated subscription QoS to: {current_qos}")
        except Exception as e:
            logging.error(f"Failed to parse control message: {e}")
        return

    data = parse_payload(msg.payload)

    if data:
        check_for_anomalies(client, data, current_qos)


def setup_client() -> Optional[mqtt.Client]:
    """Creates, configures, and connects the MQTT client."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
    except Exception as e:
        logging.error(f"🔥 [MQTT] Failed to connect to broker: {e}")
        return None
    return client


def run_alerter():
    """Starts the alerter service."""
    mqtt_client = setup_client()

    if mqtt_client is None:
        logging.critical("Exiting program, MQTT client setup failed.")
        return

    logging.info("🐾 Watchdog alerter is now listening for messages...")
    mqtt_client.loop_forever()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (alerter) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        run_alerter()
    except KeyboardInterrupt:
        logging.info("\n🛑 Alerter stopped by user.")
