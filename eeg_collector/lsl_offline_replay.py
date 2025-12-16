import multiprocessing as mp
from mne_lsl.player import PlayerLSL
from mne_lsl.datasets import sample
from mne_lsl.stream_viewer import StreamViewer
from pylsl import resolve_streams
from mne.io import read_raw_fif
from mne import Annotations
import numpy as np
from threading import Event
    
export_name = r"data/mati_imagery_2_run1_20251207_190808_raw.fif"
debug_file = False
stream_name = "test-player"

def player_process(raw_path, start_event):
    if debug_file:
        raw_path = sample.data_path() / "sample-ant-raw.fif"

    # Load raw first to manipulate annotations
    raw = read_raw_fif(raw_path, preload=True)
    
    # 1. Filter Annotations (Keep only 1-5)
    keep_desc = ['1', '2', '3', '4', '5']
    # Filter logic: list comprehension on raw.annotations
    # Note: Annotations object is mutable
    
    # Extract existing
    onsets = []
    durations = []
    descriptions = []
    
    for o, d, desc in zip(raw.annotations.onset, raw.annotations.duration, raw.annotations.description):
        if desc in keep_desc:
            onsets.append(o)
            durations.append(d)
            descriptions.append(desc)
            
    # 2. Ensure ALL classes are present (Pad with dummy at t=0 if missing)
    # This forces PlayerLSL to create channels for 1, 2, 3, 4, 5 in that sorted order.
    # PlayerLSL sorts unique(descriptions).
    # If we have ['1', '1', '2', ...], sorted=['1', '2'] -> Ch0='1', Ch1='2'.
    # If we add '3' at t=0 (duration 0), sorted=['1', '2', '3'] -> Ch0='1', Ch1='2', Ch2='3'.
    
    for val in keep_desc:
        if val not in descriptions:
            print(f"Adding dummy annotation for '{val}' to force channel creation.")
            onsets.append(0.0)
            durations.append(0.0)
            descriptions.append(val)
            
    # Re-apply
    new_annots = Annotations(onset=onsets, duration=durations, description=descriptions, orig_time=raw.annotations.orig_time)
    raw.set_annotations(new_annots)
    
    chunk_size = 128  # number of samples to send in one push
    # PlayerLSL accepts raw object
    player = PlayerLSL(raw, chunk_size=chunk_size, name=stream_name)
    
    # Explore annotations
    print("Filtered Annotations (Descriptions):")
    print(np.unique(player.annotations.description))

    # most likely 500 Hz for the sample data
    signal_freq = player.info["sfreq"]
    print("Signal frequency:", signal_freq)
    player.start()
    start_event.set()  # Signal that the player has started
    Event().wait()

if __name__ == "__main__":
    player_started_event = mp.Event()
    process = mp.Process(target=player_process, args=(export_name, player_started_event))
    process.start()
    
    print("Waiting for player to start...")
    player_started_event.wait() # Wait until the player process signals it has started
    print("Player started in a separate process!")
    
    streams = resolve_streams(wait_time=1.0)
    print(streams[0].name())
    viewer = StreamViewer(stream_name) # BioSemi
    viewer.start()
    
    process.join() # Wait for the player process to finish if it's not an infinite loop
