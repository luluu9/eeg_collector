import threading
import time
import numpy as np
from pylsl import StreamInlet, resolve_streams, local_clock
from collections import deque

class LSLClient:
    def __init__(self, stream_name=None, buffer_duration=30):
        self.stream_name = stream_name
        self.inlet = None
        self.buffer_duration = buffer_duration
        self.running = False
        self.thread = None
        self.data_buffer = deque()
        self.timestamp_buffer = deque()
        self.info = None
        self.lsl_offset = None
        
    def find_streams(self):
        """Resolve all EEG streams on the network."""
        streams = resolve_streams(wait_time=1.0)
        return streams

    def connect(self, stream_info):
        """Connect to a specific stream."""
        self.inlet = StreamInlet(stream_info)
        self.info = self.inlet.info()
        self.lsl_offset = self.inlet.time_correction()
        print(f"Connected to {self.info.name()} at {self.info.nominal_srate()} Hz")
        
    def start_recording(self):
        if self.inlet is None:
            raise RuntimeError("Stream not connected")
        
        self.running = True
        self.data_buffer.clear()
        self.timestamp_buffer.clear()
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()
        
    def stop_recording(self):
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _record_loop(self):
        while self.running:
            chunk, timestamps = self.inlet.pull_chunk(timeout=1.0)
            if timestamps:
                self.data_buffer.extend(chunk)
                self.timestamp_buffer.extend(timestamps)
            else:
                time.sleep(0.001)

    def get_data(self):
        """Return currently buffered data and clear buffer."""
        # In a real experiment, we might want to keep a rolling buffer or 
        # extract specific windows. For this simple logger, we can just 
        # dump what we have.
        # However, for precise slicing, we should probably just return everything 
        # and let the DataLogger handle the slicing based on event timestamps.
        
        # For simplicity in this phase: return all data accumulated since last call
        # CAUTION: This is not thread-safe if _record_loop is appending while we pop.
        # A safer way is to make a copy.
        
        # Actually, for the experiment, we likely want to fetch data *after* a trial 
        # or continuously save it.
        # Let's implement a method to get all available data without clearing, 
        # or a method to pop.
        
        # Let's just return lists for now.
        d = list(self.data_buffer)
        t = list(self.timestamp_buffer)
        
        # Clear for next batch to avoid memory issues if running long
        # But we need to be careful not to lose data if we are just polling.
        # Better approach: The DataLogger should poll frequently or we use a callback.
        
        self.data_buffer.clear()
        self.timestamp_buffer.clear()
        
        return np.array(d), np.array(t)

    def get_info(self):
        return self.info
