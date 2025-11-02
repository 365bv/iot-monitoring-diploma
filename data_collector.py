import paho.mqtt.client as mqtt
import json
from typing import Optional, Dict, Any

# --- Settings ---
BROKER_ADDRESS = "broker.hivemq.com"  # Public broker for Stage 2 testing
PORT = 1883
# Wildcard topic to subscribe to all turbine status updates
MQTT_TOPIC = "norway/energy/wind-turbine/+/status"

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
        print(f"⚠️ Failed to parse payload: {e}. Payload: {payload}")
        return None
    except Exception as e:
        print(f"🔥 An unexpected error occurred in parse_payload: {e}")
        return None

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Callback for when the client connects."""
    if rc == 0:
        print(f"✅ Successfully connected to broker {BROKER_ADDRESS}")
        # Subscribing in on_connect ensures we re-subscribe if connection is lost
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Connection failed with code: {rc}")

def on_subscribe(client: mqtt.Client, userdata, mid, granted_qos):
    """Callback for when the client successfully subscribes."""
    print(f"🔔 Subscribed to topic: {MQTT_TOPIC}")

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """
    Callback for when a message is received.
    This is the core logic of the collector.
    """
    data = parse_payload(msg.payload)
    
    if data:
        turbine_id = data.get("turbine_id", "Unknown")
        wind = data.get("wind_speed_ms", "N/A")
        rpm = data.get("rotor_speed_rpm", "N/A")
        power = data.get("power_output_kw", "N/A")
        temp = data.get("gearbox_temp_c", "N/A")
        
        # TODO: Replace this print statement with a write to InfluxDB in Stage 3
        print(f"Received from {turbine_id}: [Wind: {wind}m/s, RPM: {rpm}, Power: {power}kW, Temp: {temp}°C]")
    else:
        # The error is already logged inside parse_payload
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
        print(f"🔥 Failed to connect to broker: {e}")
        return None
    return client

def run_collector():
    """Starts the data collector."""
    client = setup_client()
    
    if client is None:
        print("Exiting program, client setup failed.")
        return
    
    print("🎧 Data collector is now listening for messages...")
    # loop_forever() is a blocking call that runs the network loop
    # and handles all incoming messages and callbacks automatically.
    client.loop_forever()

if __name__ == "__main__":
    try:
        run_collector()
    except KeyboardInterrupt:
        print("\n🛑 Collector stopped by user.")