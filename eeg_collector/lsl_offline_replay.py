
import multiprocessing as mp
from mne_lsl.player import PlayerLSL
from mne_lsl.datasets import sample

export_name = r"data/KONRAD-2_run1_20251202_203845_raw.fif"
debug_file = False


def player_process(raw):
    if (debug_file):
        raw = sample.data_path() / "sample-ant-raw.fif"

    chunk_size = 20  # number of samples to send in one push
    player = PlayerLSL(raw, chunk_size=chunk_size, name="test-player")
    
    # Explore annotations
    print("Annotations:")
    print(player.annotations)
    print(player.annotations.description)
    print(player.annotations.to_data_frame())

    # most likely 500 Hz for the sample data
    signal_freq = player.info["sfreq"]
    print("Signal frequency:", signal_freq)
    player.start()
    while player.running:
        pass
    print("Player finished. Repeating")

    # Restart the player
    player_process(raw)

if __name__ == "__main__":
    process = mp.Process(target=player_process, args=(export_name,))
    process.start()
    print("Player started in a separate process!")
    process.join()
