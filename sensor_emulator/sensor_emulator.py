import paho.mqtt.client as mqtt
import time
import random
import json
import os
import logging
import threading
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# --- Settings ---
BROKER_ADDRESS = "mqtt_broker"
PORT = 1883
TURBINE_IDS = [f"WT-{i:02d}" for i in range(1, 51)]
TOPIC_PREFIX = "norway/energy/wind-turbine"
QOS_LEVEL = int(os.getenv("MQTT_QOS", "0"))

# --- Simulation Constants ---
BASE_TEMP_C = 60.0
MAX_WIND_SPEED_MS = 25.0
MIN_WIND_SPEED_MS = 5.0
ANOMALY_CHANCE = 0.0015

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s ) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Logic for a single turbine thread ---

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Callback function executed when the client connects to the broker."""
    if rc == 0:
        logging.info(f"✅ MQTT Client for {userdata['turbine_id']} connected (QoS: {QOS_LEVEL})")
        client.connected_flag = True
    else:
        logging.error(f"❌ ({userdata['turbine_id']}) Connection failed with code: {rc}")
        client.loop_stop() # Stop the loop if connection failed

def on_disconnect(client: mqtt.Client, userdata, rc: int):
    """Callback executed when the client disconnects."""
    logging.warning(f"🔌 MQTT Client for {userdata['turbine_id']} disconnected.")
    client.connected_flag = False

def setup_client(turbine_id: str) -> Optional[mqtt.Client]:
    """Creates a seperate client connection for each thread."""
    
    # Each thread needs its own client object
    mqtt.Client.connected_flag = False
    client = mqtt.Client(userdata={"turbine_id": turbine_id})
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        client.loop_start() # Starts a background thread to handle network loops
    except Exception as e:
        logging.error(f"🔥 ({turbine_id}) Failed to connect to broker: {e}")
        return None
    return client

def run_single_turbine_emulator(turbine_id: str):
    """
    Main loop for a single turbine. This function will be run
    in its own dedicated thread.
    """
    client = setup_client(turbine_id)
    
    if client is None:
        return # Thread exits if client setup failed

    logging.info(f"⏳ ({turbine_id}) Attempting to connect...")
    while not client.connected_flag:
        # Wait for the on_connect callback to set the flag
        time.sleep(1) 

    logging.info(f"🚀 ({turbine_id}) Emulator started.")
    
    current_wind_speed = random.uniform(MIN_WIND_SPEED_MS, MAX_WIND_SPEED_MS)
    
    try:
        while True:
            
            # --- Simulate smooth data changes ---
            wind_change = random.uniform(-0.5, 0.5)
            new_wind_speed = round(current_wind_speed + wind_change, 2)
            new_wind_speed = max(MIN_WIND_SPEED_MS, min(new_wind_speed, MAX_WIND_SPEED_MS))
            current_wind_speed = new_wind_speed # Update for next iteration
            
            # Calculate other KPIs based on new wind speed
            rotor_speed = round((new_wind_speed * 0.8) + random.uniform(-0.5, 0.5), 2) 
            power_output_raw = (rotor_speed * 100) + random.uniform(-50, 50)
            power_output = round(max(0, power_output_raw), 0)
            gearbox_temp = round(BASE_TEMP_C + (power_output / 100) + random.uniform(-1, 1), 2)
            is_anomaly = False
            
            # --- Introduce rare anomalies ---
            if random.random() < ANOMALY_CHANCE:
                logging.warning(f"🚨 ({turbine_id}) Generating ANOMALY!")
                is_anomaly = True
                # Overwrite normal temp with a critical, overheating value
                gearbox_temp = round(random.uniform(90.0, 105.0), 2)
                
            payload = json.dumps({
                "turbine_id": turbine_id,
                "wind_speed_ms": new_wind_speed,
                "rotor_speed_rpm": rotor_speed,
                "power_output_kw": power_output,
                "gearbox_temp_c": gearbox_temp,
                "timestamp_ns": time.time_ns(),
                "is_anomaly": is_anomaly
            })
            
            topic = f"{TOPIC_PREFIX}/{turbine_id}/status"
            result = client.publish(topic, payload, qos=QOS_LEVEL)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logging.warning(f"⚠️ ({turbine_id}) Failed to send message (code: {result.rc})")
                
            # Wait 5 seconds before the next cycle 
            time.sleep(5)
            
    except KeyboardInterrupt:
        pass # The main thread will handle the stop
    finally:
        if client.connected_flag:
            client.disconnect()
        client.loop_stop()
        logging.info(f"🛑 ({turbine_id}) Emulator stopped.")

# --- Start ---
if __name__ == "__main__":
    
    logging.info(f"Starting Sensor Emulator for {len(TURBINE_IDS)} turbines...")
    
    threads = []
    
    for turbine_id in TURBINE_IDS:
        # Create a new thread for each turbine
        thread = threading.Thread(
            target=run_single_turbine_emulator,
            args=(turbine_id,),
            name=f"Turbine-{turbine_id}"
        )
        threads.append(thread)
        thread.start()
        time.sleep(0.1) # Stagger the start of each thread slightly
    
    
    try:
        # Keep the main thread alive, waiting for KeyboardInterrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("\n🛑 Main process received stop signal. Shutting down all threads...")
        
    logging.info("--- Emulator shutdown complete ---")