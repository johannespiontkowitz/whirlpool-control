import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logic import pump_should_run

def test_pump_runs_when_cold():
    assert pump_should_run(30.0, 36.0) == True

def test_pump_off_when_warm():
    assert pump_should_run(37.0, 36.0) == False