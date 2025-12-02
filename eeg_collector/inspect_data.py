import mne
import os
import glob
import matplotlib.pyplot as plt

def main():
    # Search in data/ directory
    search_dir = "data"
    search_file = None#"data/SUBJ01_runpartial_20251123_193606_raw.fif"
    
    # Check if directory exists
    # Priority: 
    # 1. "data" (Root)
    # 2. "eeg_collector/data" (Subdir)
    # 3. "eeg_collector/test_data" (Test)
    latest_file = None
    if search_file:
        latest_file = search_file
    else:
        possible_dirs = ["data", "eeg_collector/data", "eeg_collector/test_data", "test_data"]
        found = False
        
        for d in possible_dirs:
            if os.path.exists(d) and glob.glob(os.path.join(d, "*.fif")):
                search_dir = d
                found = True
                break
                
        if not found:
            print(f"No .fif files found in {possible_dirs}.")
            return

        # Find all .fif files
        files = glob.glob(os.path.join(search_dir, "*.fif"))
        if not files:
            print(f"No .fif files found in '{search_dir}'.")
            return
            
        # Get the latest file
        latest_file = max(files, key=os.path.getctime)
        print(f"Loading latest file: {latest_file}")
    
    try:
        # Load data
        raw = mne.io.read_raw_fif(latest_file, preload=True)
        print(raw.info)
        
        raw.filter(l_freq=1.0, h_freq=40.0, fir_design='firwin')
        raw.notch_filter(freqs=[50.0])
        
        # Extract events from annotations
        # MNE stores our string descriptions in annotations, we convert them back to events for plotting
        events, event_id = mne.events_from_annotations(raw)
        print(f"Found {len(events)} events.")
        print(f"Event IDs: {event_id}")
        
        # Plot
        # scalings='auto' helps if signals are small/large
        raw.plot(events=events, event_id=event_id, block=True, title=f"Inspection: {os.path.basename(latest_file)}", scalings='auto')
        
    except Exception as e:
        print(f"Error loading/plotting file: {e}")

if __name__ == "__main__":
    main()
