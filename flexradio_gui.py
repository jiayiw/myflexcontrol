import sys
import asyncio
import logging
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QShortcut,
    QMessageBox,
    QStatusBar,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings
from PyQt6.QtGui import QKeySequence

from config_manager import ConfigManager
from flexradio_client import FlexRadioClient
from flexradio_api import FlexRadioAPI, SliceState
from panadapter_display import PanadapterWidget
from waterfall_display import WaterfallWidget
from audio_manager import AudioManager
from memory_manager import MemoryManager
from settings_dialog import SettingsDialog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FlexRadioGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlexRadio 6400 Control")
        self.resize(1200, 800)

        self.config_manager = ConfigManager()
        self.client = FlexRadioClient(self.config_manager.get_radio_ip())
        self.api = FlexRadioAPI(self.client)
        self.audio_manager = AudioManager(self.config_manager.config)
        self.memory_manager = MemoryManager(max_channels=10)

        self.panadapter = PanadapterWidget()
        self.waterfall = WaterfallWidget(history_lines=100)

        self.connected = False
        self.ptt_active = False
        self.current_frequency = 7150000
        self.current_mode = "usb"

        try:
            self.async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.async_loop)
        except:
            self.async_loop = asyncio.get_event_loop()

        self.setup_ui()
        self.setup_connections()
        self._load_window_geometry()

        self.qt_timer = QTimer()
        self.qt_timer.timeout.connect(self._process_asyncio_tasks)
        self.qt_timer.start(10)

        self.api.add_state_callback(self._on_state_changed)

        logger.info("FlexRadio GUI initialized")

    def _process_asyncio_tasks(self):
        if self.async_loop.is_running():
            return
        try:
            self.async_loop.call_soon(self.async_loop.stop)
            self.async_loop.run_forever()
        except:
            pass

    def setup_ui(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&Settings", self.show_settings)
        file_menu.addAction("&Connect", self.on_connect)
        file_menu.addAction("&Disconnect", self.on_disconnect)
        file_menu.addSeparator()
        file_menu.addAction("&Quit", self.close)

        central_widget = QWidget()
        display_layout = QHBoxLayout()

        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Panadapter"))
        left_panel.addWidget(self.panadapter)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Waterfall"))
        right_panel.addWidget(self.waterfall)

        display_layout.addLayout(left_panel, 1)
        display_layout.addLayout(right_panel, 1)

        central_widget.setLayout(display_layout)

        self.setup_controls(central_widget)
        self.setCentralWidget(central_widget)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def setup_controls(self, central):
        control_panel = QWidget()
        controls_layout = QVBoxLayout()

        ip_layout = QHBoxLayout()
        self.ip_label = QLabel(f"Radio IP: {self.config_manager.get_radio_ip()}")
        ip_layout.addWidget(self.ip_label)
        controls_layout.addLayout(ip_layout)

        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Frequency (MHz):"))
        self.freq_input = QLineEdit("7.150")
        self.freq_input.editingFinished.connect(self.on_frequency_changed)
        freq_layout.addWidget(self.freq_input)
        controls_layout.addLayout(freq_layout)

        band_layout = QHBoxLayout()
        self.band_buttons = []
        bands = [
            ("160m", 1.850, "lsb"),
            ("80m", 3.650, "lsb"),
            ("60m", 5.350, "usb"),
            ("40m", 7.150, "usb"),
            ("30m", 10.125, "usb"),
            ("20m", 14.175, "usb"),
            ("17m", 18.118, "usb"),
            ("15m", 21.250, "usb"),
            ("12m", 24.950, "usb"),
            ("10m", 28.500, "usb"),
        ]
        for band_name, freq_mhz, mode in bands:
            btn = QPushButton(band_name)
            btn.setMinimumWidth(50)
            btn.setEnabled(False)
            self.band_buttons.append((btn, band_name, freq_mhz, mode))
            band_layout.addWidget(btn)
        controls_layout.addLayout(band_layout)

        mode_layout = QHBoxLayout()
        self.usb_btn = QPushButton("USB")
        self.usb_btn.setCheckable(True)
        self.usb_btn.setChecked(True)
        self.lsb_btn = QPushButton("LSB")
        self.lsb_btn.setCheckable(True)
        mode_layout.addWidget(self.usb_btn)
        mode_layout.addWidget(self.lsb_btn)
        controls_layout.addLayout(mode_layout)

        gain_layout = QHBoxLayout()

        rf_gain_layout = QVBoxLayout()
        rf_gain_layout.addWidget(QLabel("RF Power"))
        self.rf_gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.rf_gain_slider.setRange(0, 100)
        self.rf_gain_slider.setValue(50)
        rf_gain_layout.addWidget(self.rf_gain_slider)
        self.rf_gain_label = QLabel("50%")
        rf_gain_layout.addWidget(self.rf_gain_label)

        af_gain_layout = QVBoxLayout()
        af_gain_layout.addWidget(QLabel("AF Gain"))
        self.af_gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.af_gain_slider.setRange(0, 100)
        self.af_gain_slider.setValue(50)
        af_gain_layout.addWidget(self.af_gain_slider)
        self.af_gain_label = QLabel("50%")
        af_gain_layout.addWidget(self.af_gain_label)

        gain_layout.addLayout(rf_gain_layout)
        gain_layout.addLayout(af_gain_layout)
        controls_layout.addLayout(gain_layout)

        ptt_layout = QHBoxLayout()
        self.tx_btn = QPushButton("TX (PTT)")
        self.tx_btn.setCheckable(True)
        self.tx_btn.setStyleSheet("QPushButton:checked { background-color: #d32f2f; }")
        self.rx_btn = QPushButton("RX")
        self.rx_btn.setCheckable(True)
        self.rx_btn.setChecked(True)
        self.rx_btn.setStyleSheet("QPushButton:checked { background-color: #4caf50; }")
        ptt_layout.addWidget(self.tx_btn)
        ptt_layout.addWidget(self.rx_btn)
        controls_layout.addLayout(ptt_layout)

        self.status_label = QLabel("Status: Disconnected")
        controls_layout.addWidget(self.status_label)

        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Memory:"))
        self.memory_buttons = []
        for i in range(10):
            btn = QPushButton(f"M{i + 1}")
            btn.setEnabled(False)
            self.memory_buttons.append(btn)
            memory_layout.addWidget(btn)
        controls_layout.addLayout(memory_layout)

        control_panel.setLayout(controls_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(central)
        main_layout.addWidget(control_panel)

        final_widget = QWidget()
        final_widget.setLayout(main_layout)
        self.setCentralWidget(final_widget)

    def setup_connections(self):
        self.usb_btn.clicked.connect(lambda: self.on_mode_changed("usb"))
        self.lsb_btn.clicked.connect(lambda: self.on_mode_changed("lsb"))
        self.rf_gain_slider.valueChanged.connect(self.on_rf_gain_changed)
        self.af_gain_slider.valueChanged.connect(self.on_af_gain_changed)
        self.tx_btn.clicked.connect(self.on_ptt_toggled)
        self.panadapter.frequency_clicked.connect(self.on_panadapter_clicked)

        for i, btn in enumerate(self.memory_buttons):
            btn.clicked.connect(lambda checked, idx=i: self.on_memory_recall(idx))

        for i, (btn, band_name, freq_mhz, mode) in enumerate(self.band_buttons):
            btn.clicked.connect(lambda checked, idx=i: self.on_band_select(idx))

        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.on_space_key)

        self.memory_manager.load_from_config(self.config_manager.config)
        self._update_memory_buttons()
        self._update_band_buttons()

    def on_connect(self):
        ip = self.config_manager.get_radio_ip()
        self.status_bar.showMessage("Connecting to radio...")

        self.client = FlexRadioClient(ip)
        self.api = FlexRadioAPI(self.client)
        self.api.add_state_callback(self._on_state_changed)

        async def connect_task():
            if await self.client.connect():
                logger.info("Connected to radio")
                if await self.api.connect():
                    slice_id = await self.api.create_slice(mode="usb")
                    if slice_id:
                        logger.info(f"Slice created: {slice_id}")
                        await self.api.enable_panadapter()
                        await self.api.enable_rx_audio()
                        self.connected = True
                        self._update_memory_buttons()
                        self._update_band_buttons()
                        self.update_status()
                        self.status_bar.showMessage("Connected to radio", 3000)
                    else:
                        logger.error("Failed to create slice")
                        self.status_bar.showMessage("Failed to create slice", 5000)
                        QMessageBox.warning(
                            self,
                            "Connection Error",
                            "Failed to create radio slice. Please check radio settings.",
                        )
                else:
                    logger.error("Failed to connect API")
                    self.status_bar.showMessage("API connection failed", 5000)
                    QMessageBox.warning(
                        self,
                        "Connection Error",
                        "Failed to initialize radio API. Please check radio settings.",
                    )
            else:
                logger.error("Failed to connect to radio")
                self.status_bar.showMessage("Connection failed", 5000)
                QMessageBox.warning(
                    self,
                    "Connection Error",
                    f"Failed to connect to radio at {ip}.\n\n"
                    "Please check:\n"
                    "1. Radio IP address is correct\n"
                    "2. Radio is powered on\n"
                    "3. Radio is on the same network\n"
                    "4. No firewall blocking port 4992",
                )

        asyncio.run_coroutine_threadsafe(connect_task(), self.async_loop)

    def on_disconnect(self):
        self.status_bar.showMessage("Disconnecting...")

        async def disconnect_task():
            await self.api.disconnect()
            await self.client.disconnect()
            self.audio_manager.cleanup()
            self.connected = False
            self.ptt_active = False
            self._update_memory_buttons()
            self._update_band_buttons()
            self.update_status()
            self.status_bar.showMessage("Disconnected", 3000)

        asyncio.run_coroutine_threadsafe(disconnect_task(), self.async_loop)

    def on_frequency_changed(self):
        try:
            text = self.freq_input.text().strip()
            hz = int(float(text) * 1_000_000)

            async def task():
                await self.api.set_frequency(hz)

            asyncio.run_coroutine_threadsafe(task(), self.async_loop)
        except ValueError:
            pass

    def on_mode_changed(self, mode):
        self.current_mode = mode
        self.usb_btn.setChecked(mode == "usb")
        self.lsb_btn.setChecked(mode == "lsb")
        self.update_status()

        async def task():
            await self.api.set_mode(mode)

        asyncio.run_coroutine_threadsafe(task(), self.async_loop)

    def on_rf_gain_changed(self, value):
        self.rf_gain_label.setText(f"{value}%")

        async def task():
            await self.api.set_rf_gain(value)

        asyncio.run_coroutine_threadsafe(task(), self.async_loop)
        self.update_status()

    def on_af_gain_changed(self, value):
        self.af_gain_label.setText(f"{value}%")

        async def task():
            await self.api.set_af_gain(value)

        asyncio.run_coroutine_threadsafe(task(), self.async_loop)
        self.update_status()

    def on_ptt_toggled(self, checked):
        if self.connected:
            self.ptt_active = checked
            self.tx_btn.setChecked(checked)
            self.rx_btn.setChecked(not checked)

            async def task():
                if checked:
                    self.audio_manager.start_tx()
                    await self.api.set_ptt(True)
                else:
                    self.audio_manager.stop_tx()
                    await self.api.set_ptt(False)
                self.update_status()

            asyncio.run_coroutine_threadsafe(task(), self.async_loop)
        else:
            self.tx_btn.setChecked(False)
            self.rx_btn.setChecked(True)

    def on_space_key(self):
        new_state = not self.ptt_active
        self.on_ptt_toggled(new_state)

    def on_panadapter_clicked(self, frequency_hz):
        self.freq_input.setText(f"{frequency_hz / 1_000_000:.3f}")

        async def task():
            await self.api.set_frequency(frequency_hz)

        asyncio.run_coroutine_threadsafe(task(), self.async_loop)

    def on_memory_recall(self, index):
        channel = self.memory_manager.get_channel(index)
        if channel and self.connected:
            self.freq_input.setText(f"{channel.frequency / 1_000_000:.3f}")
            self.on_mode_changed(channel.mode)
            self.rf_gain_slider.setValue(channel.rf_gain)

            async def task():
                await self.api.set_frequency(channel.frequency)
                await self.api.set_mode(channel.mode)
                await self.api.set_rf_gain(channel.rf_gain)

            asyncio.run_coroutine_threadsafe(task(), self.async_loop)

    def show_settings(self):
        dialog = SettingsDialog(self.config_manager, self.audio_manager, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def _on_settings_changed(self, settings):
        if "radio.ip_address" in settings:
            self.ip_label.setText(f"Radio IP: {settings['radio.ip_address']}")
            if not self.connected:
                self.client.host = settings["radio.ip_address"]

    def _update_memory_buttons(self):
        channels = self.memory_manager.all_channels()
        for i, btn in enumerate(self.memory_buttons):
            if i < len(channels):
                btn.setText(channels[i].name)
                btn.setEnabled(self.connected)
            else:
                btn.setText(f"M{i + 1}")
                btn.setEnabled(False)

    def _update_band_buttons(self):
        for btn in self.band_buttons:
            btn[0].setEnabled(self.connected)

    def on_band_select(self, index):
        if not self.connected:
            return

        btn, band_name, freq_mhz, mode = self.band_buttons[index]
        self.freq_input.setText(f"{freq_mhz:.3f}")
        self.on_mode_changed(mode)

        hz = int(freq_mhz * 1_000_000)

        async def task():
            await self.api.set_frequency(hz)
            await self.api.set_mode(mode)

        asyncio.run_coroutine_threadsafe(task(), self.async_loop)
        self.status_bar.showMessage(f"Switched to {band_name} band", 2000)

    def _load_window_geometry(self):
        settings = QSettings("FlexRadio", "FlexRadioControl")
        geometry = settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = settings.value("window_state")
        if state:
            self.restoreState(state)

    def _save_window_geometry(self):
        settings = QSettings("FlexRadio", "FlexRadioControl")
        settings.setValue("window_geometry", self.saveGeometry())
        settings.setValue("window_state", self.saveState())

    def _on_state_changed(self, state):
        if state.frequency != self.current_frequency:
            self.current_frequency = state.frequency
            self.freq_input.setText(f"{state.frequency / 1_000_000:.3f}")
        if state.mode != self.current_mode:
            self.current_mode = state.mode
            self.usb_btn.setChecked(state.mode == "usb")
            self.lsb_btn.setChecked(state.mode == "lsb")

    def update_status(self):
        if not self.connected:
            self.status_label.setText("Status: Disconnected")
        elif self.ptt_active:
            self.status_label.setText(
                f"Status: TX - {self.freq_input.text()} MHz {self.current_mode.upper()}"
            )
        else:
            self.status_label.setText(
                f"Status: RX - {self.freq_input.text()} MHz {self.current_mode.upper()}"
            )

    def closeEvent(self, event):
        self._save_window_geometry()

        async def cleanup():
            await self.api.disconnect()
            await self.client.disconnect()
            self.audio_manager.cleanup()

        asyncio.run_coroutine_threadsafe(cleanup(), self.async_loop)
        super().closeEvent(event)
