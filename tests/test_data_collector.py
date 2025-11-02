import json
import pytest
from data_collector import parse_payload

def test_parse_payload_success():
    """
    Tests the "happy path" with a valid JSON payload.
    """
    # 1. Prepare: Create a valid payload (as bytes, like MQTT gives us)
    valid_data = {"turbine_id": "WT-01", "temperature": 25.5}
    payload_bytes = json.dumps(valid_data).encode("utf-8")
    
    # 2. Act: Run the function we are testing
    result = parse_payload(payload_bytes)
    
    # 3. Assert: Check if the result is what we expected
    assert result is not None
    assert result == valid_data
    assert result["turbine_id"] == "WT-01"

def test_parse_payload_bad_json():
    """
    Tests the "failure path" with a malformed JSON payload.
    """
    # 1. Prepare: Create a broken payload
    payload_bytes = b'{"turbine_id": "WT-01", "temperature": 25.5' # Missing closing bracket
    
    # 2. Act
    result = parse_payload(payload_bytes)
    
    # 3. Assert: We expect the function to return None
    assert result is None

def test_parse_payload_not_json():
    """
    Tests the "failure path" with a payload that isn't JSON at all.
    """
    # 1. Prepare
    payload_bytes = b'This is just a random string'
    
    # 2. Act
    result = parse_payload(payload_bytes)
    
    # 3. Assert
    assert result is None

def test_parse_payload_empty():
    """
    Tests an edge case with an empty payload.
    """
    # 1. Prepare
    payload_bytes = b''
    
    # 2. Act
    result = parse_payload(payload_bytes)
    
    # 3. Assert
    assert result is None