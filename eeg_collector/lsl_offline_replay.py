import multiprocessing as mp
from mne_lsl.player import PlayerLSL
from mne_lsl.datasets import sample
from mne_lsl.stream_viewer import StreamViewer
from pylsl import resolve_streams
import time

export_name = r"data/mati_imagery_2_run1_20251207_190808_raw.fif"
debug_file = False
stream_name = "test-player"

def player_process(raw_path, start_event):
    if debug_file:
        raw_path = sample.data_path() / "sample-ant-raw.fif"

    chunk_size = 20  # number of samples to send in one push
    player = PlayerLSL(raw_path, chunk_size=chunk_size, name=stream_name)
    
    # Explore annotations
    print("Annotations:")
    print(player.annotations)
    print(player.annotations.description)
    print(player.annotations.to_data_frame())

    # most likely 500 Hz for the sample data
    signal_freq = player.info["sfreq"]
    print("Signal frequency:", signal_freq)
    player.start()
    start_event.set()  # Signal that the player has started
    while player.running:
        pass
    print("Player finished. Repeating")

    # Restart the player (this part of the original code seems to imply
    # a continuous loop, but for a simple replay, it might be better
    # to let the process exit or handle the loop externally if needed.)
    # For now, we'll just let it exit after one replay.
    # If continuous replay is desired, the player object should be re-initialized
    # or the loop logic adjusted.
    # player_process(raw_path, start_event) # This would create infinite recursion

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
