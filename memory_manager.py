from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class MemoryChannel:
    name: str
    frequency: int
    mode: str
    rf_gain: int = 50
    af_gain: int = 50


class MemoryManager:
    def __init__(self, max_channels: int = 10):
        self.max_channels = max_channels
        self.channels: List[MemoryChannel] = []

    def load_from_config(self, config: Dict[str, Any]):
        self.channels = []
        mem_config = config.get("memory", {})
        channels_list = mem_config.get("channels", [])

        for ch in channels_list:
            try:
                channel = MemoryChannel(
                    name=ch["name"],
                    frequency=ch["frequency"],
                    mode=ch["mode"],
                    rf_gain=ch.get("rf_gain", 50),
                    af_gain=ch.get("af_gain", 50),
                )
                self.channels.append(channel)
            except Exception as e:
                print(f"Error loading memory channel: {e}")

    def save_to_config(self) -> Dict[str, Any]:
        channels_list = []
        for ch in self.channels:
            channels_list.append(
                {
                    "name": ch.name,
                    "frequency": ch.frequency,
                    "mode": ch.mode,
                    "rf_gain": ch.rf_gain,
                    "af_gain": ch.af_gain,
                }
            )
        return {
            "memory": {"max_channels": self.max_channels, "channels": channels_list}
        }

    def add_channel(self, channel: MemoryChannel) -> bool:
        if len(self.channels) >= self.max_channels:
            return False
        self.channels.append(channel)
        return True

    def update_channel(self, index: int, channel: MemoryChannel) -> bool:
        if 0 <= index < len(self.channels):
            self.channels[index] = channel
            return True
        return False

    def delete_channel(self, index: int) -> bool:
        if 0 <= index < len(self.channels):
            del self.channels[index]
            return True
        return False

    def get_channel(self, index: int) -> Optional[MemoryChannel]:
        if 0 <= index < len(self.channels):
            return self.channels[index]
        return None

    def all_channels(self) -> List[MemoryChannel]:
        return self.channels
