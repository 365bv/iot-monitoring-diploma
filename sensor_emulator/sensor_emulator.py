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
INITIAL_TURBINE_COUNT = int(os.getenv("INITIAL_TURBINE_COUNT", "5"))
TOPIC_PREFIX = "norway/energy/wind-turbine"
CONTROL_TOPIC = "sim/control/turbine_count"
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
    datefmt="%Y-%m-%d %H:%M:%S",
)

# --- Global State ---
active_turbines: Dict[str, threading.Event] = {}
turbines_lock = threading.Lock()

# --- Logic for a single turbine thread ---


def on_connect(client: mqtt.Client, userdata, flags, rc: int):
    """Callback function executed when the client connects to the broker."""
    if rc == 0:
        logging.info(
            f"✅ MQTT Client for {userdata['turbine_id']} connected (QoS: {QOS_LEVEL})"
        )
        client.connected_flag = True
    else:
        logging.error(
            f"❌ ({userdata['turbine_id']}) Connection failed with code: {rc}"
        )
        client.loop_stop()  # Stop the loop if connection failed


def on_disconnect(client: mqtt.Client, userdata, rc: int):
    """Callback executed when the client disconnects."""
    logging.warning(f"🔌 MQTT Client for {userdata['turbine_id']} disconnected.")
    client.connected_flag = False


def setup_client(turbine_id: str) -> Optional[mqtt.Client]:
    """Creates a seperate client connection for each thread."""
    mqtt.Client.connected_flag = False
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1, userdata={"turbine_id": turbine_id}
    )
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        client.loop_start()  # Starts a background thread to handle network loops
    except Exception as e:
        logging.error(f"🔥 ({turbine_id}) Failed to connect to broker: {e}")
        return None
    return client


def run_single_turbine_emulator(turbine_id: str, stop_event: threading.Event):
    """
    Main loop for a single turbine. This function will be run
    in its own dedicated thread.
    """
    client = setup_client(turbine_id)

    if client is None:
        return  # Thread exits if client setup failed

    logging.info(f"⏳ ({turbine_id}) Attempting to connect...")
    # Wait for the on_connect callback to set the flag, or until stop event is set
    while not client.connected_flag and not stop_event.is_set():
        time.sleep(1)

    if stop_event.is_set():
        client.disconnect()
        client.loop_stop()
        return

    logging.info(f"🚀 ({turbine_id}) Emulator started.")

    current_wind_speed = random.uniform(MIN_WIND_SPEED_MS, MAX_WIND_SPEED_MS)

    try:
        while not stop_event.is_set():
            # --- Simulate smooth data changes ---
            wind_change = random.uniform(-0.5, 0.5)
            new_wind_speed = round(current_wind_speed + wind_change, 2)
            new_wind_speed = max(
                MIN_WIND_SPEED_MS, min(new_wind_speed, MAX_WIND_SPEED_MS)
            )
            current_wind_speed = new_wind_speed  # Update for next iteration

            # Calculate other KPIs based on new wind speed
            rotor_speed = round((new_wind_speed * 0.8) + random.uniform(-0.5, 0.5), 2)
            power_output_raw = (rotor_speed * 100) + random.uniform(-50, 50)
            power_output = round(max(0, power_output_raw), 0)
            gearbox_temp = round(
                BASE_TEMP_C + (power_output / 100) + random.uniform(-1, 1), 2
            )
            is_anomaly = False

            # --- Introduce rare anomalies ---
            if random.random() < ANOMALY_CHANCE:
                logging.warning(f"🚨 ({turbine_id}) Generating ANOMALY!")
                is_anomaly = True
                # Overwrite normal temp with a critical, overheating value
                gearbox_temp = round(random.uniform(90.0, 105.0), 2)

            payload = json.dumps(
                {
                    "turbine_id": turbine_id,
                    "wind_speed_ms": new_wind_speed,
                    "rotor_speed_rpm": rotor_speed,
                    "power_output_kw": power_output,
                    "gearbox_temp_c": gearbox_temp,
                    "timestamp_ns": time.time_ns(),
                    "is_anomaly": is_anomaly,
                }
            )

            topic = f"{TOPIC_PREFIX}/{turbine_id}/status"
            result = client.publish(topic, payload, qos=QOS_LEVEL)

            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logging.warning(
                    f"⚠️ ({turbine_id}) Failed to send message (code: {result.rc})"
                )

            # Wait 5 seconds before the next cycle or until stop event
            stop_event.wait(5)

    except Exception as e:
        logging.error(f"Error in {turbine_id}: {e}")
    finally:
        if getattr(client, "connected_flag", False):
            client.disconnect()
        client.loop_stop()
        logging.info(f"🛑 ({turbine_id}) Emulator stopped.")


def set_turbine_count(target_count: int):
    with turbines_lock:
        current_count = len(active_turbines)
        if target_count == current_count:
            return

        logging.info(
            f"🔄 Adjusting turbine count from {current_count} to {target_count}"
        )

        if target_count > current_count:
            # Add turbines
            for i in range(current_count + 1, target_count + 1):
                turbine_id = f"WT-{i:02d}"
                stop_event = threading.Event()
                active_turbines[turbine_id] = stop_event

                thread = threading.Thread(
                    target=run_single_turbine_emulator,
                    args=(turbine_id, stop_event),
                    name=f"Turbine-{turbine_id}",
                )
                thread.start()
                time.sleep(0.05)  # Stagger start slightly
        else:
            # Remove turbines
            # We want to remove the ones with highest ID first
            sorted_turbines = sorted(active_turbines.keys(), reverse=True)
            turbines_to_remove = sorted_turbines[: (current_count - target_count)]

            for t_id in turbines_to_remove:
                active_turbines[t_id].set()  # Signal thread to stop
                del active_turbines[t_id]


# --- Control MQTT Client Logic ---
def on_control_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        if "count" in payload:
            target_count = int(payload["count"])
            target_count = max(0, target_count)  # Prevent negative

            # Spin up a new thread to handle scaling so we don't block the MQTT loop
            threading.Thread(
                target=set_turbine_count,
                args=(target_count,),
                daemon=True,
                name="TurbineScaler",
            ).start()

    except Exception as e:
        logging.error(f"Failed to process control message: {e}")


def setup_control_client():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION1, userdata={"turbine_id": "ControlNode"}
    )
    client.on_message = on_control_message

    try:
        client.connect(BROKER_ADDRESS, PORT, 60)
        client.subscribe(CONTROL_TOPIC, qos=QOS_LEVEL)
        client.loop_start()
        logging.info(f"✅ Control node connected and subscribed to {CONTROL_TOPIC}")
        return client
    except Exception as e:
        logging.error(f"🔥 Control node failed to connect: {e}")
        return None


# --- Start ---
if __name__ == "__main__":
    logging.info(f"Starting Sensor Emulator. Initial count: {INITIAL_TURBINE_COUNT}")

    control_client = setup_control_client()

    # Initialize initial turbines
    set_turbine_count(INITIAL_TURBINE_COUNT)

    try:
        # Keep the main thread alive, waiting for KeyboardInterrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info(
            "\n🛑 Main process received stop signal. Shutting down all threads..."
        )
        with turbines_lock:
            for t_id, stop_event in active_turbines.items():
                stop_event.set()
    finally:
        if control_client:
            control_client.disconnect()
            control_client.loop_stop()
        logging.info("--- Emulator shutdown complete ---")
