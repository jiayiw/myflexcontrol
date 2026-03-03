import logging
from typing import Any, Callable, Dict, List, Optional

import pyaudio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioManager:
    def __init__(self, config: Dict[str, Any]):
        self.sample_rate = config["audio"]["sample_rate"]
        self.channels = config["audio"]["channels"]
        self.chunk_size = config["audio"]["chunk_size"]
        self.pyaudio = pyaudio.PyAudio()
        self.rx_stream = None
        self.tx_stream = None
        self.selected_input_device: Optional[int] = None
        self.rx_callback: Optional[Callable[[], bytes]] = None
        self.tx_callback: Optional[Callable[[bytes], None]] = None

    def get_input_devices(self) -> List[Dict[str, Any]]:
        devices = []
        for i in range(self.pyaudio.get_device_count()):
            info = self.pyaudio.get_device_info_by_index(i)
            if int(info.get("maxInputChannels", 0)) > 0:
                devices.append({"index": i, "name": info["name"], "host_api": info["hostApi"]})
        return devices

    def set_input_device(self, device_index: Optional[int]):
        self.selected_input_device = device_index
        logger.info(f"Input device set to: {device_index}")

    def set_rx_callback(self, callback: Optional[Callable[[], bytes]]):
        """
        Set RX audio data source callback.
        The callback should return audio bytes to be played.
        """
        self.rx_callback = callback

    def set_tx_callback(self, callback: Optional[Callable[[bytes], None]]):
        """
        Set TX audio data handler callback.
        The callback receives captured microphone audio data.
        """
        self.tx_callback = callback

    def start_rx(self):
        if self.rx_stream is not None:
            return

        try:
            self.rx_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._rx_stream_callback,
            )
            logger.info("RX audio started")
        except Exception as e:
            logger.error(f"Failed to start RX audio: {e}")

    def _rx_stream_callback(self, in_data, frame: int, time_info, status: int):
        """
        RX audio stream callback.
        Called by PyAudio when the output stream (speaker) needs audio data to play.
        Returns audio bytes to be played.
        """
        try:
            if self.rx_callback:
                return (self.rx_callback(), pyaudio.paContinue)
        except Exception as e:
            logger.error(f"RX stream callback error: {e}")
        return (b"\x00" * frame * 2, pyaudio.paContinue)

    def stop_rx(self):
        if self.rx_stream:
            self.rx_stream.stop_stream()
            self.rx_stream.close()
            self.rx_stream = None
            logger.info("RX audio stopped")

    def start_tx(self):
        if self.tx_stream is not None:
            return

        device_index = (
            self.selected_input_device if self.selected_input_device is not None else None
        )

        try:
            self.tx_stream = self.pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._tx_stream_callback,
            )
            logger.info("TX audio started")
        except Exception as e:
            logger.error(f"Failed to start TX audio: {e}")

    def _tx_stream_callback(self, in_data, frame: int, time_info, status: int):
        """
        TX audio stream callback.
        Called by PyAudio when the input stream (microphone) captures audio data.
        Processes captured audio data for transmission.
        """
        try:
            if self.tx_callback:
                self.tx_callback(in_data)
        except Exception as e:
            logger.error(f"TX stream callback error: {e}")
        return (None, pyaudio.paContinue)

    def read_tx_data(self) -> bytes:
        if self.tx_stream:
            return self.tx_stream.read(self.chunk_size, exception_on_overflow=False)
        return b""

    def stop_tx(self):
        if self.tx_stream:
            self.tx_stream.stop_stream()
            self.tx_stream.close()
            self.tx_stream = None
            logger.info("TX audio stopped")

    def cleanup(self):
        self.stop_rx()
        self.stop_tx()
        self.pyaudio.terminate()

    def get_audio_backend(self) -> str:
        try:
            default_output = self.pyaudio.get_default_output_device_info()
            host_api = default_output.get("hostApi", "Unknown")
            return str(host_api)
        except:
            return "Unknown"
