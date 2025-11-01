import paho.mqtt.client as mqtt
import time
import random
import json
from typing import Optional

# --- Settings ---
BROKER_ADDRESS = "test.mosquitto.org" # Public MQTT broker for testing
PORT = 1883
# A unique topic to avoid conflicts with other users on the public broker.
MQTT_TOPIC = "norway/energy/wind-turbine/WT-07/status" 

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
    
    # We add a custom flag to the client class itself,
    # so we can access it inside the callbacks.
    mqtt.Client.connected_flag = False
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        client.loop_start()  # Starts a background thread to handle network loops
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

    # --- FIX ---
    # We now wait here until the on_connect callback has set
    # the connected_flag to True.
    print("⏳ Attempting to connect...")
    while not client.connected_flag:
        # Wait 1 second for the connection to establish
        time.sleep(1) 
    
    # --- END FIX ---
    # This code will only run AFTER the connection is successful.
    print(f"🚀 Sensor emulator started. Publishing data to topic: {MQTT_TOPIC}")
    print("Press CTRL+C to stop.")

    try:
        while True:
            
            # 1. Generate fake data
            # Simulate vibration frequency (Hz) and gearbox temperature (Celsius)
            vibration = round(random.uniform(0.5, 2.5), 3) # Normal vibration
            gearbox_temp = round(random.uniform(55.0, 70.0), 2) # Normal op temp

            # 2. Format data as JSON (best practice)
            payload = json.dumps({
                "turbine_id": "WT-07",
                "vibration_hz": vibration,
                "gearbox_temp_c": gearbox_temp,
                "timestamp": int(time.time()) # Add a Unix timestamp
            })
            
            # 3. Publish the data
            result = client.publish(MQTT_TOPIC, payload)
            
            # Check if the message was sent successfully
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📩 Sent turbine data: {payload}")
            else:
                print(f"⚠️ Failed to send message, code: {result.rc}")

            # 4. Wait for 5 seconds
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n🛑 Emulator stopped by user.")
    finally:
        if client.connected_flag:
            client.disconnect()
        client.loop_stop() # Stop the network loop

# --- Start ---
if __name__ == "__main__":
    run_emulator()