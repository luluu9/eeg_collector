import mne
import numpy as np
import pandas as pd
from datetime import datetime
import os

class DataLogger:
    def __init__(self, save_dir="data"):
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        
        self.raw_data = []
        self.timestamps = []
        self.events = [] # List of (timestamp, value)
        self.info = None
        
    def set_stream_info(self, lsl_info):
        # Convert LSL info to MNE info
        n_channels = lsl_info.channel_count()
        sfreq = lsl_info.nominal_srate()
        ch_names = []
        
        # Try to get channel names from description
        ch = lsl_info.desc().child("channels").child("channel")
        for k in range(n_channels):
            name = ch.child_value("label")
            if name:
                ch_names.append(name)
            else:
                ch_names.append(f"EEG_{k:03d}")
            ch = ch.next_sibling()
            
        self.info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
        
    def add_data(self, data, timestamps):
        """Append new data chunk."""
        if len(data) > 0:
            self.raw_data.append(data)
            self.timestamps.append(timestamps)
            
    def add_event(self, timestamp, marker):
        """Add an event marker."""
        self.events.append((timestamp, marker))
        print("event added:", timestamp, marker)
        
    def remove_last_event(self):
        """Remove the last added event."""
        if self.events:
            self.events.pop()
        
    def save(self, subject_id, run_id):
        if not self.raw_data:
            print("No data to save.")
            return
            
        # Concatenate all data
        full_data = np.concatenate(self.raw_data, axis=0).T * 1e-6 # MNE expects (n_channels, n_times)
        full_times = np.concatenate(self.timestamps)
        
        # Create Raw object
        raw = mne.io.RawArray(full_data, self.info)
        
        # Handle events
        # We need to map LSL timestamps to sample indices
        # This is tricky because LSL timestamps are absolute, but MNE expects samples relative to start.
        # We assume the data is continuous.
        
        start_time = full_times[0]
        
        mne_events = []
        for ts, marker in self.events:
            # Find sample index closest to timestamp
            # This is a simple approximation. 
            # Ideally we use the LSL timestamps to interpolate or just find nearest.
            
            # relative time
            rel_time = ts - start_time
            if rel_time < 0:
                continue # Event happened before recording?
                
            sample_idx = int(rel_time * self.info['sfreq'])
            
            if sample_idx < full_data.shape[1]:
                mne_events.append([sample_idx, 0, marker])
                
        if mne_events:
            mne_events = np.array(mne_events)
            # Add annotations or events
            # For .fif, we can usually just save the raw. 
            # But adding events is good.
            # MNE Raw doesn't store events directly in the same way as Epochs, 
            # but we can create Annotations.
            
            mapping = {v: k for k, v in {1:'Relax', 2:'Left', 3:'Right', 4:'Both', 5:'Feet'}.items()} 
            # We should pass the mapping from config, but for now hardcode or just save events array separately?
            # Standard way: Save events as a separate file or use Annotations.
            
            onset = (mne_events[:, 0] / self.info['sfreq'])
            duration = np.zeros_like(onset)
            description = [str(m) for m in mne_events[:, 2]]
            
            annotations = mne.Annotations(onset=onset, duration=duration, description=description)
            raw.set_annotations(annotations)

        # Filename
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.save_dir, f"{subject_id}_run{run_id}_{timestamp_str}_raw.fif")
        
        raw.save(filename, overwrite=True)
        print(f"Saved data to {filename}")
