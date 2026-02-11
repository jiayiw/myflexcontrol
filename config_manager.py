import yaml
from pathlib import Path
from typing import Any


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "flexradio-6400"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.yaml"
        self.config = self.load_default_config()

        if self.config_file.exists():
            self.load_config()

    def load_default_config(self) -> dict:
        return {
            "radio": {
                "ip_address": "192.168.1.100",
                "tcp_port": 4992,
                "udp_port": 4991,
            },
            "display": {
                "panadapter_enabled": True,
                "waterfall_enabled": True,
                "waterfall_lines": 100,
                "panadapter_fps": 15,
                "panadapter_width": 1024,
                "side_by_side": True,
            },
            "audio": {
                "sample_rate": 48000,
                "channels": 1,
                "chunk_size": 1024,
                "rx_gain": 1.0,
                "tx_gain": 1.0,
                "input_device": None,
                "backend": "pipewire",
            },
            "memory": {
                "max_channels": 10,
                "channels": [
                    {
                        "name": "40m SSB",
                        "frequency": 7150000,
                        "mode": "usb",
                        "rf_gain": 50,
                    },
                    {
                        "name": "20m Calling",
                        "frequency": 14250000,
                        "mode": "lsb",
                        "rf_gain": 50,
                    },
                ],
            },
        }

    def load_config(self) -> dict:
        try:
            with open(self.config_file, "r") as f:
                loaded = yaml.safe_load(f)
                self._deep_merge(loaded, self.config)
        except Exception as e:
            print(f"Error loading config: {e}")
        return self.config

    def save_config(self, config=None):
        if config is None:
            config = self.config
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get_radio_ip(self) -> str:
        return self.config["radio"]["ip_address"]

    def set_radio_ip(self, ip: str):
        self.config["radio"]["ip_address"] = ip
        self.save_config()

    def get(self, key_path: str, default=None) -> Any:
        keys = key_path.split(".")
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any):
        keys = key_path.split(".")
        obj = self.config
        for key in keys[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        obj[keys[-1]] = value
        self.save_config()

    def _deep_merge(self, source: dict, destination: dict):
        for key, value in source.items():
            if (
                key in destination
                and isinstance(destination[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(value, destination[key])
            else:
                destination[key] = value
