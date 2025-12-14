import sys
import os
import numpy as np
import mne
from collections import defaultdict
from sklearn.metrics import confusion_matrix, accuracy_score

# Add src to path
sys.path.append(os.path.join(os.getcwd()))

from src.core.classifier import CSPSVMClassifier
from src.config import TaskType, ExperimentConfig

# File to load
FILE_PATH = r"../data/mati_imagery_2_run1_20251207_190806_raw.fif"
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'csp_svm_mati_model.pkl')

def get_marker_to_task_map(config: ExperimentConfig):
    # Reverse the markers dict to map int -> TaskType
    # And specifically for feedback markers if they are what's stored? 
    # Usually standard markers are stored in the provided file.
    return {v: k for k, v in config.markers.items()}

def verify_classifier():
    print(f"Loading data from: {FILE_PATH}")
    if not os.path.exists(FILE_PATH):
        # Try finding it relative to current script if the relative path failed
        abs_path = os.path.join(os.path.dirname(__file__), FILE_PATH)
        if os.path.exists(abs_path):
            file_path_to_use = abs_path
        else:
            print(f"Error: File not found at {FILE_PATH} or {abs_path}")
            return
    else:
        file_path_to_use = FILE_PATH

    try:
        raw = mne.io.read_raw_fif(file_path_to_use, preload=True)
    except Exception as e:
        print(f"Failed to load raw file: {e}")
        return

    print("Initializing classifier...")
    try:
        classifier = CSPSVMClassifier()
        print("Classifier initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize classifier: {e}")
        return
    
    config = ExperimentConfig()
    marker_map = get_marker_to_task_map(config)
    
    # We need to find events. 
    # If the file has annotations (STIM channel might be empty or not used for events directly if annotations are present)
    # Let's try to get events from annotations first as that's typical for MNE-LSL/MNE-Python workflow
    events, event_id = mne.events_from_annotations(raw)
    
    # Filter for task events
    # event_id map might be like {'1': 1, '2': 2} or descriptions.
    # We want events that are in our marker_map values.
    
    true_labels = []
    predicted_labels = []
    
    # Prepare counters
    correct_counts = defaultdict(int)
    total_counts = defaultdict(int)
    
    print("\nStarting verification...")
    print("-" * 50)
    print(f"{'Time':<10} | {'True Label':<15} | {'Predicted':<15} | {'Result':<10}")
    print("-" * 50)

    # For each event, we want to simulate the online scenario.
    # The classifier predicts based on the 'recording_duration' window.
    # In the experiment:
    # 1. Event marker sent (Start of Task)
    # 2. Preparation (1s) - wait
    # 3. Recording (5s) <-- We classify AT THE END of this
    # Actually looking at config: preparation_duration=1.0, recording_duration=5.0
    # The marker is likely sent at the START of the 5s recording period (or preparation? Experiment logic matters)
        
    # Assuming the marker marks the BEGINNING of the task (after prep? or before prep?). 
    # Usually markers denote the start of the stimulus.
    # If standard experiment:
    # T0: Marker
    # T0+5s: End of recording -> Classify.
    
    # Let's extract the window [Marker, Marker + 5s]
    # And the classifier expects `filter_samples` amount of history BEFORE the prediction point.
    # So we need data up to T0 + 5s.
    
    # Classifier `predict` method implementation details:
    # it takes `data`. 
    # `_preprocess` takes `data`.
    # `predict` calls `_preprocess`.
    # `predict` takes the LAST `target_samples` from the filtered data for prediction.
    # But `_preprocess` takes LAST `filter_samples` for filtering.
    
    # So if we want to predict for a trial starting at T_start with duration T_dur:
    # Prediction Time T_pred = T_start + T_dur
    # We must provide data ending at T_pred.
    # The length of data provided should be >= filter_samples.
    
    required_samples = classifier.filter_samples
    recording_duration_samples = int(config.recording_duration * raw.info['sfreq'])
    
    # Correction: The classifier uses `device_sampling_rate` which is from config (2048?)
    # The raw file has its own sampling rate.
    # We must respect the raw file's sampling rate for indexing, but check consistency.
    fs_raw = raw.info['sfreq']
    
    # Check if we need to adjust expectations
    if fs_raw != classifier.device_sampling_rate:
        print(f"Warning: File fs ({fs_raw}) != Classifier expected fs ({classifier.device_sampling_rate}).")
        # Depending on implementation, classifier might handle it if we pass fs, but checking CSPSVMClassifier:
        # It uses self.device_sampling_rate hardcoded to config.sampling_rate.
        # Ideally we should temporarily patch the classifier or resample data.
        # But `_preprocess` does: `data_seconds = data.shape[1] / self.device_sampling_rate`. 
        # So it assumes data is at `device_sampling_rate`.
        # WE MUST RESAMPLE if they differ.
        pass

    for event in events:
        start_sample = event[0]
        marker_id = event[2]
        
        # Check if this marker is a known task
        if marker_id not in marker_map:
            continue
            
        task_type = marker_map[marker_id]
        
        # Determine prediction point (end of recording)
        # Assuming marker is start of recording.
        # If marker includes preparation, we might need to offset. 
        # Usually "Task" markers start the action.
        
        # Let's assume Marker = Start of imagined movement.
        pred_time_sec = start_sample / fs_raw + config.recording_duration
        pred_sample = int(pred_time_sec * fs_raw)
        
        # We need `filter_samples` BEFORE pred_sample.
        # But wait, `filter_samples` is defined based on config.sampling_rate.
        # We need the equivalent time in seconds.
        filter_duration_sec = classifier.filter_samples / classifier.device_sampling_rate
        
        start_extract_sec = pred_time_sec - filter_duration_sec
        start_extract_sample = int(start_extract_sec * fs_raw)
        
        if start_extract_sample < 0:
            print(f"Skipping event at {start_sample} (not enough history)")
            continue
            
        if pred_sample > raw.n_times:
            print(f"Skipping event at {start_sample} (end of file)")
            continue
            
        # Extract data: (n_channels, n_samples)
        # raw[] returns (data, times)
        # We need specific channels. Classifier expects 17 channels: Trigger + 16 EEG?
        # Verify classifier `_preprocess`: `data = data[1:17, ...]`
        # It drops channel 0 (Trigger) and takes 1..16.
        # So we need to provide array where index 0 is anything (trigger) and 1..16 are EEG.
        # The RAW file probably has names.
        
        # Let's try to match channels by name if possible, or assume standard order.
        # If raw file is standard, it might have 'Trigger' or 'STI' and 'EEG...'.
        # For this snippet, let's just grab all channels and ensure we have enough.
        
        # Actually, let's blindly pass the channels corresponding to what the collector saves.
        # If the collector saves all channels, we just pass them.
        # The classifier expects index 1 to 16 to be the 16 EEG channels.
        
        data_segment, _ = raw[:, start_extract_sample:pred_sample]
        
        # Handle resampling if needed to match classifier expectation (2048Hz or whatever config says)
        if fs_raw != classifier.device_sampling_rate:
            # Resample data_segment to classifier.device_sampling_rate
            # current samples = data_segment.shape[1]
            # duration = current samples / fs_raw
            # new samples = duration * classifier.device_sampling_rate
            duration = data_segment.shape[1] / fs_raw
            new_num_samples = int(duration * classifier.device_sampling_rate)
            data_segment = signal.resample(data_segment, new_num_samples, axis=1)
        
        # Predict
        try:
            prediction = classifier.predict(data_segment, task_type)
        except Exception as e:
            print(f"Error predicting: {e}")
            prediction = TaskType.ERROR
            
        true_labels.append(task_type)
        predicted_labels.append(prediction)
        
        is_correct = (prediction == task_type)
        result_str = "CORRECT" if is_correct else "WRONG"
        
        print(f"{start_sample/fs_raw:<10.1f} | {task_type.name:<15} | {prediction.name:<15} | {result_str:<10}")
        
        total_counts[task_type] += 1
        if is_correct:
            correct_counts[task_type] += 1

    print("-" * 50)
    
    # Calculate Accuracy
    if not true_labels:
        print("No events found!")
        return
        
    acc = accuracy_score(true_labels, predicted_labels) # Note: TaskType is enum, handled ok?
    # Convert to strings or ints for sklearn if needed, but enums usually compare by identity ok.
    # To be safe, list of names.
    y_true = [t.name for t in true_labels]
    y_pred = [t.name for t in predicted_labels]
    
    acc = accuracy_score(y_true, y_pred)
    
    print(f"\nOverall Accuracy: {acc*100:.2f}%")
    
    print("\nPer-Class Accuracy:")
    for task in sorted(marker_map.values(), key=lambda t: t.name): # Sort by name
        if total_counts[task] > 0:
            class_acc = correct_counts[task] / total_counts[task]
            print(f"{task.name:<15}: {class_acc*100:.2f}% ({correct_counts[task]}/{total_counts[task]})")
            
    print("\nConfusion Matrix:")
    labels = sorted(list(set(y_true) | set(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    print("Labels:", labels)
    print(cm)

if __name__ == "__main__":
    from scipy import signal # Import here since we used it in resampling logic
    verify_classifier()
