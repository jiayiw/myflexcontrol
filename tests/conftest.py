import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def qapp():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / ".config" / "flexradio-6400"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def mock_client():
    from flexradio_client import FlexRadioClient

    client = Mock(spec=FlexRadioClient)
    client.connect = AsyncMock(return_value=True)
    client.disconnect = AsyncMock()
    client.send_command = AsyncMock(return_value="R0|0|")
    client.reader = Mock()
    client.writer = Mock()
    client.host = "192.168.1.100"
    client.port = 4992
    client.running = False
    return client


@pytest.fixture
def mock_pyaudio():
    with patch("pyaudio.PyAudio") as mock:
        instance = mock.return_value
        instance.get_device_count.return_value = 2
        instance.get_device_info_by_index.side_effect = [
            {"name": "Default Mic", "maxInputChannels": 1, "hostApi": 0, "index": 0},
            {"name": "USB Mic", "maxInputChannels": 1, "hostApi": 0, "index": 1},
        ]
        instance.get_default_output_device_info.return_value = {"hostApi": 0}
        instance.open.return_value = Mock()
        yield instance


@pytest.fixture
def sample_config():
    from tests.fixtures.sample_configs import SAMPLE_CONFIG

    return SAMPLE_CONFIG


@pytest.fixture
def mock_radio_responses():
    from tests.fixtures.mock_radio_responses import (
        ERROR_RESPONSES,
        RESPONSES,
        STATUS_MESSAGES,
    )

    return {
        "responses": RESPONSES,
        "status_messages": STATUS_MESSAGES,
        "error_responses": ERROR_RESPONSES,
    }
