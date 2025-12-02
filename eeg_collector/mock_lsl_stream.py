import time
import numpy as np
from pylsl import StreamInfo, StreamOutlet

def main():
    # Define stream parameters
    srate = 250  # Sampling rate in Hz
    n_channels = 8
    name = 'MockEEG'
    type = 'EEG'
    
    # Create stream info
    info = StreamInfo(name, type, n_channels, srate, 'float32', 'myuid12345')
    
    # Append some meta-data
    channels = info.desc().append_child("channels")
    for c in ["Fp1", "Fp2", "C3", "C4", "P7", "P8", "O1", "O2"]:
        channels.append_child("channel").append_child_value("label", c)
        
    # Create outlet
    outlet = StreamOutlet(info)
    
    print(f"Sending data... Press Ctrl+C to stop.")
    
    start_time = time.time()
    sent_samples = 0
    
    try:
        while True:
            elapsed_time = time.time() - start_time
            required_samples = int(srate * elapsed_time) - sent_samples
            
            if required_samples > 0:
                # Generate random data
                # data = np.random.randn(required_samples, n_channels).astype(np.float32)
                data = (np.arange(sent_samples, sent_samples + required_samples)[:, None] * 1.0).astype(np.float32)
                data = np.tile(data, (1, n_channels))

                # Push chunk
                outlet.push_chunk(data)
                sent_samples += required_samples
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("Stopping stream...")

if __name__ == '__main__':
    main()
