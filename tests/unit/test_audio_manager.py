from unittest.mock import MagicMock, Mock, patch

import pytest

from audio_manager import AudioManager


class TestAudioManager:
    """测试音频管理器"""

    def test_init(self, sample_config, mock_pyaudio):
        """测试初始化"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            assert manager.sample_rate == 48000
            assert manager.channels == 1
            assert manager.chunk_size == 1024
            assert manager.rx_stream is None
            assert manager.tx_stream is None
            assert manager.selected_input_device is None

    def test_get_input_devices(self, sample_config, mock_pyaudio):
        """测试获取输入设备列表"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            devices = manager.get_input_devices()

            assert len(devices) == 2
            assert devices[0]["name"] == "Default Mic"
            assert devices[0]["index"] == 0
            assert devices[1]["name"] == "USB Mic"
            assert devices[1]["index"] == 1

    def test_get_input_devices_empty(self, sample_config):
        """测试获取输入设备列表（无设备）"""
        mock_pyaudio_instance = Mock()
        mock_pyaudio_instance.get_device_count.return_value = 0

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio_instance):
            manager = AudioManager(sample_config)
            devices = manager.get_input_devices()

            assert len(devices) == 0

    def test_set_input_device(self, sample_config, mock_pyaudio):
        """测试设置输入设备"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            manager.set_input_device(1)

            assert manager.selected_input_device == 1

    def test_set_input_device_none(self, sample_config, mock_pyaudio):
        """测试设置输入设备为 None"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            manager.set_input_device(None)

            assert manager.selected_input_device is None

    def test_set_rx_callback(self, sample_config, mock_pyaudio):
        """测试设置接收回调"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            callback = Mock()
            manager.set_rx_callback(callback)

            assert manager.rx_callback == callback

    def test_set_tx_callback(self, sample_config, mock_pyaudio):
        """测试设置发射回调"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            callback = Mock()
            manager.set_tx_callback(callback)

            assert manager.tx_callback == callback

    def test_start_rx(self, sample_config, mock_pyaudio):
        """测试启动接收音频流"""
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_rx()

            mock_pyaudio.open.assert_called_once()
            call_kwargs = mock_pyaudio.open.call_args[1]
            assert call_kwargs["output"] is True
            assert call_kwargs["rate"] == 48000
            assert call_kwargs["channels"] == 1
            assert manager.rx_stream == mock_stream

    def test_start_rx_already_running(self, sample_config, mock_pyaudio):
        """测试启动接收音频流（已运行）"""
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_rx()

            first_call_count = mock_pyaudio.open.call_count

            manager.start_rx()

            assert mock_pyaudio.open.call_count == first_call_count

    def test_stop_rx(self, sample_config, mock_pyaudio):
        """测试停止接收音频流"""
        mock_stream = Mock()
        mock_stream.stop_stream = Mock()
        mock_stream.close = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_rx()
            manager.stop_rx()

            mock_stream.stop_stream.assert_called_once()
            mock_stream.close.assert_called_once()
            assert manager.rx_stream is None

    def test_stop_rx_not_running(self, sample_config, mock_pyaudio):
        """测试停止接收音频流（未运行）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            manager.stop_rx()

            assert manager.rx_stream is None

    def test_start_tx(self, sample_config, mock_pyaudio):
        """测试启动发射音频流"""
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_tx()

            mock_pyaudio.open.assert_called_once()
            call_kwargs = mock_pyaudio.open.call_args[1]
            assert call_kwargs["input"] is True
            assert call_kwargs["rate"] == 48000
            assert call_kwargs["channels"] == 1
            assert manager.tx_stream == mock_stream

    def test_start_tx_with_device(self, sample_config, mock_pyaudio):
        """测试启动发射音频流（指定设备）"""
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.set_input_device(1)
            manager.start_tx()

            call_kwargs = mock_pyaudio.open.call_args[1]
            assert call_kwargs["input_device_index"] == 1

    def test_start_tx_already_running(self, sample_config, mock_pyaudio):
        """测试启动发射音频流（已运行）"""
        mock_stream = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_tx()

            first_call_count = mock_pyaudio.open.call_count

            manager.start_tx()

            assert mock_pyaudio.open.call_count == first_call_count

    def test_stop_tx(self, sample_config, mock_pyaudio):
        """测试停止发射音频流"""
        mock_stream = Mock()
        mock_stream.stop_stream = Mock()
        mock_stream.close = Mock()
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_tx()
            manager.stop_tx()

            mock_stream.stop_stream.assert_called_once()
            mock_stream.close.assert_called_once()
            assert manager.tx_stream is None

    def test_stop_tx_not_running(self, sample_config, mock_pyaudio):
        """测试停止发射音频流（未运行）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            manager.stop_tx()

            assert manager.tx_stream is None

    def test_read_tx_data(self, sample_config, mock_pyaudio):
        """测试读取发射数据"""
        mock_stream = Mock()
        mock_stream.read.return_value = b"test_audio_data"
        mock_pyaudio.open.return_value = mock_stream

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_tx()

            data = manager.read_tx_data()

            assert data == b"test_audio_data"
            mock_stream.read.assert_called_once_with(1024, exception_on_overflow=False)

    def test_read_tx_data_no_stream(self, sample_config, mock_pyaudio):
        """测试读取发射数据（无流）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            data = manager.read_tx_data()

            assert data == b""

    def test_write_rx_data(self, sample_config, mock_pyaudio):
        """测试写入接收数据"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            manager.write_rx_data(b"test_audio_data")

    def test_cleanup(self, sample_config, mock_pyaudio):
        """测试清理资源"""
        mock_rx_stream = Mock()
        mock_rx_stream.stop_stream = Mock()
        mock_rx_stream.close = Mock()

        mock_tx_stream = Mock()
        mock_tx_stream.stop_stream = Mock()
        mock_tx_stream.close = Mock()

        def open_side_effect(**kwargs):
            if kwargs.get("output"):
                return mock_rx_stream
            elif kwargs.get("input"):
                return mock_tx_stream
            return Mock()

        mock_pyaudio.open.side_effect = open_side_effect

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.start_rx()
            manager.start_tx()
            manager.cleanup()

            assert manager.rx_stream is None
            assert manager.tx_stream is None
            mock_pyaudio.terminate.assert_called_once()

    def test_cleanup_no_streams(self, sample_config, mock_pyaudio):
        """测试清理资源（无流）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            manager.cleanup()

            mock_pyaudio.terminate.assert_called_once()

    def test_get_audio_backend(self, sample_config, mock_pyaudio):
        """测试获取音频后端"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)
            backend = manager.get_audio_backend()

            assert backend == "0"

    def test_get_audio_backend_error(self, sample_config):
        """测试获取音频后端（错误）"""
        mock_pyaudio_instance = Mock()
        mock_pyaudio_instance.get_default_output_device_info.side_effect = Exception("Error")

        with patch("pyaudio.PyAudio", return_value=mock_pyaudio_instance):
            manager = AudioManager(sample_config)
            backend = manager.get_audio_backend()

            assert backend == "Unknown"

    def test_rx_stream_callback_with_tx_callback(self, sample_config, mock_pyaudio):
        """测试接收流回调（有发射回调）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            tx_callback = Mock(return_value=b"test_data")
            manager.set_tx_callback(tx_callback)

            data = manager._rx_stream_callback(None, 1024, None, 0)

            assert data[0] == b"test_data"
            tx_callback.assert_called_once()

    def test_rx_stream_callback_without_tx_callback(self, sample_config, mock_pyaudio):
        """测试接收流回调（无发射回调）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            data = manager._rx_stream_callback(None, 1024, None, 0)

            assert len(data[0]) == 2048
            assert data[0] == b"\x00" * 2048

    def test_tx_stream_callback_with_rx_callback(self, sample_config, mock_pyaudio):
        """测试发射流回调（有接收回调）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            rx_callback = Mock()
            manager.set_rx_callback(rx_callback)

            result = manager._tx_stream_callback(b"input_data", 1024, None, 0)

            rx_callback.assert_called_once_with(b"input_data")
            assert result == (None, 0)

    def test_tx_stream_callback_without_rx_callback(self, sample_config, mock_pyaudio):
        """测试发射流回调（无接收回调）"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            result = manager._tx_stream_callback(b"input_data", 1024, None, 0)

            assert result == (None, 0)

    def test_rx_stream_callback_error(self, sample_config, mock_pyaudio):
        """测试接收流回调错误处理"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            tx_callback = Mock(side_effect=Exception("Test error"))
            manager.set_tx_callback(tx_callback)

            data = manager._rx_stream_callback(None, 1024, None, 0)

            assert len(data[0]) == 2048

    def test_tx_stream_callback_error(self, sample_config, mock_pyaudio):
        """测试发射流回调错误处理"""
        with patch("pyaudio.PyAudio", return_value=mock_pyaudio):
            manager = AudioManager(sample_config)

            rx_callback = Mock(side_effect=Exception("Test error"))
            manager.set_rx_callback(rx_callback)

            result = manager._tx_stream_callback(b"input_data", 1024, None, 0)

            assert result == (None, 0)
