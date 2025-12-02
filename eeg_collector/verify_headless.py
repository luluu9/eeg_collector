import time
import threading
import sys
import os
from PyQt6.QtCore import QCoreApplication, QTimer

# Add current dir to path
sys.path.append(os.getcwd())

from src.core.lsl_client import LSLClient
from src.core.experiment import ExperimentSession, ExperimentState
from src.core.data_handler import DataLogger
from src.config import ExperimentConfig

def run_verification():
    print("Starting verification...")
    
    # 1. Start Mock LSL (we assume it's running or we start it here?)
    # It's better if it's running separately. 
    # But for this script, let's try to connect.
    
    lsl = LSLClient()
    print("Looking for streams...")
    streams = lsl.find_streams()
    if not streams:
        print("No streams found. Please ensure mock_lsl_stream.py is running.")
        return
        
    print(f"Found {len(streams)} streams. Connecting to first: {streams[0].name()}")
    lsl.connect(streams[0])
    
    logger = DataLogger(save_dir="test_data")
    logger.set_stream_info(lsl.get_info())
    
    config = ExperimentConfig()
    config.repetitions_per_run = 1 # Short run (1 rep * 5 tasks = 5 trials)
    config.preparation_duration = 0.5
    config.recording_duration = 1.0
    config.min_relax_duration = 0.5
    config.max_relax_duration = 0.5
    
    # We need a QCoreApplication for signals/timers
    app = QCoreApplication(sys.argv)
    
    session = ExperimentSession(config, lsl, logger)
    
    def on_finished():
        print("Experiment finished signal received.")
        logger.save("TEST_SUBJ", 999)
        app.quit()
        
    session.finished.connect(on_finished)
    
    print("Starting session...")
    session.start()
    
    # Simulate manual stop after 1.5s
    def simulate_stop():
        print("Simulating manual stop...")
        # We need to simulate what MainWindow does: save then stop
        # But here we are testing ExperimentSession directly.
        # ExperimentSession doesn't save, DataLogger does.
        # MainWindow calls logger.save() then experiment.stop().
        
        logger.save("TEST_SUBJ", "partial")
        session.stop()
        app.quit()

    QTimer.singleShot(1500, simulate_stop)
    
    # Run event loop
    app.exec()
    print("Verification done.")

if __name__ == "__main__":
    run_verification()
