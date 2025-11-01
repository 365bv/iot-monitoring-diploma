import paho.mqtt.client as mqtt
import time
import random
import json
from typing import Optional

# --- Settings ---
BROKER_ADDRESS = "broker.hivemq.com" # Using a public broker for testing
PORT = 1883
TURBINE_IDS = [f"WT-{i:02d}" for i in range(1, 51)]
TOPIC_PREFIX = "norway/energy/wind-turbine"

# --- Logic ---

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Callback function executed when the client connects to the broker."""
    if rc == 0:
        print(f"✅ Successfully connected to broker {BROKER_ADDRESS}")
        # Signal the main loop that we are connected
        client.connected_flag = True
    else:
        print(f"❌ Connection failed with code: {rc}")
        client.loop_stop() # Stop the loop if connection failed

def on_disconnect(client: mqtt.Client, userdata, rc: int):
    """Callback executed when the client disconnects."""
    print(f"🔌 Disconnected from broker with code: {rc}")
    client.connected_flag = False

def setup_client() -> Optional[mqtt.Client]:
    """Creates, configures, and connects the MQTT client."""
    
    # Add a custom flag to the client class to track connection status
    mqtt.Client.connected_flag = False
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        client.loop_start() # Starts a background thread to handle network loops
    except Exception as e:
        print(f"🔥 Failed to connect to broker: {e}")
        return None
    return client

def run_emulator():
    """Main loop for the sensor emulator."""
    client = setup_client()
    
    if client is None:
        print("Exiting program, client setup failed.")
        return

    print("⏳ Attempting to connect...")
    while not client.connected_flag:
        # Wait for the on_connect callback to set the flag
        time.sleep(1) 
    
    print(f"🚀 Sensor fleet emulator started. Publishing data for {len(TURBINE_IDS)} turbines.")
    print("Press CTRL+C to stop.")

    try:
        while True:
            for turbine_id in TURBINE_IDS:
                
                vibration = round(random.uniform(0.5, 2.5), 3)
                gearbox_temp = round(random.uniform(55.0, 70.0), 2)
                
                payload = json.dumps({
                    "turbine_id": turbine_id,
                    "vibration_hz": vibration,
                    "gearbox_temp_c": gearbox_temp,
                    "timestamp": int(time.time())
                })
                
                topic = f"{TOPIC_PREFIX}/{turbine_id}/status"
                
                result = client.publish(topic, payload)
                
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"📩 Sent data for {turbine_id} to {topic}")
                else:
                    print(f"⚠️ Failed to send message for {turbine_id} (code: {result.rc})")

            print("--- Cycle complete, sleeping for 5 seconds ---")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Emulator stopped by user.")
    finally:
        if client.connected_flag:
            client.disconnect()
        client.loop_stop()

# --- Start ---
if __name__ == "__main__":
    run_emulator()