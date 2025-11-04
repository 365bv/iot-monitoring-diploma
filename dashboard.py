import streamlit as st
import pandas as pd
import influxdb_client
import os
import warnings
from dotenv import load_dotenv
from typing import List
from influxdb_client.client.warnings import MissingPivotFunction

# This will silence ONLY that specific, annoying warning
warnings.simplefilter("ignore", MissingPivotFunction)

# --- Load Config ---
load_dotenv()
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# --- InfluxDB Connection ---
# Set up the client and query API
try:
    influx_client = influxdb_client.InfluxDBClient(
        url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG
    )
    query_api = influx_client.query_api()
    print("✅ [InfluxDB] Successfully connected to InfluxDB for dashboard.")
except Exception as e:
    print(f"🔥 [InfluxDB] Error connecting to InfluxDB: {e}")
    st.error(f"Error connecting to InfluxDB: {e}")

def fetch_data(query: str) -> pd.DataFrame:
    """Queries InfluxDB and returns data as a Pandas DataFrame."""
    try:
        # Execute the Flux query
        tables = query_api.query_data_frame(query=query, org=INFLUX_ORG)
        # InfluxDB can return multiple tables; we'll join them
        if isinstance(tables, List):
            if not tables:
                return pd.DataFrame() # Return empty if list is empty
            return pd.concat(tables, ignore_index=True)
        return tables
    except Exception as e:
        print(f"Error querying InfluxDB: {e}")
        return pd.DataFrame() # Return empty DataFrame on error

def get_turbine_list() -> List[str]:
    """Fetches a unique list of turbine IDs from the database."""
    query = f'''
        import "influxdata/influxdb/schema"
        schema.tagValues(
            bucket: "{INFLUX_BUCKET}",
            tag: "turbine_id",
            predicate: (r) => r._measurement == "turbine_status",
            start: -30d // Look for turbines active in the last 30 days
        )
    '''
    df = fetch_data(query)
    if not df.empty and '_value' in df.columns:
        return df['_value'].tolist()
    return [] # Return empty list if no turbines found

# --- Build the Web Dashboard ---
st.set_page_config(page_title="Turbine Fleet Monitoring", layout="wide")
st.title("Turbine Fleet Real-Time Dashboard ⚡️")

# --- 1. Sidebar for Filters (The "Magic" Part) ---
st.sidebar.header("Dashboard Filters")
turbine_list = ["All"] + get_turbine_list() # Add "All" option
selected_turbine = st.sidebar.selectbox(
    "Select Turbine ID:",
    options=turbine_list
)

# --- 2. Main Flux Query ---
# This query will be dynamically filtered by the sidebar selection
query_filter = f'r["turbine_id"] == "{selected_turbine}"'
if selected_turbine == "All":
    # If "All" is selected, we don't filter by a specific ID
    query_filter = 'true' # This means "include everything"

flux_query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h) // Query data from the last 1 hour
      |> filter(fn: (r) => r["_measurement"] == "turbine_status")
      |> filter(fn: (r) => {query_filter})
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> drop(columns: ["_start", "_stop", "_measurement"])
'''

# --- 3. Fetch and Display Data ---
data_df = fetch_data(flux_query)

if not data_df.empty:
    # Set the time as the index for plotting
    data_df = data_df.set_index("_time")
    
    st.header(f"Live Data for: {selected_turbine}")

    # Display line charts
    st.subheader("Power Output (kW)")
    st.line_chart(data_df, y="power_output_kw")

    st.subheader("Gearbox Temperature (°C)")
    st.line_chart(data_df, y="gearbox_temp_c")

    st.subheader("Rotor Speed (RPM) & Wind Speed (m/s)")
    st.line_chart(data_df, y=["rotor_speed_rpm", "wind_speed_ms"])

    # Display raw data in a table
    st.subheader("Raw Data (Last 20 points)")
    st.dataframe(data_df.tail(20)) # Show last 20 data points
else:
    st.warning("No data found for the selected time range. Are the sensor and collector scripts running?")