# IIoT Wind Turbine Monitoring Pipeline

[![Python CI](https://github.com/365bv/iot-monitoring-diploma/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/365bv/iot-monitoring-diploma/actions/workflows/ci-cd.yml)

This repository contains the full source code for my Bachelor's Diploma project (KPI, 2026). It is a commercially-relevant prototype of an end-to-end Industrial IoT (IIoT) data pipeline, built to monitor the real-time health and performance of a wind turbine fleet.

The system simulates a fleet of 50 turbines, collects telemetry, stores it in a time-series database, and visualizes the data on an interactive web dashboard—all containerized with Docker.

![Streamlit Dashboard Screenshot](https://github.com/user-attachments/assets/3d8d71a6-a574-4650-b961-9d247f513158) 

## 🚀 Key Features

* **Microservice Architecture:** The entire system runs as a set of 5 containerized services using Docker Compose.
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

This system is composed of 5 services managed by `docker-compose.yml`:

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