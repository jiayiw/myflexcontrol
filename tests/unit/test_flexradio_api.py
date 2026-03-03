from unittest.mock import AsyncMock, Mock, call

import pytest

from flexradio_api import FlexRadioAPI, SliceState


class TestFlexRadioAPI:
    """测试 FlexRadio API 层"""

    def test_init(self, mock_client):
        """测试初始化"""
        api = FlexRadioAPI(mock_client)

        assert api.client == mock_client
        assert api.slice_id is None
        assert api.pan_id is None
        assert isinstance(api.slice_state, SliceState)
        assert len(api.state_callbacks) == 0
        mock_client.set_status_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_success(self, mock_client, mock_radio_responses):
        """测试 API 连接成功"""
        api = FlexRadioAPI(mock_client)
        mock_client.send_command.return_value = mock_radio_responses["responses"]["client_udpport"]

        result = await api.connect()

        assert result is True
        mock_client.send_command.assert_called_once_with("client udpport 4991")

    @pytest.mark.asyncio
    async def test_connect_failure(self, mock_client):
        """测试 API 连接失败"""
        api = FlexRadioAPI(mock_client)
        mock_client.send_command.side_effect = Exception("Connection error")

        result = await api.connect()

        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_client):
        """测试断开连接"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"
        api.pan_id = "0x40000000"

        await api.disconnect()

        assert api.slice_id is None
        mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_slice_success(self, mock_client, mock_radio_responses):
        """测试创建 slice 成功"""
        api = FlexRadioAPI(mock_client)
        mock_client.send_command.return_value = mock_radio_responses["responses"]["slice_create"]

        slice_id = await api.create_slice("usb")

        assert slice_id == "1"
        assert api.slice_id == "1"
        calls = mock_client.send_command.call_args_list
        assert "slice create 0 usb" in calls[0][0][0]

    @pytest.mark.asyncio
    async def test_create_slice_failure(self, mock_client):
        """测试创建 slice 失败"""
        api = FlexRadioAPI(mock_client)
        mock_client.send_command.side_effect = Exception("Failed to create slice")

        slice_id = await api.create_slice("usb")

        assert slice_id is None
        assert api.slice_id is None

    @pytest.mark.asyncio
    async def test_remove_slice(self, mock_client):
        """测试删除 slice"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.remove_slice("1")

        mock_client.send_command.assert_called_once_with("slice remove 1")
        assert api.slice_id is None

    @pytest.mark.asyncio
    async def test_set_frequency(self, mock_client):
        """测试设置频率"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.set_frequency(7150000)

        mock_client.send_command.assert_called_once_with("slice set 1 frequency=7150000")
        assert api.slice_state.frequency == 7150000

    @pytest.mark.asyncio
    async def test_set_frequency_no_slice(self, mock_client):
        """测试设置频率（无 slice）"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = None

        await api.set_frequency(7150000)

        mock_client.send_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_frequency(self, mock_client):
        """测试获取频率"""
        api = FlexRadioAPI(mock_client)
        api.slice_state.frequency = 7150000

        result = await api.get_frequency()

        assert result == 7150000

    @pytest.mark.asyncio
    async def test_set_mode(self, mock_client):
        """测试设置模式"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.set_mode("lsb")

        mock_client.send_command.assert_called_once_with("slice set 1 mode=lsb")
        assert api.slice_state.mode == "lsb"

    @pytest.mark.asyncio
    async def test_get_mode(self, mock_client):
        """测试获取模式"""
        api = FlexRadioAPI(mock_client)
        api.slice_state.mode = "usb"

        result = await api.get_mode()

        assert result == "usb"

    @pytest.mark.asyncio
    async def test_set_rf_gain(self, mock_client):
        """测试设置 RF 增益"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.set_rf_gain(75)

        mock_client.send_command.assert_called_once_with("slice set 1 rfpower=75")
        assert api.slice_state.rf_gain == 75

    @pytest.mark.asyncio
    async def test_get_rf_gain(self, mock_client):
        """测试获取 RF 增益"""
        api = FlexRadioAPI(mock_client)
        api.slice_state.rf_gain = 75

        result = await api.get_rf_gain()

        assert result == 75

    @pytest.mark.asyncio
    async def test_set_af_gain(self, mock_client):
        """测试设置 AF 增益"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.set_af_gain(80)

        mock_client.send_command.assert_called_once_with("slice set 1 af_gain=80")
        assert api.slice_state.af_gain == 80

    @pytest.mark.asyncio
    async def test_get_af_gain(self, mock_client):
        """测试获取 AF 增益"""
        api = FlexRadioAPI(mock_client)
        api.slice_state.af_gain = 80

        result = await api.get_af_gain()

        assert result == 80

    @pytest.mark.asyncio
    async def test_set_ptt_on(self, mock_client):
        """测试 PTT 开启"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.set_ptt(True)

        mock_client.send_command.assert_called_once_with("xmit 1")
        assert api.slice_state.ptt is True

    @pytest.mark.asyncio
    async def test_set_ptt_off(self, mock_client):
        """测试 PTT 关闭"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.set_ptt(False)

        mock_client.send_command.assert_called_once_with("xmit off")
        assert api.slice_state.ptt is False

    @pytest.mark.asyncio
    async def test_get_ptt(self, mock_client):
        """测试获取 PTT 状态"""
        api = FlexRadioAPI(mock_client)
        api.slice_state.ptt = True

        result = await api.get_ptt()

        assert result is True

    @pytest.mark.asyncio
    async def test_enable_panadapter(self, mock_client, mock_radio_responses):
        """测试启用 panadapter"""
        api = FlexRadioAPI(mock_client)
        api.slice_state.frequency = 7150000
        mock_client.send_command.return_value = mock_radio_responses["responses"]["pan_create"]

        result = await api.enable_panadapter(width=1024)

        assert result is not None
        assert api.pan_id == "0x40000000"
        mock_client.send_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_enable_panadapter_with_center_freq(self, mock_client, mock_radio_responses):
        """测试启用 panadapter（指定中心频率）"""
        api = FlexRadioAPI(mock_client)
        mock_client.send_command.return_value = mock_radio_responses["responses"]["pan_create"]

        result = await api.enable_panadapter(width=1024, center_freq=14250000)

        assert result is not None
        call_args = mock_client.send_command.call_args[0][0]
        assert "14250000" in call_args

    @pytest.mark.asyncio
    async def test_disable_panadapter(self, mock_client):
        """测试禁用 panadapter"""
        api = FlexRadioAPI(mock_client)
        api.pan_id = "0x40000000"

        await api.disable_panadapter()

        mock_client.send_command.assert_called_once_with("display pan remove 0x40000000")
        assert api.pan_id is None

    @pytest.mark.asyncio
    async def test_enable_rx_audio(self, mock_client, mock_radio_responses):
        """测试启用接收音频"""
        api = FlexRadioAPI(mock_client)
        mock_client.send_command.return_value = mock_radio_responses["responses"]["audio_create_rx"]

        await api.enable_rx_audio(sample_rate=48000)

        mock_client.send_command.assert_called_once_with("audio client create rx 48000")

    @pytest.mark.asyncio
    async def test_enable_tx_audio(self, mock_client, mock_radio_responses):
        """测试启用发射音频"""
        api = FlexRadioAPI(mock_client)
        mock_client.send_command.return_value = mock_radio_responses["responses"]["audio_create_tx"]

        await api.enable_tx_audio(sample_rate=48000)

        mock_client.send_command.assert_called_once_with("audio client create tx 48000")

    @pytest.mark.asyncio
    async def test_disable_audio(self, mock_client):
        """测试禁用音频"""
        api = FlexRadioAPI(mock_client)

        await api.disable_audio()

        mock_client.send_command.assert_called_once_with("audio client remove all")

    @pytest.mark.asyncio
    async def test_subscribe_to_updates(self, mock_client):
        """测试订阅更新"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        await api.subscribe_to_updates()

        mock_client.send_command.assert_called_once_with("sub slice 1 all")

    def test_handle_status_frequency_update(self, mock_client):
        """测试处理状态消息（频率更新）"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        api._handle_status("S|slice|1|frequency=14250000")

        assert api.slice_state.frequency == 14250000

    def test_handle_status_mode_update(self, mock_client):
        """测试处理状态消息（模式更新）"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        api._handle_status("S|slice|1|mode=lsb")

        assert api.slice_state.mode == "lsb"

    def test_handle_status_rfpower_update(self, mock_client):
        """测试处理状态消息（RF 功率更新）"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        api._handle_status("S|slice|1|rfpower=75")

        assert api.slice_state.rf_gain == 75

    def test_handle_status_af_gain_update(self, mock_client):
        """测试处理状态消息（AF 增益更新）"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        api._handle_status("S|slice|1|af_gain=80")

        assert api.slice_state.af_gain == 80

    def test_handle_status_multiple_params(self, mock_client):
        """测试处理状态消息（多个参数）"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        api._handle_status("S|slice|1|frequency=7150000|mode=usb|rfpower=50")

        assert api.slice_state.frequency == 7150000
        assert api.slice_state.mode == "usb"
        assert api.slice_state.rf_gain == 50

    def test_handle_status_wrong_slice(self, mock_client):
        """测试处理状态消息（错误 slice ID）"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"
        original_freq = api.slice_state.frequency

        api._handle_status("S|slice|2|frequency=14250000")

        assert api.slice_state.frequency == original_freq

    def test_state_callback(self, mock_client):
        """测试状态回调机制"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        callback = Mock()
        api.add_state_callback(callback)

        api._handle_status("S|slice|1|frequency=7150000")

        callback.assert_called_once()
        state = callback.call_args[0][0]
        assert isinstance(state, SliceState)
        assert state.frequency == 7150000

    def test_multiple_callbacks(self, mock_client):
        """测试多个状态回调"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        callback1 = Mock()
        callback2 = Mock()
        api.add_state_callback(callback1)
        api.add_state_callback(callback2)

        api._handle_status("S|slice|1|frequency=7150000")

        callback1.assert_called_once()
        callback2.assert_called_once()

    def test_remove_callback(self, mock_client):
        """测试移除状态回调"""
        api = FlexRadioAPI(mock_client)
        api.slice_id = "1"

        callback = Mock()
        api.add_state_callback(callback)
        api.remove_state_callback(callback)

        api._handle_status("S|slice|1|frequency=7150000")

        callback.assert_not_called()

    def test_update_slice_state_invalid_frequency(self, mock_client):
        """测试更新状态（无效频率）"""
        api = FlexRadioAPI(mock_client)
        original_freq = api.slice_state.frequency

        api._update_slice_state(["frequency=invalid"])

        assert api.slice_state.frequency == original_freq

    def test_update_slice_state_invalid_rfpower(self, mock_client):
        """测试更新状态（无效 RF 功率）"""
        api = FlexRadioAPI(mock_client)
        original_gain = api.slice_state.rf_gain

        api._update_slice_state(["rfpower=invalid"])

        assert api.slice_state.rf_gain == original_gain
