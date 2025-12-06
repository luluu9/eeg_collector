from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox)
from PyQt6.QtCore import QTimer, pyqtSlot, Qt
from ..core.lsl_client import LSLClient
from ..core.experiment import ExperimentSession, ExperimentState
from ..core.data_handler import DataLogger
from ..config import ExperimentConfig
from .stimulus_window import StimulusWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EEG Data Collector")
        self.resize(400, 300)
        
        self.lsl_client = LSLClient()
        self.data_logger = DataLogger()
        self.config = ExperimentConfig()
        self.experiment = None
        self.stimulus_window = None
        
        self._init_ui()
        
        # Timer to refresh stream list
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_streams)
        self.refresh_timer.start(2000)
        self.refresh_streams()
        
    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Configuration Group
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()
        
        # Subject ID
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Subject ID:"))
        self.subject_input = QLineEdit("SUBJ01")
        h_layout.addWidget(self.subject_input)
        config_layout.addLayout(h_layout)
        
        # Stream Selection
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("LSL Stream:"))
        self.stream_combo = QComboBox()
        h_layout.addWidget(self.stream_combo)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_streams)
        h_layout.addWidget(self.refresh_btn)
        config_layout.addLayout(h_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Status Group
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Status: Idle")
        status_layout.addWidget(self.status_label)
        self.progress_label = QLabel("Trial: 0 / 0")
        status_layout.addWidget(self.progress_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Controls
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Experiment")
        self.start_btn.clicked.connect(self.start_experiment)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_experiment)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        
    def refresh_streams(self):
        streams = self.lsl_client.find_streams()
        current_text = self.stream_combo.currentText()
        self.stream_combo.clear()
        for s in streams:
            self.stream_combo.addItem(f"{s.name()} ({s.type()})", s)
            
        # Restore selection if possible
        index = self.stream_combo.findText(current_text)
        if index >= 0:
            self.stream_combo.setCurrentIndex(index)
            
    def start_experiment(self):
        # Get selected stream
        idx = self.stream_combo.currentIndex()
        if idx < 0:
            self.status_label.setText("Status: No stream selected")
            return
            
        stream_info = self.stream_combo.itemData(idx)
        
        try:
            self.lsl_client.connect(stream_info)
            self.data_logger.set_stream_info(self.lsl_client.get_info())
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            return
            
        # Create Stimulus Window
        self.stimulus_window = StimulusWindow()
        self.stimulus_window.keyPressed.connect(self.on_stimulus_key_pressed)
        self.stimulus_window.show()
        
        # Create Experiment Session
        self.experiment = ExperimentSession(self.config, self.lsl_client, self.data_logger)
        self.experiment.state_changed.connect(self.on_state_changed)
        self.experiment.task_changed.connect(self.on_task_changed)
        self.experiment.feedback_ready.connect(self.on_feedback_ready)
        self.experiment.progress_updated.connect(self.on_progress_updated)
        self.experiment.finished.connect(self.on_finished)
        
        self.experiment.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.subject_input.setEnabled(False)
        self.stream_combo.setEnabled(False)
        
    def stop_experiment(self):
        if self.experiment:
            self.experiment.stop()
            
        if self.stimulus_window:
            self.stimulus_window.close()
            self.stimulus_window = None
            
        # Save data if we have any (partial run)
        # on_finished calls save, but if we stop manually, on_finished might not be called 
        # or we want to ensure it's saved.
        # on_finished is connected to experiment.finished signal.
        # If we call experiment.stop(), does it emit finished?
        # In experiment.py: stop() sets state to IDLE and emits state_changed.
        # It does NOT emit finished.
        # So we should save here.
        
        subject_id = self.subject_input.text()
        self.data_logger.save(subject_id, "partial")
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.subject_input.setEnabled(True)
        self.stream_combo.setEnabled(True)
        self.status_label.setText("Status: Stopped & Saved")

    def closeEvent(self, event):
        if self.experiment and self.experiment.running:
            self.stop_experiment()
        event.accept()
        
    @pyqtSlot(ExperimentState)
    def on_state_changed(self, state):
        self.status_label.setText(f"Status: {state.name}")
        if state == ExperimentState.FINISHED:
            self.on_finished()
            
    @pyqtSlot(str)
    def on_task_changed(self, task_name):
        if self.stimulus_window:
            self.stimulus_window.set_task(task_name)
                
    @pyqtSlot(int, int)
    def on_progress_updated(self, current, total):
        self.progress_label.setText(f"Trial: {current} / {total}")
        
    @pyqtSlot(str, bool)
    def on_feedback_ready(self, prediction, is_correct):
        if self.stimulus_window:
            self.stimulus_window.show_feedback(prediction, is_correct)
            self.status_label.setText(f"Feedback: {prediction} ({'Correct' if is_correct else 'Wrong'})")
        
    def on_finished(self):
        # Save data
        subject_id = self.subject_input.text()
        # We assume run 1 for now, or could auto-increment
        self.data_logger.save(subject_id, 1)
        
        # We don't want stop_experiment to save AGAIN if we just saved.
        # But stop_experiment logic is good for manual stop.
        # Let's just call stop_experiment but maybe with a flag?
        # Or just let it save twice? No, that's bad.
        
        # Refactor:
        # on_finished -> Save (Completed) -> Reset UI
        # stop_experiment -> Stop -> Save (Partial) -> Reset UI
        
        # Let's keep on_finished saving as "run 1" (completed)
        # And stop_experiment saving as "partial"
        
        # But we need to reset UI.
        if self.experiment:
            self.experiment.stop()
            
        if self.stimulus_window:
            self.stimulus_window.close()
            self.stimulus_window = None
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.subject_input.setEnabled(True)
        self.stream_combo.setEnabled(True)
        
        self.status_label.setText("Status: Finished & Saved")

    def on_stimulus_key_pressed(self, key):
        if key == Qt.Key.Key_Escape:
            self.handle_escape()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.handle_escape()
        super().keyPressEvent(event)

    def handle_escape(self):
        if self.experiment and self.experiment.running:
            if self.experiment.paused:
                # Resume
                self.experiment.resume()
                self.status_label.setText("Status: Resumed")
                if self.stimulus_window:
                    self.stimulus_window.showFullScreen()
            else:
                # Pause
                self.experiment.pause()
                self.status_label.setText("Status: Paused - Press ESC to Resume")
                if self.stimulus_window:
                    self.stimulus_window.showNormal() # Or hide?
                    # User might want to see the main window to check things.
