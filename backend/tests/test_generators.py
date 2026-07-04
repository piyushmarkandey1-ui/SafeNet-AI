"""
Unit tests for the synthetic data generators to verify row counts,
columns, and specific logical patterns (like fan-in money mules).
"""
import pytest
import os
import sys

# Add scripts directory to path for testing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from generate_call_records import generate_call_records
from generate_transactions import generate_transactions
from generate_complaints_geo import generate_complaints_geo, LAT_MIN, LAT_MAX, LNG_MIN, LNG_MAX

def test_generate_call_records():
    data = generate_call_records(100)
    assert len(data) == 100
    assert 'call_id' in data[0]
    assert 'caller_number' in data[0]
    assert 'is_spoofed' in data[0]
    
    # Verify boolean logic
    assert any(record['is_spoofed'] == True for record in data)
    assert any(record['is_spoofed'] == False for record in data)

def test_generate_transactions():
    data = generate_transactions(num_normal=100, num_mule_networks=1)
    
    # Normal + at least 5 incoming + 1 sweep out = 106 minimum
    assert len(data) >= 106
    assert 'txn_id' in data[0]
    assert 'amount' in data[0]
    assert 'flagged_mule' in data[0]
    
    # Verify fan-in pattern exists
    flagged = [r for r in data if r['flagged_mule']]
    assert len(flagged) >= 6 # At least 5 in, 1 out
    
    # Check if multiple transactions converged on one receiver
    receivers = {}
    for r in flagged:
        receivers[r['receiver_account']] = receivers.get(r['receiver_account'], 0) + 1
        
    # At least one account should have multiple incoming flagged transfers
    assert any(count >= 5 for count in receivers.values())

def test_generate_complaints_geo():
    data = generate_complaints_geo(5)
    assert len(data) == 5
    assert 'lat' in data[0]
    assert 'lng' in data[0]
    assert 'intensity' in data[0]
    
    # Verify bounding box (Delhi NCR)
    for spot in data:
        assert LAT_MIN <= spot['lat'] <= LAT_MAX
        assert LNG_MIN <= spot['lng'] <= LNG_MAX
