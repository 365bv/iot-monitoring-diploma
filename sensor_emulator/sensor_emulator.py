import paho.mqtt.client as mqtt
import time
import random
import json
import logging
from typing import Optional, Dict

# --- Settings ---
BROKER_ADDRESS = "mqtt_broker"
PORT = 1883
TURBINE_IDS = [f"WT-{i:02d}" for i in range(1, 51)]
TOPIC_PREFIX = "norway/energy/wind-turbine"

# --- Simulation Constants ---
BASE_TEMP_C = 60.0
MAX_WIND_SPEED_MS = 25.0
MIN_WIND_SPEED_MS = 5.0
ANOMALY_CHANCE = 0.0015

# --- Logic ---

def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Callback function executed when the client connects to the broker."""
    if rc == 0:
        logging.info(f"✅ Successfully connected to broker {BROKER_ADDRESS}")
        # Signal the main loop that we are connected
        client.connected_flag = True
    else:
        logging.error(f"❌ Connection failed with code: {rc}")
        client.loop_stop() # Stop the loop if connection failed

def on_disconnect(client: mqtt.Client, userdata, rc: int):
    """Callback executed when the client disconnects."""
    logging.warning(f"🔌 Disconnected from broker with code: {rc}")
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
        logging.error(f"🔥 Failed to connect to broker: {e}")
        return None
    return client

def run_emulator():
    """Main loop for the sensor emulator."""
    client = setup_client()
    
    if client is None:
        logging.critical("Exiting program, client setup failed.")
        return

    logging.info("⏳ Attempting to connect...")
    while not client.connected_flag:
        # Wait for the on_connect callback to set the flag
        time.sleep(1) 

    logging.info(f"🚀 Sensor fleet emulator started. Publishing data for {len(TURBINE_IDS)} turbines.")

    fleet_state = {
        turbine_id: {"wind_speed_ms": random.uniform(MIN_WIND_SPEED_MS, MAX_WIND_SPEED_MS)}
        for turbine_id in TURBINE_IDS
    }
    
    try:
        while True:
            for turbine_id in TURBINE_IDS:
                
                # --- Simulate smooth data changes ---
                current_wind_speed = fleet_state[turbine_id]["wind_speed_ms"]
                
                wind_change = random.uniform(-0.5, 0.5)
                new_wind_speed = round(current_wind_speed + wind_change, 2)
                
                new_wind_speed = max(MIN_WIND_SPEED_MS, min(new_wind_speed, MAX_WIND_SPEED_MS))

                fleet_state[turbine_id]["wind_speed_ms"] = new_wind_speed
                
                # Calculate other KPIs based on new wind speed
                rotor_speed = round((new_wind_speed * 0.8) + random.uniform(-0.5, 0.5), 2) 
                power_output_raw = (rotor_speed * 100) + random.uniform(-50, 50)
                power_output = round(max(0, power_output_raw), 0)
                gearbox_temp = round(BASE_TEMP_C + (power_output / 100) + random.uniform(-1, 1), 2)
                
                is_anomaly = False
                
                # --- Introduce rare anomalies ---
                if random.random() < ANOMALY_CHANCE:
                    logging.warning(f"🚨 Generating ANOMALY for {turbine_id}!")
                    is_anomaly = True
                    # Overwrite normal temp with a critical, overheating value
                    gearbox_temp = round(random.uniform(90.0, 105.0), 2)
                    
                payload = json.dumps({
                    "turbine_id": turbine_id,
                    "wind_speed_ms": new_wind_speed,
                    "rotor_speed_rpm": rotor_speed,
                    "power_output_kw": power_output,
                    "gearbox_temp_c": gearbox_temp,
                    "timestamp": int(time.time()),
                    "is_anomaly": is_anomaly
                })
                
                topic = f"{TOPIC_PREFIX}/{turbine_id}/status"
                
                result = client.publish(topic, payload)
                
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    logging.warning(f"⚠️ Failed to send message for {turbine_id} (code: {result.rc})")

            # Wait 5 seconds before the next cycle
            logging.info(f"--- Cycle complete ({len(TURBINE_IDS)} messages sent), sleeping for 5 seconds ---")
            time.sleep(5)
            
    except KeyboardInterrupt:
        logging.info("🛑 Emulator stopped by user.")
    finally:
        if client.connected_flag:
            client.disconnect()
        client.loop_stop()

# --- Start ---
if __name__ == "__main__":
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (sensor_emulator) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    run_emulator()