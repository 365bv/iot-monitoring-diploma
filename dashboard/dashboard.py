import streamlit as st
import pandas as pd
import influxdb_client
import os
import altair as alt
import logging
from dotenv import load_dotenv
from typing import List

# --- (Fix: Silence InfluxDB/Pandas Warning) ---
import warnings
from influxdb_client.client.warnings import MissingPivotFunction
warnings.simplefilter("ignore", MissingPivotFunction)
# --- (End Fix) ---

# --- Load Config (from .env file) ---
load_dotenv()
INFLUX_URL = "http://database:8086"
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_ORG = os.getenv("INFLUX_ORG")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (dashboard) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- InfluxDB Connection ---
# Set up the client and query API
try:
    influx_client = influxdb_client.InfluxDBClient(
        url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG
    )
    query_api = influx_client.query_api()
    logging.info("✅ [InfluxDB] Successfully connected to InfluxDB for dashboard.")
except Exception as e:
    logging.error(f"🔥 [InfluxDB] Error connecting to InfluxDB: {e}")
    st.error(f"Error connecting to InfluxDB: {e}")

@st.cache_data(ttl=10) # Cache results for 10 seconds
def fetch_data(query: str) -> pd.DataFrame:
    """Queries InfluxDB and returns data as a Pandas DataFrame."""
    try:
        tables = query_api.query_data_frame(query=query, org=INFLUX_ORG)
        if isinstance(tables, List):
            if not tables:
                return pd.DataFrame() 
            return pd.concat(tables, ignore_index=True)
        return tables
    except Exception as e:
        logging.error(f"🔥 [InfluxDB] Error querying InfluxDB: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60) # Cache this list for 1 minute
def get_turbine_list() -> List[str]:
    """Fetches a unique list of turbine IDs from the database."""
    query = f'''
        import "influxdata/influxdb/schema"
        schema.tagValues(
            bucket: "{INFLUX_BUCKET}",
            tag: "turbine_id",
            predicate: (r) => r._measurement == "turbine_status",
            start: -30d
        )
    '''
    df = fetch_data(query)
    if not df.empty and '_value' in df.columns:
        return df['_value'].tolist()
    return [] 

# --- Build the Web Dashboard ---
st.set_page_config(page_title="Turbine Fleet Monitoring", layout="wide")
st.title("Turbine Fleet Real-Time Dashboard ⚡️", anchor=False)

# --- 1. Sidebar for Filters (Multi-Select) ---
st.header("Dashboard Filters", anchor=False)
turbine_list = get_turbine_list() # Get the clean list of turbines

# Use st.multiselect. Search functionality is built-in.
selected_turbines = st.multiselect(
    "Search turbines:",
    options=turbine_list,
    default=turbine_list[:3] if turbine_list else None,
    label_visibility="collapsed" # Hides the label "Search turbines..."
    )


# --- 2. Main Flux Query (Dynamic Filter Logic) ---

if not selected_turbines:
    # If the user deselected everything, show nothing.
    st.warning("Please select at least one turbine ID from the sidebar.")
    query_filter = "false" # Flux filter that returns nothing
else:
    # Build a list of filter conditions
    # e.g., ['r["turbine_id"] == "WT-01"', 'r["turbine_id"] == "WT-02"']
    filter_conditions = [f'r["turbine_id"] == "{tid}"' for tid in selected_turbines]
    
    # Join them with "or"
    # e.g., 'r["turbine_id"] == "WT-01" or r["turbine_id"] == "WT-02"'
    query_filter = " or ".join(filter_conditions)

# Build the final query, injecting our dynamic filter
flux_query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h) // Query data from the last 1 hour
      |> filter(fn: (r) => r["_measurement"] == "turbine_status")
      |> filter(fn: (r) => {query_filter})
      |> aggregateWindow(every: 10s, fn: max, createEmpty: false)
      |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
      |> drop(columns: ["_start", "_stop", "_measurement"])
'''

# --- 3. Fetch and Display Data ---
data_df = fetch_data(flux_query)

if not data_df.empty:
    # --- (FIX: Use Altair for better, colored charts) ---
    
    # We need _time to be a column, not an index, for Altair
    data_df_for_charts = data_df.reset_index()

    st.subheader("Power Output (kW)", anchor=False)
    # Create the Altair chart
    chart_power = alt.Chart(data_df_for_charts).mark_line(point=True).encode(
        x=alt.X('_time', title='Time'),
        y=alt.Y('power_output_kw', title='Power (kW)'),
        color=alt.Color('turbine_id', title='Turbine'), # <-- THE MAGIC
        tooltip=['_time', 'turbine_id', 'power_output_kw']
    ).interactive() # Make the chart zoomable/pannable
    st.altair_chart(chart_power, width='stretch')


    st.subheader("Gearbox Temperature (°C)", anchor=False)
    chart_temp = alt.Chart(data_df_for_charts).mark_line(point=True).encode(
        x=alt.X('_time', title='Time'),
        y=alt.Y('gearbox_temp_c', title='Temperature (°C)'),
        color=alt.Color('turbine_id', title='Turbine'), # <-- THE MAGIC
        tooltip=['_time', 'turbine_id', 'gearbox_temp_c']
    ).interactive()
    st.altair_chart(chart_temp, width='stretch')

    
    st.subheader("Rotor Speed (RPM)", anchor=False)
    chart_rpm = alt.Chart(data_df_for_charts).mark_line(point=True).encode(
        x=alt.X('_time', title='Time'),
        y=alt.Y('rotor_speed_rpm', title='RPM'),
        color=alt.Color('turbine_id', title='Turbine'),
        tooltip=['_time', 'turbine_id', 'rotor_speed_rpm']
    ).interactive()
    st.altair_chart(chart_rpm, width='stretch')

    st.subheader("Wind Speed (m/s)", anchor=False)
    chart_wind = alt.Chart(data_df_for_charts).mark_line(point=True).encode(
        x=alt.X('_time', title='Time'),
        y=alt.Y('wind_speed_ms', title='Wind Speed (m/s)'),
        color=alt.Color('turbine_id', title='Turbine'),
        tooltip=['_time', 'turbine_id', 'wind_speed_ms']
    ).interactive()
    st.altair_chart(chart_wind, width='stretch')

    # --- (END FIX) ---

    st.subheader("Aggregated Raw Data (Last 20 points)", anchor=False)
    table_df = data_df.drop(columns=['result', 'table'], errors='ignore')
    table_df = table_df.set_index("_time")
    st.dataframe(table_df.tail(20))
else:
    if selected_turbines:
        st.warning("No data found for the selected turbine(s) in this time range. Are the sensor and collector scripts running?")