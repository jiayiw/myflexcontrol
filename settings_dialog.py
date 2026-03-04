import logging
import os
import re

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
)

from ai_denoiser.detector import detect_gpu
from ai_denoiser.model_manager import get_status_message, needs_download, download_model

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, config_manager, audio_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.audio_manager = audio_manager
        self.setWindowTitle("Settings")
        self.resize(550, 450)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # === Radio Settings ===
        radio_group = QGroupBox("Radio Settings")
        radio_layout = QVBoxLayout()

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Radio IP Address:"))
        self.ip_input = QLineEdit(self.config_manager.get("radio.ip_address"))
        ip_layout.addWidget(self.ip_input)
        radio_layout.addLayout(ip_layout)

        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Panadapter Width:"))
        self.width_input = QSpinBox()
        self.width_input.setRange(512, 4096)
        self.width_input.setValue(
            self.config_manager.get("display.panadapter_width", 1024)
        )
        width_layout.addWidget(self.width_input)
        radio_layout.addLayout(width_layout)

        radio_group.setLayout(radio_layout)
        layout.addWidget(radio_group)

        # === Audio Settings ===
        audio_group = QGroupBox("Audio Settings")
        audio_layout = QVBoxLayout()

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
            logger.warning(f"Failed to get input devices: {e}")
            self.mic_combo.addItem("Default (System)", None)

        mic_layout.addWidget(self.mic_combo)
        audio_layout.addLayout(mic_layout)

        backend_info_label = QLabel(
            f"Audio Backend: {self.audio_manager.get_audio_backend()}"
        )
        audio_layout.addWidget(backend_info_label)

        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)

        # === AI Denoiser Settings ===
        self.ai_group = QGroupBox("AI Audio Denoiser (Experimental)")
        ai_layout = QVBoxLayout()

        # AI Denoiser checkbox
        self.ai_checkbox = QCheckBox("Enable AI Denoising")
        self.ai_checkbox.setChecked(
            self.config_manager.get("ai_denoiser.enabled", False)
        )
        self.ai_checkbox.stateChanged.connect(self._on_ai_checkbox_changed)
        ai_layout.addWidget(self.ai_checkbox)

        # GPU status label
        gpu_info = detect_gpu()
        if gpu_info.get("meets_requirement", False):
            self.gpu_label = QLabel(
                f"✓ GPU Detected: {gpu_info['name']} ({gpu_info['memory_gb']:.1f}GB VRAM)\n"
                "   Using SpeechBrain (GPU-accelerated) with ~100ms latency"
            )
            self.gpu_label.setStyleSheet("color: green;")
        elif gpu_info.get("available", False):
            self.gpu_label = QLabel(
                f"⚠ GPU Insufficient: {gpu_info['name']} ({gpu_info['memory_gb']:.1f}GB VRAM)\n"
                f"   Need ≥8GB for GPU mode. Using CPU mode (DeepFilterNet) with ~10ms latency"
            )
            self.gpu_label.setStyleSheet("color: orange;")
            # CPU fallback checkbox
            self.cpu_fallback_checkbox = QCheckBox("Use CPU mode (DeepFilterNet)")
            self.cpu_fallback_checkbox.setChecked(
                self.config_manager.get("ai_denoiser.manual_fallback", False)
            )
            self.cpu_fallback_checkbox.setEnabled(False)
            if self.ai_checkbox.isChecked():
                self.cpu_fallback_checkbox.setEnabled(True)
            ai_layout.addWidget(self.cpu_fallback_checkbox)
        else:
            self.gpu_label = QLabel(
                "✗ No suitable GPU detected\n"
                "   CPU mode (DeepFilterNet) will be used with ~10ms latency\n"
                "   For GPU mode, install CUDA-capable GPU with ≥8GB VRAM"
            )
            self.gpu_label.setStyleSheet("color: red;")
            # CPU fallback checkbox (always enabled when no GPU)
            self.cpu_fallback_checkbox = QCheckBox("Use CPU mode (DeepFilterNet)")
            self.cpu_fallback_checkbox.setChecked(
                self.config_manager.get("ai_denoiser.manual_fallback", False)
            )
            ai_layout.addWidget(self.cpu_fallback_checkbox)

        ai_layout.addWidget(self.gpu_label)

        self.ai_status_label = QLabel(
            get_status_message(self.config_manager.get("ai_denoiser", {}))
        )
        self.ai_status_label.setWordWrap(True)
        ai_layout.addWidget(self.ai_status_label)

        # Download button
        self.ai_download_btn = QPushButton("Download Models")
        self.ai_download_btn.clicked.connect(self._handle_download)
        ai_layout.addWidget(self.ai_download_btn)

        self.ai_group.setLayout(ai_layout)
        layout.addWidget(self.ai_group)

        layout.addStretch()

        # === Buttons ===
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _on_ai_checkbox_changed(self, state):
        """Handle AI denoiser checkbox state change"""
        enabled = state == 2  # Qt.CheckState.Checked = 2

        # Enable/disable download button based on whether models need downloading
        download_status = needs_download(self.config_manager.get("ai_denoiser", {}))
        if not download_status.get(
            "speechbrain_needed", False
        ) and not download_status.get("deepfilter_needed", False):
            self.ai_download_btn.setText("Models downloaded")
            self.ai_download_btn.setEnabled(False)
        else:
            self.ai_download_btn.setText("Download Models")
            self.ai_download_btn.setEnabled(enabled)

        # Update CPU fallback checkbox availability
        if hasattr(self, "cpu_fallback_checkbox"):
            gpu_info = detect_gpu()
            if gpu_info.get("available") and not gpu_info.get("meets_requirement"):
                self.cpu_fallback_checkbox.setEnabled(enabled)

    def _handle_download(self):
        """Handle model download with user confirmation"""
        download_status = needs_download(self.config_manager.get("ai_denoiser", {}))

        gpu_info = detect_gpu()

        if gpu_info.get("meets_requirement"):
            msg = (
                f"Download ~400MB SpeechBrain model for GPU-accelerated denoising\n"
                f"to: {self.config_manager.get('ai_denoiser.model_cache_dir')}\n\n"
                f"Continue?"
            )
        else:
            msg = (
                f"Download ~10MB DeepFilterNet model for CPU denoising\n"
                f"to: {self.config_manager.get('ai_denoiser.model_cache_dir')}\n\n"
                f"Continue?"
            )

        reply = QMessageBox.question(
            self,
            "Download AI Denoiser Model",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Mark auto_download for download_model function
            self.config_manager.set("ai_denoiser.auto_download", True)
            self.config_manager.save_config()

            # Perform download
            from ai_denoiser.model_manager import download_model

            cache_dir = self.config_manager.get(
                "ai_denoiser.model_cache_dir",
                os.path.expanduser("~/.cache/flexradio/ai_models"),
            )

            if gpu_info.get("meets_requirement"):
                success = download_model("speechbrain", cache_dir)
            else:
                success = download_model("deepfilter", cache_dir)

            if success:
                QMessageBox.information(
                    self, "Download Complete", "Model downloaded successfully."
                )
                self.ai_status_label.setText("Models downloaded and ready.")
                self._on_ai_checkbox_changed(self.ai_checkbox.checkState())
            else:
                QMessageBox.warning(
                    self,
                    "Download Failed",
                    "Failed to download model. Please check your internet connection.",
                )

    def accept(self):
        """Accept settings with validation"""
        ip = self.ip_input.text().strip()

        if not self._validate_ip_address(ip):
            QMessageBox.warning(
                self,
                "Invalid IP Address",
                "Please enter a valid IP address (e.g., 192.168.1.100)",
            )
            return

        # Save settings
        settings = {}
        settings["radio.ip_address"] = ip
        settings["display.panadapter_width"] = self.width_input.value()
        settings["audio.input_device"] = self.mic_combo.currentData()

        # AI Denoiser settings
        ai_enabled = self.ai_checkbox.isChecked()
        settings["ai_denoiser.enabled"] = ai_enabled

        if (
            hasattr(self, "cpu_fallback_checkbox")
            and self.cpu_fallback_checkbox.isEnabled()
        ):
            settings["ai_denoiser.manual_fallback"] = (
                self.cpu_fallback_checkbox.isChecked()
            )

        # Emit changes
        if hasattr(self, "ai_group") and ai_enabled and self.ai_group.isVisible():
            settings["ai_denoiser.enabled"] = ai_enabled

        if settings["audio.input_device"] is not None:
            self.audio_manager.set_input_device(settings["audio.input_device"])

        self.settings_changed.emit(settings)
        super().accept()

    def _validate_ip_address(self, ip: str) -> bool:
        """Validate IP address format"""
        pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(pattern, ip.strip()):
            return False
        parts = ip.strip().split(".")
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
