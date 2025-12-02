import random
import time
from enum import Enum, auto
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from pylsl import local_clock
from ..config import ExperimentConfig, TaskType

class ExperimentState(Enum):
    IDLE = auto()
    RELAX = auto()
    CUE = auto()
    RECORDING = auto()
    FINISHED = auto()

class ExperimentSession(QObject):
    # Signals to update GUI
    state_changed = pyqtSignal(ExperimentState)
    task_changed = pyqtSignal(str) # e.g. "Left Hand"
    progress_updated = pyqtSignal(int, int) # current_trial, total_trials
    finished = pyqtSignal()
    
    def __init__(self, config: ExperimentConfig, lsl_client, data_logger):
        super().__init__()
        self.config = config
        self.lsl_client = lsl_client
        self.data_logger = data_logger
        
        self.state = ExperimentState.IDLE
        self.current_trial_idx = 0
        self.trial_sequence = []
        self.current_task = None
        self.running = False
        self.paused = False
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._on_timeout)
        
        # Data polling timer
        self.poll_timer = QTimer()
        self.poll_timer.timeout.connect(self._poll_data)
        
    def start(self):
        self.running = True
        self.paused = False
        self.current_trial_idx = 0
        self._generate_sequence()
        
        self.lsl_client.start_recording()
        self.poll_timer.start(100) # Poll every 100ms
        self._next_trial()
        
    def stop(self):
        self.running = False
        self.timer.stop()
        self.poll_timer.stop()
        self.lsl_client.stop_recording()
        self.state = ExperimentState.IDLE
        self.state_changed.emit(self.state)
        
    def pause(self):
        """Pause the experiment. If in a trial, it will be retried."""
        if not self.running:
            return
            
        self.paused = True
        self.timer.stop()
        self.state = ExperimentState.IDLE # Or a PAUSED state?
        # Let's add PAUSED state to Enum if needed, or just handle logic.
        # User wants "reset only current task".
        # So we stop the timer, and when we resume, we restart the SAME trial index.
        
        # If we pause during CUE or RECORDING, we should remove the event
        # because the trial is being rejected/retried.
        if self.state in [ExperimentState.CUE, ExperimentState.RECORDING]:
            self.data_logger.remove_last_event()
            
        self.state_changed.emit(ExperimentState.IDLE) # Show Idle/Paused
        
    def resume(self):
        if not self.running or not self.paused:
            return
            
        self.paused = False
        # Restart current trial
        self._next_trial()

    def _generate_sequence(self):
        # Balanced block randomization
        # Create blocks of all tasks, shuffle each block, then concatenate
        tasks = self.config.tasks
        sequence = []
        for _ in range(self.config.repetitions_per_run):
            block = tasks.copy()
            random.shuffle(block)
            sequence.extend(block)
        self.trial_sequence = sequence
        
    def _poll_data(self):
        # Fetch data from LSL client and push to DataLogger
        data, timestamps = self.lsl_client.get_data()
        self.data_logger.add_data(data, timestamps)
        if timestamps.size > 0:
            print("timestamps[0]", timestamps[0]) # should be every 100ms
            print("timestamps[-1]", timestamps[-1])
        

    def _next_trial(self):
        if not self.running or self.paused:
            return
            
        if self.current_trial_idx >= len(self.trial_sequence):
            self._finish_experiment()
            return
            
        self.current_task = self.trial_sequence[self.current_trial_idx]
        self.progress_updated.emit(self.current_trial_idx + 1, len(self.trial_sequence))
        
        # Start with Relax (Inter-trial interval)
        self._enter_relax()
        
    def _enter_relax(self):
        self.state = ExperimentState.RELAX
        self.state_changed.emit(self.state)
        # For inter-trial relax, we might show a cross?
        self.task_changed.emit("Relax") 
        
        # Log event? Maybe not for inter-trial relax, or use a specific code?
        # If "Relax" is also a task, we need to distinguish "Inter-trial Relax" from "Task Relax".
        # Let's assume Inter-trial is just a break.
        
        # Random duration
        duration = random.uniform(self.config.min_relax_duration, self.config.max_relax_duration)
        self.timer.start(int(duration * 1000))
        
    def _enter_cue(self):
        self.state = ExperimentState.CUE
        self.state_changed.emit(self.state)
        
        task_name = self.current_task.name
        self.task_changed.emit(task_name)
        
        # Log event (Cue onset)
        event_timestamp = local_clock()-self.lsl_client.lsl_offset
        self.data_logger.add_event(event_timestamp, self.config.get_marker(self.current_task))
        
        self.timer.start(int(self.config.preparation_duration * 1000))
        
    def _enter_recording(self):
        self.state = ExperimentState.RECORDING
        self.state_changed.emit(self.state)
        
        self.timer.start(int(self.config.recording_duration * 1000))
        
    def _on_timeout(self):
        if self.state == ExperimentState.RELAX:
            self._enter_cue()
        elif self.state == ExperimentState.CUE:
            self._enter_recording()
        elif self.state == ExperimentState.RECORDING:
            # Trial done, move to next
            self.current_trial_idx += 1
            self._next_trial()
            
    def _finish_experiment(self):
        self.stop()
        self.state = ExperimentState.FINISHED
        self.state_changed.emit(self.state)
        self.finished.emit()
