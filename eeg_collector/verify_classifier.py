import sys
import os
import numpy as np
import mne
from collections import defaultdict
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report

# Add src to path
sys.path.append(os.path.join(os.getcwd()))

from src.core.classifier import CSPSVMClassifier
from src.config import TaskType, ExperimentConfig

# File to load
FILE_PATHS = [
    #r'../data/mati_imagery_1_run1_20251207_183304_raw.fif',
    r'../data/mati_imagery_2_run1_20251207_190808_raw.fif',
    #r'../data/mati_imagery_3_real_classifier_run1_20251207_204045_raw.fif',
    #r'../data/mati_imagery_4_real_classifier_run1_20251207_210156_raw.fif'
    ]
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'csp_svm_model.pkl')

DEBUG_RUN = False

events_real = {"relax": 1, "left_hand": 2, "right_hand": 3, "both_hands": 4, "both_feets": 5}
events_predicted = {"relax_predicted": 11, "left_hand_predicted": 12, "right_hand_predicted": 13, "both_hands_predicted": 14, "both_feets_predicted": 15}
classification_result = {"correct": 20, "incorrect": 21}
all_possible_events_id = {**events_real, **events_predicted, **classification_result}

def get_marker_to_task_map(config: ExperimentConfig):
    return {v: k for k, v in config.markers.items()}

def verify_classifier():
    global_true_labels = []
    global_predicted_labels = []
    run_results = []

    for file_path in FILE_PATHS:
        print(f"Loading data from: {file_path}")
        if not os.path.exists(file_path):
            # Try finding it relative to current script if the relative path failed
            abs_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(abs_path):
                file_path_to_use = abs_path
            else:
                print(f"Error: File not found at {file_path} or {abs_path}")
                continue
        else:
            file_path_to_use = file_path

        try:
            raw = mne.io.read_raw_fif(file_path_to_use, preload=True)
        except Exception as e:
            print(f"Failed to load raw file: {e}")
            continue

        print("Initializing classifier...")
        try:
            classifier = CSPSVMClassifier(MODEL_PATH)
            print("Classifier initialized successfully.")
        except Exception as e:
            print(f"Failed to initialize classifier: {e}")
            continue
        
        config = ExperimentConfig()
        marker_map = get_marker_to_task_map(config)

        description_code_to_consistent_id = {str(v): v for v in all_possible_events_id.values()}
        events, event_id = mne.events_from_annotations(raw, event_id=description_code_to_consistent_id)
        model_classes = classifier.model.classes_
        
        file_true_labels = []
        file_predicted_labels = []
        
        # Prepare counters
        correct_counts = defaultdict(int)
        total_counts = defaultdict(int)
        
        if DEBUG_RUN:
            print(f"\nStarting verification for {os.path.basename(file_path)}...")
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
                if DEBUG_RUN:
                    print("Warning: Unknown marker id: ", marker_id)
                continue
            
            if marker_id not in model_classes:
                if DEBUG_RUN:
                    print("Info: Model does not know task ", marker_map[marker_id])
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
                
            file_true_labels.append(task_type)
            file_predicted_labels.append(prediction)
            
            is_correct = (prediction == task_type)
            result_str = "CORRECT" if is_correct else "WRONG"
            
            if DEBUG_RUN:
                print(f"{start_sample/fs_raw:<10.1f} | {task_type.name:<10} | {prediction.name:<10} | {result_str:<10}")
                print("-" * 50)
            
            total_counts[task_type] += 1
            if is_correct:
                correct_counts[task_type] += 1
        
        y_true_names = [t.name for t in file_true_labels]
        y_pred_names = [t.name for t in file_predicted_labels]
        
        acc = accuracy_score(y_true_names, y_pred_names)
        
        run_results.append({
                'file': os.path.basename(file_path),
                'accuracy': acc,
                'correct': sum(1 for t, p in zip(file_true_labels, file_predicted_labels) if t == p),
                'total': len(file_true_labels)
            })

        global_true_labels.extend(y_true_names)
        global_predicted_labels.extend(y_pred_names)
        
        print(f"File Accuracy: {acc*100:.2f}%")

    # --- Overall Summary ---
    print("\n" + "=" * 60)
    print("SUMMARY OF ALL RUNS")
    print("=" * 60)
    print(f"{'File Name':<40} | {'Accuracy':<10} | {'Correct/Total':<15}")
    print("-" * 70)
    
    for res in run_results:
        if 'note' in res:
            acc_str = "N/A"
            ct_str = "0/0"
        else:
            acc_str = f"{res['accuracy']*100:.2f}%"
            ct_str = f"{res['correct']}/{res['total']}"
        print(f"{res['file']:<40} | {acc_str:<10} | {ct_str:<15}")

    print("-" * 70)

    if global_true_labels:
        overall_acc = accuracy_score(global_true_labels, global_predicted_labels)
        print(f"Overall Accuracy: {overall_acc*100:.2f}% ({sum(1 for t, p in zip(global_true_labels, global_predicted_labels) if t == p)}/{len(global_true_labels)})")
        
        print("\nOverall Confusion Matrix:")
        labels = ["RELAX", "LEFT_HAND", "RIGHT_HAND", "BOTH_HANDS", "FEET"]
        cm = confusion_matrix(global_true_labels, global_predicted_labels, labels=labels)
        print(cm)

        print ("\nClassification report:")
        print(classification_report(global_true_labels, global_predicted_labels, labels=labels))
    else:
        print("No events processed across all files.")


if __name__ == "__main__":
    verify_classifier()
