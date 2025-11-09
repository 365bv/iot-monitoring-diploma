import paho.mqtt.client as mqtt
import json
import logging
from typing import Optional, Dict, Any

# --- Settings ---
BROKER_ADDRESS = "mqtt_broker"
PORT = 1883
MQTT_TOPIC = "norway/energy/wind-turbine/+/status"

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
    if rc == 0:
        logging.info(f"✅ [MQTT] Successfully connected to broker {BROKER_ADDRESS}")
        client.subscribe(MQTT_TOPIC)
    else:
        logging.error(f"❌ [MQTT] Connection failed with code: {rc}")

def on_subscribe(client: mqtt.Client, userdata, mid, granted_qos):
    """Callback for when the client successfully subscribes."""
    logging.info(f"🔔 [MQTT] Subscribed to topic: {MQTT_TOPIC}")

def check_for_anomalies(data: Dict[str, Any]):
    """
    This is the core logic for the alerter.
    It checks incoming data against predefined rules.
    """
    try:
        turbine_id = data.get("turbine_id", "Unknown")
        
        # --- Rule 1: Check for anomaly flag (from sensor) ---
        if data.get("is_anomaly") == True:
            logging.critical(
                f"🚨 CRITICAL ALERT (from sensor): Anomaly detected for {turbine_id}!"
                f" Payload: {json.dumps(data)}"
            )

        # --- Rule 2: Check for high temperature ---
        elif data.get("gearbox_temp_c") is not None and data.get("gearbox_temp_c") > CRITICAL_TEMP_THRESHOLD:
            logging.critical(
                f"🚨 CRITICAL ALERT (rule breach): Gearbox overheating on {turbine_id}!"
                f" Temperature: {data.get('gearbox_temp_c')}°C"
            )


    except Exception as e:
        logging.error(f"🔥 Error processing rules: {e}")

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """Callback for when a message is received."""
    data = parse_payload(msg.payload)
    
    if data:
        check_for_anomalies(data)
    else:
        pass 

def setup_client() -> Optional[mqtt.Client]:
    """Creates, configures, and connects the MQTT client."""
    client = mqtt.Client()
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
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    try:
        run_alerter()
    except KeyboardInterrupt:
        logging.info("\n🛑 Alerter stopped by user.")