import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from config_manager import ConfigManager
from flexradio_api import FlexRadioAPI
from flexradio_client import FlexRadioClient
from memory_manager import MemoryManager


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndFlow:
    """测试完整的端到端流程"""

    @pytest.mark.asyncio
    async def test_complete_connection_flow(self, mock_client, mock_radio_responses):
        """测试完整连接流程"""
        responses = mock_radio_responses["responses"]

        mock_client.send_command.side_effect = [
            responses["client_udpport"],
            responses["slice_create"],
            responses["slice_set_mode"],
            responses["pan_create"],
            responses["audio_create_rx"],
        ]

        api = FlexRadioAPI(mock_client)

        connected = await api.connect()
        assert connected is True

        slice_id = await api.create_slice("usb")
        assert slice_id == "1"

        await api.enable_panadapter()
        assert api.pan_id == "0x40000000"

        await api.enable_rx_audio()

        assert mock_client.send_command.call_count == 5

    @pytest.mark.asyncio
    async def test_tune_and_transmit_flow(self, mock_client):
        """测试调谐和发射流程"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.set_frequency(14250000)
        assert api.slice_state.frequency == 14250000

        await api.set_mode("usb")
        assert api.slice_state.mode == "usb"

        await api.set_rf_gain(75)
        assert api.slice_state.rf_gain == 75

        await api.set_af_gain(80)
        assert api.slice_state.af_gain == 80

        await api.set_ptt(True)
        assert api.slice_state.ptt is True

        await api.set_ptt(False)
        assert api.slice_state.ptt is False

        calls = mock_client.send_command.call_args_list
        assert len(calls) == 6
        assert "frequency=14250000" in calls[0][0][0]
        assert "mode=usb" in calls[1][0][0]
        assert "rfpower=75" in calls[2][0][0]
        assert "af_gain=80" in calls[3][0][0]
        assert "xmit 1" in calls[4][0][0]
        assert "xmit off" in calls[5][0][0]

    def test_memory_channel_flow(self, temp_config_dir, sample_config):
        """测试存储信道完整流程"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            config_manager = ConfigManager()

            memory_manager = MemoryManager(max_channels=10)
            memory_manager.load_from_config(config_manager.config)

            initial_count = len(memory_manager.channels)

            from memory_manager import MemoryChannel

            new_channel = MemoryChannel("15m USB", 21250000, "usb", 60, 50)
            assert memory_manager.add_channel(new_channel) is True

            assert len(memory_manager.channels) == initial_count + 1

            updated = MemoryChannel("15m USB Updated", 21300000, "usb", 65, 55)
            assert memory_manager.update_channel(len(memory_manager.channels) - 1, updated) is True

            config_update = memory_manager.save_to_config()
            config_manager.config.update(config_update)
            config_manager.save_config()

            config_manager2 = ConfigManager()
            memory_manager2 = MemoryManager()
            memory_manager2.load_from_config(config_manager2.config)

            assert len(memory_manager2.channels) == initial_count + 1
            last_channel = memory_manager2.channels[-1]
            assert last_channel.name == "15m USB Updated"
            assert last_channel.frequency == 21300000

    @pytest.mark.asyncio
    async def test_frequency_mode_sequence(self, mock_client):
        """测试频率和模式序列操作"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        frequencies = [7150000, 14250000, 21250000]
        modes = ["usb", "lsb", "usb"]

        for freq, mode in zip(frequencies, modes):
            await api.set_frequency(freq)
            await api.set_mode(mode)

            assert api.slice_state.frequency == freq
            assert api.slice_state.mode == mode

        assert mock_client.send_command.call_count == len(frequencies) * 2

    @pytest.mark.asyncio
    async def test_error_handling_flow(self, mock_client):
        """测试错误处理流程"""
        mock_client.connect = AsyncMock(return_value=False)

        client = FlexRadioClient("invalid_ip")
        result = await client.connect()

        assert result is False

        mock_client.send_command.side_effect = TimeoutError("Timeout")

        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        with pytest.raises(TimeoutError):
            await api.set_frequency(7150000)

    @pytest.mark.asyncio
    async def test_state_update_flow(self, mock_client):
        """测试状态更新流程"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        callback = Mock()
        api.add_state_callback(callback)

        api._handle_status("S|slice|1|frequency=14250000")

        assert api.slice_state.frequency == 14250000
        callback.assert_called_once()

        api._handle_status("S|slice|1|mode=lsb")

        assert api.slice_state.mode == "lsb"
        assert callback.call_count == 2

    @pytest.mark.asyncio
    async def test_full_session_flow(self, mock_client, mock_radio_responses):
        """测试完整会话流程"""
        responses = mock_radio_responses["responses"]

        mock_client.send_command.side_effect = [
            responses["client_udpport"],
            responses["slice_create"],
            responses["slice_set_frequency"],
            responses["slice_set_mode"],
            responses["slice_set_rfpower"],
            responses["xmit_on"],
            responses["xmit_off"],
            responses["slice_remove"],
        ]

        api = FlexRadioAPI(mock_client)

        await api.connect()
        slice_id = await api.create_slice("usb")

        await api.set_frequency(7150000)
        await api.set_mode("usb")
        await api.set_rf_gain(50)

        await api.set_ptt(True)
        await api.set_ptt(False)

        await api.disconnect()

        assert mock_client.send_command.call_count == 8
        assert api.slice_id is None

    def test_config_memory_integration(self, temp_config_dir, sample_config):
        """测试配置和存储集成"""
        with patch.object(Path, "home", return_value=temp_config_dir.parent):
            config_manager = ConfigManager()

            memory_manager = MemoryManager()
            memory_manager.load_from_config(config_manager.config)

            assert len(memory_manager.channels) > 0

            for channel in memory_manager.channels:
                assert channel.frequency > 0
                assert channel.mode in ["usb", "lsb"]
                assert 0 <= channel.rf_gain <= 100

    @pytest.mark.asyncio
    async def test_multiple_frequency_changes(self, mock_client):
        """测试多次频率更改"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        test_frequencies = [1800000, 3500000, 7000000, 14000000, 21000000, 28000000]

        for freq in test_frequencies:
            await api.set_frequency(freq)
            assert api.slice_state.frequency == freq

        assert mock_client.send_command.call_count == len(test_frequencies)

    @pytest.mark.asyncio
    async def test_panadapter_audio_flow(self, mock_client, mock_radio_responses):
        """测试 panadapter 和音频流程"""
        responses = mock_radio_responses["responses"]

        mock_client.send_command.side_effect = [
            responses["pan_create"],
            responses["audio_create_rx"],
            responses["audio_create_tx"],
            responses["pan_remove"],
            responses["audio_remove"],
        ]

        api = FlexRadioAPI(mock_client)

        result = await api.enable_panadapter()
        assert result is not None

        await api.enable_rx_audio()
        await api.enable_tx_audio()

        await api.disable_panadapter()
        await api.disable_audio()

        assert api.pan_id is None

    @pytest.mark.asyncio
    async def test_concurrent_state_updates(self, mock_client):
        """测试并发状态更新"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        status_messages = [
            "S|slice|1|frequency=7150000",
            "S|slice|1|mode=usb",
            "S|slice|1|rfpower=50",
            "S|slice|1|af_gain=60",
        ]

        for msg in status_messages:
            api._handle_status(msg)

        assert api.slice_state.frequency == 7150000
        assert api.slice_state.mode == "usb"
        assert api.slice_state.rf_gain == 50
        assert api.slice_state.af_gain == 60
