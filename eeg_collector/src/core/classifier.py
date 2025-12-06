from abc import ABC, abstractmethod
import random
from ..config import TaskType

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
