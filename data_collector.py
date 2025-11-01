import paho.mqtt.client as mqtt
import json
from typing import Optional

# --- Settings ---
# We MUST connect to the same broker as the emulator
BROKER_ADDRESS = "broker.hivemq.com" 
PORT = 1883
# This is the wildcard topic to subscribe to
MQTT_TOPIC = "norway/energy/wind-turbine/+/status"

# --- Logic ---

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Callback for when the client connects."""
    if rc == 0:
        print(f"✅ Successfully connected to broker {BROKER_ADDRESS}")
        # Subscribe to the topic AFTER connection is established
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"❌ Connection failed with code: {rc}")

def on_subscribe(client: mqtt.Client, userdata, mid, granted_qos):
    """Callback for when the client successfully subscribes to a topic."""
    print(f"🔔 Subscribed to topic: {MQTT_TOPIC}")

def on_message(client: mqtt.Client, userdata, msg: mqtt.MQTTMessage):
    """Callback for when a message is received from the broker."""
    # msg.payload is in bytes, so we decode it to a string
    # Then we parse the string (JSON) into a Python dictionary
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        turbine_id = data.get("turbine_id", "Unknown")
        temp = data.get("gearbox_temp_c", "N/A")
        vibration = data.get("vibration_hz", "N/A")
        
        print(f"Received data from {turbine_id}: [Temp: {temp}°C, Vibration: {vibration}Hz]")
    
    except json.JSONDecodeError:
        print(f"⚠️ Received malformed JSON: {msg.payload.decode('utf-8')}")
    except Exception as e:
        print(f"🔥 An error occurred in on_message: {e}")

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
    
    # loop_forever() is a blocking call.
    # It runs the client's network loop continuously to listen for messages.
    # It will run until the program is stopped (e.g., CTRL+C).
    print("🎧 Data collector is now listening for messages...")
    client.loop_forever()

# --- Start ---
if __name__ == "__main__":
    try:
        run_collector()
    except KeyboardInterrupt:
        print("\n🛑 Collector stopped by user.")