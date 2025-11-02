# Industrial IoT (IIoT) Data Pipeline for Energy Monitoring

This is the repository for my Bachelor's Diploma project (KPI, 2026).

The goal is to build a **commercially-relevant prototype** of an **Industrial IoT (IIoT) data pipeline**. This system simulates, collects, stores, and visualizes real-time status data (like vibration and temperature) from a **wind turbine fleet**, a use case directly applicable to the Norwegian energy sector.

## Core Tech Stack

* **Python** (for data producers/emulators and consumers)
* **MQTT** (for data transport)
* **InfluxDB** (for time-series data storage)
* **Grafana** (for data visualization and dashboards)
* **Docker** & **Docker Compose** (for containerization and deployment)

## Project Architecture

This system is built using a microservice architecture and is designed to run entirely within Docker Compose.

1.  **Sensor Emulator (`sensor_emulator.py`):** A Python script that simulates a fleet of 50+ wind turbines. Every 5 seconds, it generates realistic data (vibration, temperature) and publishes it as JSON payloads to unique MQTT topics (e.g., `norway/energy/wind-turbine/WT-01/status`).

2.  **MQTT Broker (`Mosquitto`):** A lightweight, containerized broker that receives all messages from the sensor fleet and routes them to any subscribed consumers.

3.  **Data Collector (`data_collector.py`):** A separate Python consumer script that subscribes to the MQTT broker using a wildcard topic (`norway/energy/wind-turbine/+/status`). It receives the JSON data from *all* turbines, parses it, and writes it in batches to the database.

4.  **Database (`InfluxDB`):** A high-performance time-series database, running in its own container, designed to store millions of data points from the monitoring system efficiently.

5.  **Visualization (`Grafana`):** A containerized Grafana instance connected directly to InfluxDB. It provides a real-time dashboard to monitor the entire fleet's health, with the ability to filter by individual turbine.


## How to Run

1.  **Clone the repository**
    ```sh
    git clone [your-repo-url]
    cd iot-monitoring-diploma
    ```

2.  **Set up Environment Variables**
    This project uses a `.env` file for configuration. A template is provided.
    ```sh
    # 1. Copy the template file
    cp .env.example .env
    
    # 2. Edit the .env file and set your own passwords/tokens
    # nano .env 
    ```

3.  **Run the System**
    ```sh
    docker-compose up -d
    ```

4.  **(In a separate terminal) Start the Sensor Emulator**
    ```sh
    # 1. Activate virtual environment
    source .venv/bin/activate
    # 2. Run the script
    python sensor_emulator.py
    ```

5.  **(In a third terminal) Start the Data Collector**
    ```sh
    # 1. Activate virtual environment
    source .venv/bin/activate
    # 2. Run the script
    python data_collector.py
    ```

    
## Project Status

*(This project is currently in development. **Stage 3: Database & Local Infrastructure (Docker)**)*