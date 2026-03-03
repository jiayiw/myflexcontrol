RESPONSES = {
    "connect": "H44|3|4",
    "client_udpport": "R0|0|",
    "slice_create": "R0|0|1",
    "slice_remove": "R0|0|",
    "slice_set_frequency": "R0|0|",
    "slice_set_mode": "R0|0|",
    "slice_set_rfpower": "R0|0|",
    "slice_set_af_gain": "R0|0|",
    "xmit_on": "R0|0|",
    "xmit_off": "R0|0|",
    "pan_create": "R0|0|0x40000000",
    "pan_remove": "R0|0|",
    "audio_create_rx": "R0|0|0x50000000",
    "audio_create_tx": "R0|0|0x60000000",
    "audio_remove": "R0|0|",
}

STATUS_MESSAGES = [
    "S|slice|1|frequency=7150000|mode=usb|rfpower=50",
    "S|slice|1|frequency=14250000|mode=lsb",
    "S|slice|1|ptt=1",
    "S|slice|1|frequency=7150000|mode=usb|af_gain=50",
]

ERROR_RESPONSES = {
    "invalid_command": "R0|1|Invalid command",
    "slice_not_found": "R0|2|Slice not found",
    "connection_failed": "R0|3|Connection failed",
}
