# Industrial IoT (IIoT) Data Pipeline for Energy Monitoring

This is the repository for my Bachelor's Diploma project (KPI, 2026).

The goal is to build a **commercially-relevant prototype** of an **Industrial IoT (IIoT) data pipeline**. This system simulates, collects, stores, and visualizes real-time status data from a **wind turbine fleet**, a use case directly applicable to the Norwegian energy sector.

## Core Tech Stack

* **Python** (for data producers, consumers, and dashboarding)
* **Streamlit** (for the web dashboard)
* **Pandas** (for data manipulation)
* **MQTT** (for data transport)
* **InfluxDB** (for time-series data storage)
* **Docker** & **Docker Compose** (for containerization and deployment)

## Project Architecture

This system is built using a microservice architecture. The core infrastructure (broker, database) runs via Docker Compose, while the Python scripts interact with it.

1.  **Sensor Emulator (`sensor_emulator.py`):** A Python script that simulates a fleet of 50+ wind turbines, publishing real-time KPIs (wind speed, RPM, power output, temp) as JSON payloads to unique MQTT topics.

2.  **MQTT Broker (`Mosquitto`):** A lightweight, containerized broker that routes messages from all sensors.

3.  **Data Collector (`data_collector.py`):** A Python consumer script that subscribes to all sensor topics (using a wildcard). It parses the data, validates it (using unit tests), and writes it efficiently to the InfluxDB database.

4.  **Database (`InfluxDB`):** A high-performance time-series database running in Docker, storing all incoming telemetry.

5.  **Visualization (`dashboard.py`):** A **Streamlit** web application written entirely in Python. It queries the InfluxDB database (using Flux and `aggregateWindow` for optimization) and displays interactive, auto-refreshing charts and data tables for the entire fleet or individual turbines.

## Project Status

*(This project is currently in development. **Stage 5: Full Containerization (Dockerizing Python apps)**)*