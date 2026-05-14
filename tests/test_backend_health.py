import pytest
import paho.mqtt.client as mqtt
import json
import time
from influxdb_client import InfluxDBClient
import os
import socket
from dotenv import load_dotenv

load_dotenv()

# Constants
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "secret-token")
INFLUX_ORG = os.getenv("INFLUX_ORG", "Turbine-Monitoring-Project")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "turbine_data")

CONTROL_TOPIC = "sim/control/turbine_count"
TELEMETRY_TOPIC = "norway/energy/wind-turbine/+/status"


def is_service_running(host, port):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


BACKEND_RUNNING = is_service_running(MQTT_BROKER, MQTT_PORT) and is_service_running(
    "localhost", 8086
)
pytestmark = pytest.mark.skipif(
    not BACKEND_RUNNING, reason="Backend services are not running"
)


@pytest.fixture
def mqtt_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    yield client
    client.disconnect()
    client.loop_stop()


@pytest.fixture
def influx_client():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    yield client
    client.close()


def test_mqtt_connection_and_subscription(mqtt_client):
    """Test 1 (MQTT): Check connection and ability to subscribe."""
    messages = []

    def on_message(client, userdata, msg):
        messages.append(msg)

    mqtt_client.on_message = on_message
    result, _ = mqtt_client.subscribe(TELEMETRY_TOPIC)

    assert result == mqtt.MQTT_ERR_SUCCESS, "Failed to subscribe to telemetry topic"


def test_influxdb_connection(influx_client):
    """Test 2 (InfluxDB): Check connection and bucket existence."""
    assert influx_client.ping() is True, (
        "InfluxDB health check failed: ping unsuccessful"
    )

    buckets_api = influx_client.buckets_api()
    bucket = buckets_api.find_bucket_by_name(INFLUX_BUCKET)
    assert bucket is not None, f"Bucket '{INFLUX_BUCKET}' not found"


def test_dynamic_scaling(mqtt_client):
    """Test 3 (Emulator): Check dynamic scaling via control topic."""
    received_turbines = set()

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            received_turbines.add(payload.get("turbine_id"))
        except Exception:
            pass

    mqtt_client.on_message = on_message
    mqtt_client.subscribe(TELEMETRY_TOPIC)

    # Send control message to scale to 3 turbines
    payload = json.dumps({"count": 3})
    mqtt_client.publish(CONTROL_TOPIC, payload)

    # Wait for the scaling to take effect and messages to arrive
    time.sleep(8)

    # Assert that we are receiving data only from WT-01, WT-02, WT-03
    assert len(received_turbines) > 0, "No telemetry received after scaling"
    for t_id in received_turbines:
        assert int(t_id.split("-")[1]) <= 3, (
            f"Received data from unexpected turbine: {t_id}"
        )
