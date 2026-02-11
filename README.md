# FlexRadio 6400 Control for Linux (ARM64)

Remote control application for FlexRadio FLEX-6400 SDR with full SSB support.

## Features

- Remote control via LAN (configurable IP)
- Panadapter display with click-to-tune
- Waterfall display (100-line history)
- USB/LSB mode support
- RX and TX audio playback
- PTT control (Space key shortcut)
- RF and AF gain control
- 10 memory channels
- Side-by-side display layout
- Pipewire audio backend
- Microphone selection

## Supported Platforms

- Ubuntu Server 24.04 ARM64 (Nvidia)
- Ubuntu/Debian x86_64
- Other Linux distributions with ARM64 support

## Installation

### Ubuntu Server 24.04 ARM64:

```bash
# Install system dependencies
sudo apt update
sudo apt install python3-pip python3-dev portaudio19-dev pipewire libpipewire-0.3-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Run
python run.py
```

### Ubuntu/Debian x86_64:

```bash
sudo apt update
sudo apt install python3-pip python3-yaml portaudio19-dev pipewire
pip install -r requirements.txt
python run.py
```

### Fedora ARM64:

```bash
sudo dnf install python3-pip python3-devel portaudio-devel pipewire-devel
pip install -r requirements.txt
python run.py
```

### Arch Linux:

```bash
sudo pacman -S python-pip python-yaml portaudio pipewire
pip install -r requirements.txt
python run.py
```

## Configuration

Edit `~/.config/flexradio-6400/config.yaml` or use Settings dialog:

```yaml
radio:
  ip_address: "192.168.1.100"
```

## Controls

- **Frequency**: Enter frequency in MHz (e.g., 7.150)
- **Mode**: Click USB or LSB button
- **RF Gain**: Slider 0-100
- **AF Gain**: Slider 0-100
- **PTT**: Click TX button or press Space
- **Panadapter**: Click to tune to frequency
- **Memory**: Click M1-M10 to recall

## Requirements

- Python 3.9+
- Linux (ARM64 or x86_64)
- Pipewire audio framework
- PortAudio development libraries
- FlexRadio 6400 on same LAN

## Troubleshooting

### Audio not working

1. Verify Pipewire is running: `pactl info`
2. Check PyAudio backend: Look at "Audio Backend" in Settings dialog
3. Ensure microphone is selected in Settings

### Cannot connect to radio

1. Verify radio IP address in Settings
2. Check radio is powered on and connected to LAN
3. Verify network connectivity: `ping <radio-ip>`

### PyAudio installation fails

On ARM64, may need to compile from source:

```bash
sudo apt install portaudio19-dev python3-dev
pip install --no-binary PyAudio PyAudio
```

## License

MIT License
