import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication


@pytest.mark.integration
class TestFlexRadioGUI:
    """测试 GUI 关键路径"""

    @pytest.fixture
    def gui_app(self, qapp, temp_config_dir, mock_pyaudio, mock_client):
        """创建 GUI 应用实例"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            with patch("flexradio_gui.FlexRadioClient", return_value=mock_client):
                with patch("flexradio_gui.AudioManager") as mock_audio:
                    mock_audio_instance = mock_audio.return_value
                    mock_audio_instance.get_input_devices.return_value = [
                        {"name": "Default Mic", "index": 0}
                    ]
                    mock_audio_instance.get_audio_backend.return_value = "pipewire"

                    from flexradio_gui import FlexRadioGUI

                    window = FlexRadioGUI()
                    yield window

    def test_window_initialization(self, gui_app):
        """测试窗口初始化"""
        assert gui_app.windowTitle() == "FlexRadio 6400 Control"
        assert gui_app.freq_input is not None
        assert gui_app.usb_btn is not None
        assert gui_app.lsb_btn is not None
        assert gui_app.rf_gain_slider is not None
        assert gui_app.af_gain_slider is not None
        assert gui_app.tx_btn is not None
        assert gui_app.rx_btn is not None

    def test_initial_frequency(self, gui_app):
        """测试初始频率"""
        assert gui_app.freq_input.text() == "7.150"
        assert gui_app.current_frequency == 7150000

    def test_initial_mode(self, gui_app):
        """测试初始模式"""
        assert gui_app.current_mode == "usb"
        assert gui_app.usb_btn.isChecked() is True
        assert gui_app.lsb_btn.isChecked() is False

    def test_frequency_input_change(self, gui_app, qtbot):
        """测试频率输入更改"""
        gui_app.freq_input.setText("14.250")
        gui_app.freq_input.editingFinished.emit()

        assert gui_app.current_frequency == 14250000

    def test_mode_switch_to_lsb(self, gui_app, qtbot):
        """测试切换到 LSB 模式"""
        gui_app.lsb_btn.click()

        assert gui_app.current_mode == "lsb"
        assert gui_app.lsb_btn.isChecked() is True
        assert gui_app.usb_btn.isChecked() is False

    def test_mode_switch_to_usb(self, gui_app, qtbot):
        """测试切换到 USB 模式"""
        gui_app.lsb_btn.click()
        gui_app.usb_btn.click()

        assert gui_app.current_mode == "usb"
        assert gui_app.usb_btn.isChecked() is True
        assert gui_app.lsb_btn.isChecked() is False

    def test_rf_gain_slider(self, gui_app, qtbot):
        """测试 RF 增益滑块"""
        gui_app.rf_gain_slider.setValue(75)

        assert gui_app.rf_gain_label.text() == "75%"

    def test_af_gain_slider(self, gui_app, qtbot):
        """测试 AF 增益滑块"""
        gui_app.af_gain_slider.setValue(80)

        assert gui_app.af_gain_label.text() == "80%"

    def test_ptt_button_toggle(self, gui_app, qtbot):
        """测试 PTT 按钮切换"""
        gui_app.connected = True

        gui_app.tx_btn.click()
        assert gui_app.ptt_active is True
        assert gui_app.tx_btn.isChecked() is True
        assert gui_app.rx_btn.isChecked() is False

        gui_app.tx_btn.click()
        assert gui_app.ptt_active is False
        assert gui_app.tx_btn.isChecked() is False
        assert gui_app.rx_btn.isChecked() is True

    def test_ptt_button_when_disconnected(self, gui_app, qtbot):
        """测试断开连接时的 PTT 按钮"""
        gui_app.connected = False

        gui_app.tx_btn.click()

        assert gui_app.ptt_active is False
        assert gui_app.tx_btn.isChecked() is False
        assert gui_app.rx_btn.isChecked() is True

    def test_space_key_ptt(self, gui_app, qtbot):
        """测试空格键 PTT 控制"""
        gui_app.connected = True

        qtbot.keyPress(gui_app, Qt.Key.Key_Space)
        assert gui_app.ptt_active is True

        qtbot.keyPress(gui_app, Qt.Key.Key_Space)
        assert gui_app.ptt_active is False

    def test_status_display_disconnected(self, gui_app):
        """测试断开连接时的状态显示"""
        gui_app.connected = False
        gui_app.update_status()

        assert "Disconnected" in gui_app.status_label.text()

    def test_status_display_rx(self, gui_app):
        """测试接收状态显示"""
        gui_app.connected = True
        gui_app.ptt_active = False
        gui_app.update_status()

        assert "RX" in gui_app.status_label.text()

    def test_status_display_tx(self, gui_app):
        """测试发射状态显示"""
        gui_app.connected = True
        gui_app.ptt_active = True
        gui_app.update_status()

        assert "TX" in gui_app.status_label.text()

    def test_memory_buttons_initial_state(self, gui_app):
        """测试存储按钮初始状态"""
        for btn in gui_app.memory_buttons:
            assert btn.isEnabled() is False

    def test_band_buttons_initial_state(self, gui_app):
        """测试波段按钮初始状态"""
        for btn, _, _, _ in gui_app.band_buttons:
            assert btn.isEnabled() is False

    def test_update_memory_buttons_when_connected(self, gui_app):
        """测试连接时更新存储按钮"""
        gui_app.connected = True
        gui_app._update_memory_buttons()

        channels = gui_app.memory_manager.all_channels()
        for i, btn in enumerate(gui_app.memory_buttons):
            if i < len(channels):
                assert btn.isEnabled() is True
            else:
                assert btn.isEnabled() is False

    def test_update_band_buttons_when_connected(self, gui_app):
        """测试连接时更新波段按钮"""
        gui_app.connected = True
        gui_app._update_band_buttons()

        for btn, _, _, _ in gui_app.band_buttons:
            assert btn.isEnabled() is True

    def test_band_selection_40m(self, gui_app, qtbot):
        """测试选择 40m 波段"""
        gui_app.connected = True
        gui_app._update_band_buttons()

        gui_app.band_buttons[3][0].click()

        assert gui_app.freq_input.text() == "7.150"
        assert gui_app.current_mode == "usb"

    def test_band_selection_20m(self, gui_app, qtbot):
        """测试选择 20m 波段"""
        gui_app.connected = True
        gui_app._update_band_buttons()

        gui_app.band_buttons[5][0].click()

        assert gui_app.freq_input.text() == "14.175"
        assert gui_app.current_mode == "usb"

    def test_memory_recall(self, gui_app, qtbot, sample_config):
        """测试存储信道召回"""
        gui_app.connected = True
        gui_app.memory_manager.load_from_config(sample_config)
        gui_app._update_memory_buttons()

        gui_app.memory_buttons[0].click()

        assert gui_app.freq_input.text() == "7.150"
        assert gui_app.current_mode == "usb"

    def test_on_state_changed_frequency(self, gui_app):
        """测试状态改变（频率）"""
        from flexradio_api import SliceState

        state = SliceState()
        state.frequency = 14250000

        gui_app._on_state_changed(state)

        assert gui_app.current_frequency == 14250000
        assert gui_app.freq_input.text() == "14.250"

    def test_on_state_changed_mode(self, gui_app):
        """测试状态改变（模式）"""
        from flexradio_api import SliceState

        state = SliceState()
        state.mode = "lsb"

        gui_app._on_state_changed(state)

        assert gui_app.current_mode == "lsb"
        assert gui_app.lsb_btn.isChecked() is True
        assert gui_app.usb_btn.isChecked() is False

    def test_window_geometry_save_load(self, gui_app, qtbot):
        """测试窗口几何状态保存和加载"""
        original_size = gui_app.size()

        gui_app.resize(1400, 900)
        gui_app._save_window_geometry()

        gui_app._load_window_geometry()

    def test_settings_dialog_open(self, gui_app, qtbot):
        """测试打开设置对话框"""
        with patch("flexradio_gui.SettingsDialog") as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog_instance.exec.return_value = 0
            mock_dialog.return_value = mock_dialog_instance

            gui_app.show_settings()

            mock_dialog.assert_called_once()

    def test_on_settings_changed_ip(self, gui_app):
        """测试设置更改（IP 地址）"""
        settings = {"radio.ip_address": "192.168.1.200"}

        gui_app._on_settings_changed(settings)

        assert gui_app.ip_label.text() == "Radio IP: 192.168.1.200"

    def test_invalid_frequency_input(self, gui_app, qtbot):
        """测试无效频率输入"""
        original_freq = gui_app.current_frequency

        gui_app.freq_input.setText("invalid")
        gui_app.freq_input.editingFinished.emit()

        assert gui_app.current_frequency == original_freq

    def test_frequency_input_with_spaces(self, gui_app, qtbot):
        """测试带空格的频率输入"""
        gui_app.freq_input.setText(" 14.250 ")
        gui_app.freq_input.editingFinished.emit()

        assert gui_app.current_frequency == 14250000

    def test_frequency_input_in_mhz(self, gui_app, qtbot):
        """测试 MHz 频率输入"""
        gui_app.freq_input.setText("7.150")
        gui_app.freq_input.editingFinished.emit()

        assert gui_app.current_frequency == 7150000

    def test_close_event(self, gui_app):
        """测试关闭事件"""
        with patch.object(gui_app, "_save_window_geometry"):
            with patch.object(gui_app, "audio_manager") as mock_audio:
                mock_audio.cleanup = Mock()

                event = Mock()
                event.accept = Mock()

                gui_app.closeEvent(event)

                gui_app._save_window_geometry.assert_called_once()
                mock_audio.cleanup.assert_called_once()
