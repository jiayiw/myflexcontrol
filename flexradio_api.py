import asyncio
from dataclasses import dataclass
from typing import Optional, List, Callable
import logging

from flexradio_client import FlexRadioClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SliceState:
    frequency: int = 7150000
    mode: str = "usb"
    rf_gain: int = 50
    af_gain: int = 50
    ptt: bool = False


class FlexRadioAPI:
    def __init__(self, client: FlexRadioClient):
        self.client = client
        self.slice_id: Optional[str] = None
        self.pan_id: Optional[str] = None
        self.slice_state = SliceState()
        self.state_callbacks: List[Callable] = []

        self.client.set_status_callback(self._handle_status)

    async def connect(self) -> bool:
        try:
            result = await self.client.send_command("client udpport 4991")
            logger.info(f"UDP port set: {result}")
            return True
        except Exception as e:
            logger.error(f"API connection failed: {e}")
            return False

    async def disconnect(self):
        if self.slice_id:
            await self.remove_slice(self.slice_id)
        if self.pan_id is not None:
            await self.disable_panadapter()
        await self.client.disconnect()

    async def create_slice(self, mode: str = "usb") -> Optional[str]:
        try:
            result = await self.client.send_command(f"slice create 0 {mode}")
            if result:
                parts = result.split()
                slice_id = parts[-1]
                self.slice_id = slice_id
                await self.client.send_command(f"sub slice {slice_id} all")
                logger.info(f"Slice created: {slice_id}")
                return slice_id
        except Exception as e:
            logger.error(f"Failed to create slice: {e}")
        return None

    async def remove_slice(self, slice_id: str):
        try:
            await self.client.send_command(f"slice remove {slice_id}")
            if self.slice_id == slice_id:
                self.slice_id = None
            logger.info(f"Slice removed: {slice_id}")
        except Exception as e:
            logger.error(f"Failed to remove slice: {e}")

    async def set_frequency(self, hz: int):
        if not self.slice_id:
            return
        try:
            await self.client.send_command(f"slice set {self.slice_id} frequency={hz}")
            self.slice_state.frequency = hz
        except Exception as e:
            logger.error(f"Failed to set frequency: {e}")

    async def get_frequency(self) -> int:
        return self.slice_state.frequency

    async def set_mode(self, mode: str):
        if not self.slice_id:
            return
        try:
            await self.client.send_command(f"slice set {self.slice_id} mode={mode}")
            self.slice_state.mode = mode
        except Exception as e:
            logger.error(f"Failed to set mode: {e}")

    async def get_mode(self) -> str:
        return self.slice_state.mode

    async def set_rf_gain(self, level: int):
        if not self.slice_id:
            return
        try:
            await self.client.send_command(f"slice set {self.slice_id} rfpower={level}")
            self.slice_state.rf_gain = level
        except Exception as e:
            logger.error(f"Failed to set RF gain: {e}")

    async def get_rf_gain(self) -> int:
        return self.slice_state.rf_gain

    async def set_af_gain(self, level: int):
        if not self.slice_id:
            return
        try:
            await self.client.send_command(f"slice set {self.slice_id} af_gain={level}")
            self.slice_state.af_gain = level
        except Exception as e:
            logger.error(f"Failed to set AF gain: {e}")

    async def get_af_gain(self) -> int:
        return self.slice_state.af_gain

    async def set_ptt(self, on: bool):
        if not self.slice_id:
            return
        try:
            if on:
                await self.client.send_command(f"xmit {self.slice_id}")
            else:
                await self.client.send_command("xmit off")
            self.slice_state.ptt = on
        except Exception as e:
            logger.error(f"Failed to set PTT: {e}")

    async def get_ptt(self) -> bool:
        return self.slice_state.ptt

    async def enable_panadapter(
        self, width: int = 1024, center_freq: Optional[int] = None
    ):
        try:
            if center_freq is None:
                center_freq = self.slice_state.frequency
            result = await self.client.send_command(
                f"display pan create {width} {center_freq}"
            )
            if result:
                parts = result.split()
                self.pan_id = parts[-1]
                logger.info(f"Panadapter enabled: {self.pan_id}")
                return result
        except Exception as e:
            logger.error(f"Failed to enable panadapter: {e}")
        return None

    async def disable_panadapter(self):
        if self.pan_id is not None:
            try:
                await self.client.send_command(f"display pan remove {self.pan_id}")
                self.pan_id = None
                logger.info("Panadapter disabled")
            except Exception as e:
                logger.error(f"Failed to disable panadapter: {e}")

    async def enable_rx_audio(self, sample_rate: int = 48000):
        try:
            result = await self.client.send_command(
                f"audio client create rx {sample_rate}"
            )
            logger.info(f"RX audio enabled: {result}")
        except Exception as e:
            logger.error(f"Failed to enable RX audio: {e}")

    async def enable_tx_audio(self, sample_rate: int = 48000):
        try:
            result = await self.client.send_command(
                f"audio client create tx {sample_rate}"
            )
            logger.info(f"TX audio enabled: {result}")
        except Exception as e:
            logger.error(f"Failed to enable TX audio: {e}")

    async def disable_audio(self):
        try:
            await self.client.send_command("audio client remove all")
            logger.info("Audio streams disabled")
        except Exception as e:
            logger.error(f"Failed to disable audio: {e}")

    async def subscribe_to_updates(self):
        if self.slice_id:
            await self.client.send_command(f"sub slice {self.slice_id} all")

    def _handle_status(self, line: str):
        parts = line[1:].split("|")
        if len(parts) < 2:
            return

        msg_type = parts[0]

        if msg_type == "slice" and len(parts) > 2:
            slice_id = parts[1]
            if slice_id == self.slice_id:
                params = parts[2:]
                self._update_slice_state(params)
                self._notify_state_change()

    def _update_slice_state(self, params: List[str]):
        for param in params:
            if "frequency=" in param:
                try:
                    self.slice_state.frequency = int(param.split("=")[1])
                except:
                    pass
            elif "mode=" in param:
                self.slice_state.mode = param.split("=")[1]
            elif "rfpower=" in param:
                try:
                    self.slice_state.rf_gain = int(param.split("=")[1])
                except:
                    pass
            elif "af_gain=" in param:
                try:
                    self.slice_state.af_gain = int(param.split("=")[1])
                except:
                    pass

    def _notify_state_change(self):
        for callback in self.state_callbacks:
            callback(self.slice_state)

    def add_state_callback(self, callback: Callable):
        self.state_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable):
        if callback in self.state_callbacks:
            self.state_callbacks.remove(callback)
