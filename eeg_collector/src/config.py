from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Tuple

class TaskType(Enum):
    RELAX = auto()
    LEFT_HAND = auto()
    RIGHT_HAND = auto()
    BOTH_HANDS = auto()
    FEET = auto()

@dataclass
class ExperimentConfig:
    # Timing parameters (in seconds)
    preparation_duration: float = 1.0 # event is emitted at start of preparation
    recording_duration: float = 5.0
    feedback_duration: float = 1.5
    min_relax_duration: float = 2.0
    max_relax_duration: float = 3.0
    
    # Experiment structure
    n_runs: int = 1
    repetitions_per_run: int = 10 # 5 classes * 10 reps = 50 trials
    
    # Classifier
    mock_classifier_accuracy: float = 0.5
    
    # Markers for LSL/Events
    markers: Dict[TaskType, int] = None
    feedback_markers: Dict[TaskType, int] = None
    marker_correct: int = 20
    marker_wrong: int = 21

    def __post_init__(self):
        if self.markers is None:
            self.markers = {
                TaskType.RELAX: 1,
                TaskType.LEFT_HAND: 2,
                TaskType.RIGHT_HAND: 3,
                TaskType.BOTH_HANDS: 4,
                TaskType.FEET: 5
            }
            
        if self.feedback_markers is None:
            # Feedback markers are offset by 10 from the original markers
            self.feedback_markers = {k: v + 10 for k, v in self.markers.items()}

    @property
    def tasks(self) -> List[TaskType]:
        return [TaskType.LEFT_HAND, TaskType.RIGHT_HAND, TaskType.BOTH_HANDS, TaskType.FEET, TaskType.RELAX]

    @property
    def trials_per_run(self) -> int:
        return len(self.tasks) * self.repetitions_per_run

    def get_marker(self, task: TaskType) -> int:
        return self.markers.get(task, 0)

    def get_feedback_marker(self, task: TaskType) -> int:
        return self.feedback_markers.get(task, 0)
