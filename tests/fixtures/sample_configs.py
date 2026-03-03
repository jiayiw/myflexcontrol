SAMPLE_CONFIG = {
    "radio": {"ip_address": "192.168.1.100", "tcp_port": 4992, "udp_port": 4991},
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
                "af_gain": 50,
            },
            {
                "name": "20m Calling",
                "frequency": 14250000,
                "mode": "lsb",
                "rf_gain": 50,
                "af_gain": 50,
            },
        ],
    },
}

MEMORY_CHANNEL_DATA = [
    {
        "name": "40m SSB",
        "frequency": 7150000,
        "mode": "usb",
        "rf_gain": 50,
        "af_gain": 50,
    },
    {
        "name": "20m LSB",
        "frequency": 14250000,
        "mode": "lsb",
        "rf_gain": 60,
        "af_gain": 55,
    },
    {
        "name": "15m USB",
        "frequency": 21250000,
        "mode": "usb",
        "rf_gain": 55,
        "af_gain": 50,
    },
]
