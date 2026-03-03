import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from flexradio_client import FlexRadioClient


class TestFlexRadioClient:
    """测试 FlexRadio TCP 客户端"""

    def test_init(self):
        """测试初始化"""
        client = FlexRadioClient("192.168.1.100", port=4992, timeout=5.0)

        assert client.host == "192.168.1.100"
        assert client.port == 4992
        assert client.timeout == 5.0
        assert client.reader is None
        assert client.writer is None
        assert client.sequence == 0
        assert client.running is False

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """测试成功连接"""
        client = FlexRadioClient("192.168.1.100")

        mock_reader = Mock()
        mock_writer = Mock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
            mock_open.return_value = (mock_reader, mock_writer)

            result = await client.connect()

            assert result is True
            assert client.running is True
            assert client.reader == mock_reader
            assert client.writer == mock_writer
            mock_open.assert_called_once_with("192.168.1.100", 4992)

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """测试连接失败"""
        client = FlexRadioClient("invalid_ip")

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = Exception("Connection refused")

            result = await client.connect()

            assert result is False
            assert client.running is False
            mock_open.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """测试断开连接"""
        client = FlexRadioClient("192.168.1.100")

        mock_writer = Mock()
        mock_writer.close = Mock()
        mock_writer.wait_closed = AsyncMock()

        client.writer = mock_writer
        client.running = True

        await client.disconnect()

        assert client.running is False
        assert client.reader is None
        assert client.writer is None
        mock_writer.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_success(self):
        """测试发送命令成功"""
        client = FlexRadioClient("192.168.1.100")

        mock_writer = Mock()
        mock_writer.write = Mock()
        mock_writer.drain = AsyncMock()

        client.writer = mock_writer
        client.running = True

        with patch.object(client, "_receive_responses"):
            future = asyncio.Future()
            future.set_result("OK")
            client.pending_commands[1] = future

            with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                mock_wait.return_value = "OK"

                with patch("asyncio.Future") as mock_future_class:
                    mock_future = asyncio.Future()
                    mock_future_class.return_value = mock_future

                    result = await client.send_command("test command")

                    assert result == "OK"
                    mock_writer.write.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_timeout(self):
        """测试命令超时"""
        client = FlexRadioClient("192.168.1.100", timeout=0.1)

        mock_writer = Mock()
        mock_writer.write = Mock()
        mock_writer.drain = AsyncMock()

        client.writer = mock_writer
        client.running = True

        with patch.object(client, "_receive_responses"):
            with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait:
                mock_wait.side_effect = asyncio.TimeoutError()

                with patch("asyncio.Future") as mock_future_class:
                    mock_future = asyncio.Future()
                    mock_future_class.return_value = mock_future

                    with pytest.raises(TimeoutError):
                        await client.send_command("test command")

    def test_parse_response_success(self):
        """测试解析成功响应"""
        client = FlexRadioClient("192.168.1.100")

        seq, errno, message = client._parse_response("R123|0|OK")
        assert seq == 123
        assert errno == "0"
        assert message == "OK"

    def test_parse_response_with_error(self):
        """测试解析错误响应"""
        client = FlexRadioClient("192.168.1.100")

        seq, errno, message = client._parse_response("R456|1|Error message")
        assert seq == 456
        assert errno == "1"
        assert message == "Error message"

    def test_parse_response_empty(self):
        """测试解析空响应"""
        client = FlexRadioClient("192.168.1.100")

        seq, errno, message = client._parse_response("R789")
        assert seq == 789
        assert errno == "0"
        assert message == ""

    def test_handle_heartbeat(self):
        """测试心跳处理"""
        client = FlexRadioClient("192.168.1.100")

        client._handle_heartbeat("H44|3|4")

    def test_handle_status_with_callback(self):
        """测试状态消息处理（有回调）"""
        client = FlexRadioClient("192.168.1.100")

        callback_mock = Mock()
        client.set_status_callback(callback_mock)

        client._handle_status("S|slice|1|frequency=7150000")

        callback_mock.assert_called_once_with("S|slice|1|frequency=7150000")

    def test_handle_status_without_callback(self):
        """测试状态消息处理（无回调）"""
        client = FlexRadioClient("192.168.1.100")

        client._handle_status("S|slice|1|frequency=7150000")

    def test_set_status_callback(self):
        """测试设置状态回调"""
        client = FlexRadioClient("192.168.1.100")

        callback = Mock()
        client.set_status_callback(callback)

        assert client.status_callback == callback
