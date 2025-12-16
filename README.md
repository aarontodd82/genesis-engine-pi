# GenesisEngine-Pi

Python driver for GenesisEngine sound boards (YM2612 + SN76489) on Raspberry Pi.

## Features

- **VGM Playback**: Play VGM/VGZ files with accurate timing
- **Direct Synthesis**: Control YM2612 FM and SN76489 PSG chips directly
- **Emulator Bridge**: Real-time audio from BlastEm emulator
- **Hardware Control**: Uses the GenesisEngine PCB with SPI and GPIO

## Installation

### Prerequisites

Enable SPI on your Raspberry Pi:
```bash
sudo raspi-config
# Interface Options → SPI → Enable
```

### Install from source

```bash
git clone https://github.com/aarontodd82/genesis-engine-pi.git
cd genesis-engine-pi
pip install -e .
```

### Optional: pigpio for better timing

For more accurate timing, install pigpio:
```bash
sudo apt install pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
pip install pigpio
```

## Hardware Wiring

Connect the GenesisEngine board to the Raspberry Pi GPIO:

| Function | Pi GPIO (BCM) | Physical Pin |
|----------|---------------|--------------|
| WR_P (PSG) | 17 | 11 |
| WR_Y (YM2612) | 27 | 13 |
| IC_Y (Reset) | 22 | 15 |
| A0_Y | 23 | 16 |
| A1_Y | 24 | 18 |
| SPI MOSI | 10 | 19 |
| SPI SCLK | 11 | 23 |
| GND | GND | 6, 9, etc. |

See `../GenesisEngine/hardware/` for board schematics.

## Quick Start

### Jukebox (VGM Player)

```bash
# Put VGM files in a directory
mkdir music
cp *.vgm music/

# Run the jukebox
python examples/jukebox.py music/
```

### Simple Synth

```bash
python examples/simple_synth.py
```

Commands:
- `n60` - Play middle C on FM
- `s` - Stop FM note
- `p3` - Change to patch 3 (Lead)
- `t60` - Play middle C on PSG
- `q` - Silence all

### Emulator Bridge

```bash
python examples/emulator_bridge.py
# Then connect BlastEm to /tmp/genesis_bridge.sock
```

## API Usage

```python
import time
from genesis_engine import GenesisEngine, GenesisBoard

# Initialize
board = GenesisBoard()
player = GenesisEngine(board)

board.begin()

# Play a VGM file
player.play("/path/to/music.vgm")
player.looping = True

# Update loop
while player.is_playing:
    player.update()
    time.sleep(0.001)

# Cleanup
player.stop()
board.cleanup()
```

### Direct Chip Control

```python
import time
from genesis_engine import GenesisBoard
from genesis_engine.synth import (
    DEFAULT_FM_PATCHES,
    write_to_channel,
    key_on,
    key_off,
    play_note,
)

board = GenesisBoard()
board.begin()

# Load an FM patch and play a note
patch = DEFAULT_FM_PATCHES[0]  # Bright EP
patch.load_to_channel(board, 0)

write_to_channel(board, 0, 60)  # Set frequency (middle C)
key_on(board, 0)                # Start note

time.sleep(0.5)

key_off(board, 0)               # Release note

# Play a PSG note
play_note(board, 0, 60, 2)      # Channel 0, middle C, volume 2

board.silence_psg()
board.cleanup()
```

## Architecture

```
genesis_engine/
├── __init__.py          # Main exports
├── engine.py            # GenesisEngine - VGM player
├── board.py             # GenesisBoard - hardware driver
├── vgm_parser.py        # VGM format parsing
├── vgm_commands.py      # VGM constants
├── pcm_bank.py          # DAC sample storage
├── sources/
│   ├── base.py          # Abstract VGM source
│   ├── file_source.py   # File-based VGM
│   └── vgz_source.py    # Compressed VGZ
└── synth/
    ├── fm_patch.py      # FM voice definitions
    ├── fm_frequency.py  # MIDI to FM conversion
    ├── psg_frequency.py # MIDI to PSG conversion
    └── default_patches.py
```

## Implementation Notes

- Uses `spidev` for SPI communication with the shift register
- Uses `RPi.GPIO` for control pin management
- Uses `time.perf_counter_ns()` for microsecond-accurate VGM timing
- VGZ decompression via Python's `gzip` module
- Full VGM files loaded into RAM (Pi has plenty of memory)

## License

LGPL-2.1-or-later

Copyright (C) 2025 Aaron Todd
