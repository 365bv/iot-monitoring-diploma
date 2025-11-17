"""
Unit tests for the data_collector.py script.
Uses pytest and pytest-mock.
"""

import json
import pytest
import time
from data_collector.data_collector import parse_payload, write_to_influxdb_async
from influxdb_client import Point

TEST_TIMESTAMP_NS = time.time_ns()

def test_parse_payload_success():
    """
    Tests the "happy path" with a valid wind turbine payload.
    """
    # Prepare
    valid_data = {
        "turbine_id": "WT-01",
        "wind_speed_ms": 12.5,
        "rotor_speed_rpm": 10.1,
        "power_output_kw": 1500,
        "gearbox_temp_c": 65.7,
        "timestamp_ns": TEST_TIMESTAMP_NS
    }
    payload_bytes = json.dumps(valid_data).encode("utf-8")
    
    # Act
    result = parse_payload(payload_bytes)
    
    # Assert
    assert result is not None
    assert result == valid_data
    assert result["turbine_id"] == "WT-01"
    assert result["power_output_kw"] == 1500
    assert result["timestamp_ns"] == TEST_TIMESTAMP_NS

def test_parse_payload_bad_json():
    """
    Tests the "failure path" with a malformed JSON payload.
    """
    # Prepare: Create a broken payload (missing closing bracket)
    # Using the *new* data structure for consistency.
    payload_bytes = b'{"turbine_id": "WT-01", "wind_speed_ms": 12.5'
    
    # Act
    result = parse_payload(payload_bytes)
    
    # Assert
    assert result is None

def test_parse_payload_not_json():
    """
    Tests the "failure path" with a payload that isn't JSON at all.
    """
    # Prepare
    payload_bytes = b'This is just a random string'
    
    # Act
    result = parse_payload(payload_bytes)
    
    # Assert
    assert result is None

def test_parse_payload_empty():
    """
    Tests an edge case with an empty payload.
    """
    # Prepare
    payload_bytes = b''
    
    # Act
    result = parse_payload(payload_bytes)
    
    # Assert
    assert result is None
    
def test_write_to_influxdb_happy_path(mocker):
    """
    Tests that write_to_influxdb correctly calls the
    InfluxDB write_api with a full, valid data object.
    """
    # Prepare
    mock_write_api = mocker.MagicMock()
    
    test_sent_time = time.time_ns() - 1000
    
    sample_data = {
        "turbine_id": "WT-TEST-01",
        "wind_speed_ms": 15.0,
        "rotor_speed_rpm": 12.5,
        "power_output_kw": 2000,
        "gearbox_temp_c": 70.1,
        "timestamp_ns": test_sent_time
    }

    # Act
    write_to_influxdb_async(mock_write_api, sample_data)

    # Assert
    mock_write_api.write.assert_called_once()
    
    call_args = mock_write_api.write.call_args
    point_as_string = call_args.kwargs["record"].to_line_protocol()
    
    assert "turbine_status" in point_as_string
    assert "turbine_id=WT-TEST-01" in point_as_string
    assert "power_output_kw=2000" in point_as_string
    assert str(test_sent_time) in point_as_string
    
def test_write_to_influxdb_partial_data(mocker):
    """
    Tests that the function handles a payload missing some optional fields
    without crashing.
    """
    # Prepare
    mock_write_api = mocker.MagicMock()
    partial_data = {
        "turbine_id": "WT-TEST-02",
        "power_output_kw": 1800,
        "gearbox_temp_c": 68.0,
        "timestamp_ns": TEST_TIMESTAMP_NS
    }

    # Act
    write_to_influxdb_async(mock_write_api, partial_data)

    # Assert
    mock_write_api.write.assert_called_once()
    point_as_string = mock_write_api.write.call_args.kwargs["record"].to_line_protocol()
    
    assert "turbine_id=WT-TEST-02" in point_as_string
    assert "power_output_kw=1800" in point_as_string
    # Assert that missing fields are NOT in the payload
    assert "wind_speed_ms" not in point_as_string
    assert "rotor_speed_rpm" not in point_as_string

def test_write_to_influxdb_no_timestamp(mocker):
    """
    Tests that the function handles a payload missing the timestamp
    without crashing. InfluxDB should assign its own timestamp.
    """
    # Prepare
    mock_write_api = mocker.MagicMock()
    no_time_data = {
        "turbine_id": "WT-TEST-03",
        "power_output_kw": 100,
        "gearbox_temp_c": 61.0
    }

    # Act
    write_to_influxdb_async(mock_write_api, no_time_data)

    # Assert
    mock_write_api.write.assert_called_once()
    point_as_string = mock_write_api.write.call_args.kwargs["record"].to_line_protocol()

    assert "turbine_id=WT-TEST-03" in point_as_string
    assert "power_output_kw=100" in point_as_string
    assert "latency_ns=None" not in point_as_string
    # Assert that no user-defined timestamp was added
    last_part = point_as_string.split(' ')[-1]
    assert not last_part.isdigit()