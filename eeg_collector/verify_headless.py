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
        
    print(f"Found {len(streams)} streams.")
    for s in streams:
        print(f" - Found Stream: Name='{s.name()}', Type='{s.type()}'")

    # Filter for MockEEG or type EEG
    target_stream = None
    for s in streams:
        if s.name() == 'MockEEG' and s.type() == 'EEG':
            target_stream = s
            break
            
    if not target_stream:
        # Fallback to first EEG stream
        for s in streams:
            if s.type() == 'EEG':
                target_stream = s
                break
                
    if not target_stream:
         print("No EEG streams found. Available streams:")
         for s in streams:
             print(f" - {s.name()} ({s.type()})")
         if streams:
             target_stream = streams[0]
             print(f"Connecting to first available stream: {target_stream.name()}")
         else:
             return
    else:
        print(f"Connecting to target stream: {target_stream.name()} ({target_stream.type()})")

    lsl.connect(target_stream)
    
    logger = DataLogger(save_dir="test_data")
    logger.set_stream_info(lsl.get_info())
    
    config = ExperimentConfig()
    config.repetitions_per_run = 1 # Short run (1 rep * 5 tasks = 5 trials)
    config.preparation_duration = 0.5
    config.recording_duration = 1.0
    config.min_relax_duration = 0.5
    config.feedback_duration = 0.5 # Short feedback for test
    
    # We need a QCoreApplication for signals/timers
    app = QCoreApplication(sys.argv)
    
    session = ExperimentSession(config, lsl, logger)
    
    def on_finished():
        print("Experiment finished signal received.")
        # Check if we have feedback markers
        events = logger.events
        print(f"Recorded {len(events)} events.")
        # We expect markers > 10 (Prediction) AND 20/21 (Quality)
        feedback_events = [e for e in events if e[1] > 10]
        # Filter prediction markers (11-15)
        predictions = [e for e in feedback_events if 11 <= e[1] <= 15]
        # Filter quality markers (20-21)
        qualities = [e for e in feedback_events if e[1] in [20, 21]]
        
        print(f"Found {len(predictions)} prediction events: {[e[1] for e in predictions]}")
        print(f"Found {len(qualities)} quality events: {[e[1] for e in qualities]}")
        
        logger.save("TEST_SUBJ", 999)
        app.quit()
        
    def on_feedback(prediction, is_correct):
        print(f"FEEDBACK RECEIVED: Prediction={prediction}, Correct={is_correct}")

    session.finished.connect(on_finished)
    session.feedback_ready.connect(on_feedback)
    
    print("Starting session...")
    session.start()
    
    # Stop after 10 seconds (enough for ~2 trials)
    def stop_later():
        print("Stopping session...")
        session.stop()
        app.quit()

    QTimer.singleShot(10000, stop_later)
    
    # Run event loop
    app.exec()
    print("Verification done.")

if __name__ == "__main__":
    run_verification()
