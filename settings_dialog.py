from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
)
from PyQt6.QtCore import pyqtSignal, QObject


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, config_manager, audio_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.audio_manager = audio_manager
        self.setWindowTitle("Settings")
        self.resize(500, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Radio IP Address:"))
        self.ip_input = QLineEdit(self.config_manager.get("radio.ip_address"))
        ip_layout.addWidget(self.ip_input)
        layout.addLayout(ip_layout)

        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Panadapter Width:"))
        self.width_input = QSpinBox()
        self.width_input.setRange(512, 4096)
        self.width_input.setValue(
            self.config_manager.get("display.panadapter_width", 1024)
        )
        width_layout.addWidget(self.width_input)
        layout.addLayout(width_layout)

        mic_layout = QHBoxLayout()
        mic_layout.addWidget(QLabel("Microphone:"))
        self.mic_combo = QComboBox()

        try:
            devices = self.audio_manager.get_input_devices()
            self.mic_combo.addItem("Default (System)", None)
            for device in devices:
                self.mic_combo.addItem(f"{device['name']}", device["index"])

            current_mic = self.config_manager.get("audio.input_device")
            index = self.mic_combo.findData(current_mic)
            if index >= 0:
                self.mic_combo.setCurrentIndex(index)
        except Exception as e:
            self.mic_combo.addItem("Default (System)", None)

        mic_layout.addWidget(self.mic_combo)
        layout.addLayout(mic_layout)

        backend_info_label = QLabel(
            f"Audio Backend: {self.audio_manager.get_audio_backend()}"
        )
        layout.addWidget(backend_info_label)

        layout.addStretch()

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def accept(self):
        settings = {}
        settings["radio.ip_address"] = self.ip_input.text()
        settings["display.panadapter_width"] = self.width_input.value()

        mic_index = self.mic_combo.currentData()
        settings["audio.input_device"] = mic_index

        if mic_index is not None:
            self.audio_manager.set_input_device(mic_index)

        self.settings_changed.emit(settings)
        super().accept()
