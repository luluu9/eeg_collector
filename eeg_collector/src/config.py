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
    preparation_duration: float = 1.0
    recording_duration: float = 5.0
    min_relax_duration: float = 2.0
    max_relax_duration: float = 3.0
    
    # Experiment structure
    n_runs: int = 1
    repetitions_per_run: int = 15 # 5 classes * 15 reps = 75 trials
    
    # Markers for LSL/Events
    markers: Dict[TaskType, int] = None

    def __post_init__(self):
        if self.markers is None:
            self.markers = {
                TaskType.RELAX: 1,
                TaskType.LEFT_HAND: 2,
                TaskType.RIGHT_HAND: 3,
                TaskType.BOTH_HANDS: 4,
                TaskType.FEET: 5
            }

    @property
    def tasks(self) -> List[TaskType]:
        return [TaskType.LEFT_HAND, TaskType.RIGHT_HAND, TaskType.BOTH_HANDS, TaskType.FEET, TaskType.RELAX]

    @property
    def trials_per_run(self) -> int:
        return len(self.tasks) * self.repetitions_per_run

    def get_marker(self, task: TaskType) -> int:
        return self.markers.get(task, 0)
