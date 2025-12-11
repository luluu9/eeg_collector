from abc import ABC, abstractmethod
import random
from ..config import TaskType, ExperimentConfig
import numpy as np
import joblib
from scipy import signal
import os

class BaseClassifier(ABC):
    @abstractmethod
    def predict(self, data, true_label: TaskType) -> TaskType:
        """
        Predict the class for the given data.
        
        Args:
            data: The EEG data (numpy array).
            true_label: The actual task type (for mock behavior).
            
        Returns:
            The predicted TaskType.
        """
        pass

class MockClassifier(BaseClassifier):
    def __init__(self, accuracy=0.5):
        """
        Args:
            accuracy (float): Probability of correct classification (0.0 to 1.0).
        """
        self.accuracy = accuracy
        
    def predict(self, data, true_label: TaskType) -> TaskType:
        if random.random() < self.accuracy:
            return true_label
        else:
            # Return a random WRONG label
            all_types = list(TaskType)
            # Filter out the true label and RELAX if needed (usually we don't classify relax as a task? or do we?)
            # The prompt says "5 states: Relax, Left Hand, Right Hand, Both Hands, Feet".
            # So Relax IS a class.
            
            wrong_choices = [t for t in all_types if t != true_label]
            if not wrong_choices:
                 # Should not happen if >1 tasks
                return true_label
            return random.choice(wrong_choices)


class CSPSVMClassifier(BaseClassifier):
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'csp_svm_mati_model.pkl')
        
        self.config = ExperimentConfig()
        self.classifier_sampling_rate: int = 256
        self.device_sampling_rate: int = self.config.sampling_rate
        self.target_time: int = 2
        self.target_samples: int = self.classifier_sampling_rate * self.target_time
        self.filter_samples: int = self.device_sampling_rate * self.target_time * 10
        self.lowcut: int = 8
        self.highcut: int = 32

        self.mapping = {
            1: TaskType.RELAX,
            2: TaskType.LEFT_HAND,
            3: TaskType.RIGHT_HAND,
            4: TaskType.BOTH_HANDS,
            5: TaskType.FEET
        }

        try:
            self.model = joblib.load(self.model_path)
        except Exception as e:
            print(f"Failed to load model from {self.model_path}: {e}")
            raise

    def _preprocess(self, data: np.ndarray) -> np.ndarray:
        """
        Apply 50Hz notch filter and 8-32Hz bandpass filter.
        
        Args:
            data: EEG data of shape (n_channels, n_samples)
            fs: Sampling frequency
            
        Returns:
            Filtered data
        """
        # Pick channels A1-16 and only recent samples
        # 0: trigger, 1: A1, 2: A2, ... 16: A16 
        data = data[1:17, -self.filter_samples:]

        # Resample to 250Hz
        data_seconds = data.shape[1] / self.device_sampling_rate
        target_samples = int(data_seconds * self.classifier_sampling_rate)
        data = signal.resample(data, target_samples, axis=1)

        # Notch filter at 50Hz
        # Quality factor Q = 30
        b_notch, a_notch = signal.iirnotch(50.0, 30.0, self.classifier_sampling_rate)
        data_notch = signal.filtfilt(b_notch, a_notch, data, axis=-1)

        # Bandpass filter
        # Using butterworth filter
        nyquist = 0.5 * self.classifier_sampling_rate
        low = self.lowcut / nyquist
        high = self.highcut / nyquist
        b_band, a_band = signal.butter(5, [low, high], btype='band')
        data_filtered = signal.filtfilt(b_band, a_band, data_notch, axis=-1)
        
        return data_filtered

    def predict(self, data: np.ndarray, true_label: TaskType) -> TaskType:
        n_samples = data.shape[1]
        
        if n_samples < self.filter_samples:
            print(f"Warning: data length {n_samples} < {self.filter_samples}")
            return TaskType.ERROR

        data_filtered = self._preprocess(data)
        X = data_filtered[np.newaxis, :, -self.target_samples:] # (1, ch, time)
        
        try:
            prediction = self.model.predict(X)[0] # Returns class ID (e.g. 7)
            probs = self.model.predict_proba(X)
            print(probs)


            return self.mapping[prediction]
        except Exception as e:
            print(f"Prediction error: {e}")
            return TaskType.ERROR
