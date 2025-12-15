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

events_real = {"relax": 1, "left_hand": 2, "right_hand": 3, "both_hands": 4, "both_feets": 5}
events_predicted = {"relax_predicted": 11, "left_hand_predicted": 12, "right_hand_predicted": 13, "both_hands_predicted": 14, "both_feets_predicted": 15}
classification_result = {"correct": 20, "incorrect": 21}
all_possible_events_id = {**events_real, **events_predicted, **classification_result}

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


    description_code_to_consistent_id = {str(v): v for v in all_possible_events_id.values()}
    events, event_id = mne.events_from_annotations(raw, event_id=description_code_to_consistent_id)
    model_classes = classifier.model.classes_
    
    true_labels = []
    predicted_labels = []
    
    # Prepare counters
    correct_counts = defaultdict(int)
    total_counts = defaultdict(int)
    
    print("\nStarting verification...")
    print("-" * 50)
    print(f"{'Time':<10} | {'True Label':<10} | {'Predicted':<10} | {'Result':<10}")
    print("-" * 50)

    fs_raw = raw.info['sfreq']
    
    # Check if we need to adjust expectations
    if fs_raw != classifier.device_sampling_rate:
        assert False, f"File fs ({fs_raw}) != Classifier expected fs ({classifier.device_sampling_rate})."

    for event in events:
        start_sample = event[0]
        marker_id = event[2]
        
        # Check if this marker is a known task
        if marker_id not in marker_map:
            #print("Warning: Unknown marker id: ", marker_id)
            continue
        
        if marker_id not in model_classes:
            #print("Info: Model does not know task ", marker_map[marker_id])
            continue
            
        task_type = marker_map[marker_id]
        
        pred_sample = int(start_sample + (config.preparation_duration * fs_raw) + (config.recording_duration * fs_raw))
        start_extract_sample = pred_sample - classifier.filter_samples
        
        if start_extract_sample < 0:
            print(f"Skipping {task_type.name} event at {start_sample} (not enough history)")
            continue
            
        if pred_sample > raw.n_times:
            print(f"Skipping {task_type.name} event at {start_sample} (end of file)")
            continue
        
        data_segment, _ = raw[:, start_extract_sample:pred_sample]
        
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
        
        print(f"{start_sample/fs_raw:<10.1f} | {task_type.name:<10} | {prediction.name:<10} | {result_str:<10}")
        
        total_counts[task_type] += 1
        if is_correct:
            correct_counts[task_type] += 1

    print("-" * 50)
    
    # Calculate Accuracy
    if not true_labels:
        print("No events found!")
        return
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
    verify_classifier()
