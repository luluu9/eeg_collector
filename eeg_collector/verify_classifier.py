import sys
import os
import numpy as np

# Add src to path
sys.path.append(os.path.join(os.getcwd()))

from src.core.classifier import CSPSVMClassifier
from src.config import TaskType, ExperimentConfig

model_path = os.path.join(os.path.dirname(__file__), 'models', 'csp_svm_mati_model.pkl')

def verify_classifier():
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        return

    print("Initializing classifier...")
    try:
        classifier = CSPSVMClassifier()
        print("Classifier initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize classifier: {e}")
        return
    
    n_channels = 17 # Model expects 16 features (channels), but preprocessing expects 17 (trigger + 16 channels) 
    n_samples = classifier.filter_samples
    data = np.random.randn(n_channels, n_samples)
    
    print("Predicting on random data...")
    try:
        prediction = classifier.predict(data, TaskType.RELAX)
        print(f"Prediction result: {prediction}")
    except Exception as e:
        print(f"Prediction failed: {e}")

    # Test with too short data
    print("Testing short data...")
    short_data = np.random.randn(n_channels, 100)
    pred_short = classifier.predict(short_data, TaskType.RELAX)
    print(f"Short data prediction: {pred_short}")

if __name__ == "__main__":
    verify_classifier()
