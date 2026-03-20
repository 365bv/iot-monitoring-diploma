# IIoT Wind Turbine Monitoring Pipeline

[![Python CI](https://github.com/365bv/iot-monitoring-diploma/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/365bv/iot-monitoring-diploma/actions/workflows/ci-cd.yml)

This repository contains the full source code for my Bachelor's Diploma project (KPI, 2026). It is a commercially-relevant prototype of an end-to-end Industrial IoT (IIoT) data pipeline, built to monitor the real-time health and performance of a wind turbine fleet.

The system simulates a fleet of 50 turbines, collects telemetry, stores it in a time-series database, and visualizes the data on an interactive web dashboard—all containerized with Docker.

![Streamlit Dashboard Screenshot](https://github.com/user-attachments/assets/3d8d71a6-a574-4650-b961-9d247f513158) 

## 🚀 Key Features

* **Microservice Architecture:** The entire system runs as a set of 6 containerized services using Docker Compose.
* **Realistic Data Simulation:** A Python script simulates a fleet of 50+ turbines, generating correlated data (wind speed, RPM, power output, temperature).
* **Scalable Data Transport:** Uses **MQTT (Mosquitto)** with wildcard topics, allowing the system to scale to thousands of sensors without code changes.
* **Real-Time Alerting:** A dedicated Python "watchdog" service (`alerter`) monitors the data stream for anomalies (e.g., high temperature) and logs critical alerts.
* **Time-Series Storage:** Utilizes **InfluxDB** as a high-performance database, optimized for high-volume, time-stamped telemetry data.
* **Interactive Web Dashboard:** A **Streamlit** app (written in pure Python) provides a filterable, real-time view of the fleet's health, replacing complex UI configuration.
* **Tested & Robust:** The data collection logic includes **unit tests (Pytest)** to ensure reliable data parsing and error handling.
* **Fully Automated CI/CD:** A **GitHub Actions** pipeline automatically:
    *  **CI:** Runs all **Pytest** unit tests on every push.
    *  **CD:** Builds and pushes new, production-ready Docker images to **Docker Hub** on every successful merge to `main`.

## 🛠️ Core Tech Stack

* **Application:** Python 3.12, Streamlit, Pandas, Altair
* **Infrastructure:** Docker & Docker Compose
* **Data Pipeline:** MQTT (Mosquitto), InfluxDB 2.7
* **Testing & DevOps:** Pytest, Pytest-Mock, GitHub Actions

## 🐳 Docker Hub Images

This project's CD pipeline automatically builds and publishes the following images:
* **Sensor Emulator:** `hub.docker.com/r/365bv/sensor-emulator`
* **Data Collector:** `hub.docker.com/r/365bv/data-collector`
* **Dashboard:** `hub.docker.com/r/365bv/dashboard`
* **Alerter:** `hub.docker.com/r/365bv/alerter`

## ⚙️ Project Architecture

This system is composed of 6 services managed by `docker-compose.yml`:

1.  **`sensor_emulator` (Python/Docker):** Simulates 50+ turbines, publishing JSON data to MQTT.
2.  **`mqtt_broker` (Mosquitto/Docker):** The message broker that routes all telemetry.
3.  **`data_collector` (Python/Docker):** Subscribes to the MQTT broker, parses data (validated by unit tests), and writes it to InfluxDB.
4.  **`database` (InfluxDB/Docker):** Stores all incoming time-series data.
5.  **`alerter` (Python/Docker):** Subscribes to MQTT and checks data against alert rules (e.g., high temperature).
6.  **`dashboard` (Streamlit/Docker):** The Python web app that queries InfluxDB (using Flux) and displays interactive charts (using Altair).

## ⚡ How to Run

The entire system is designed to run with a single command.

### Prerequisites

* Git
* Docker Desktop (must be running)

### 1. Clone the Repository

```sh
git clone https://github.com/365bv/iot-monitoring-diploma.git

cd iot-monitoring-diploma
```
### 2. Set Up Environment Variables

This project uses a .env file for configuration. A template is provided.

```sh
# 1. Copy the template file
cp .env.example .env

# 2. (Optional) Edit the .env file if you wish to change the default passwords/tokens.
# The default values will work out-of-the-box.

```
### 3. Build and Run the System

```sh
docker-compose up --build -d
```

## Dynamic MQTT QoS Configuration

To analyze network performance under different message reliability guarantees, you can dynamically set the MQTT Quality of Service (QoS) level at runtime.

### Launching with a Specific QoS Level

Use the following command to start the services with a specific QoS level, overriding the default value in the `.env` file. This example sets the QoS level to 2:

```bash
MQTT_QOS=2 docker-compose up -d
```

### Understanding MQTT Quality of Service (QoS)

MQTT QoS is a crucial feature that defines the guarantee of message delivery between a publisher (like our sensor emulator) and a subscriber (like our data collector) via the MQTT broker. The QoS level determines the reliability of the message transport, which directly impacts latency and network overhead.

- **QoS 0 (At most once):** This is the fastest delivery option, often called "fire and forget." Messages are sent without confirmation of receipt.
  - **Use Case:** Best for high-frequency, non-critical data where occasional message loss is acceptable. Minimizes latency and network traffic.
- **QoS 1 (At least once):** This level guarantees that a message will be delivered at least one time. The sender stores the message until it receives a confirmation (PUBACK packet) from the receiver. If no confirmation is received, the message is resent, which could result in duplicate messages.
  - **Use Case:** Suitable for important data where message loss is not an option, but duplicate processing can be handled.
- **QoS 2 (Exactly once):** This is the most reliable but also the slowest delivery level. It uses a four-part handshake to ensure the message is delivered exactly once, preventing both loss and duplication.
  - **Use Case:** Critical for systems where data integrity is paramount and duplicate messages would cause errors, such as financial transactions or, in our case, precise command-and-control signals for the turbine.

Testing with different QoS levels is vital for this project to quantify the trade-offs between message reliability, network latency, and system overhead in a simulated industrial IoT environment.

### 4. View the Dashboard

1. Wait about 30-60 seconds for all services to start and for data to begin flowing.

2. Open your browser and go to: http://localhost:8501 or http://0.0.0.0:8501

3. You will see the live dashboard.

## Other Service:

* InfluxDB UI: http://localhost:8086 (Login with credentials from .env file)

* MQTT Broker: localhost:1883

## How to Stop the System:

```sh
docker-compose down
```
## 🧪 Running Tests

 To run the unit tests for the data collector:

### Set up the local Python environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
### Run pytest:

```sh
pytest
```
## 📄 License
This project is licensed under the MIT License.