# GenesisEngine Raspberry Pi Port - Direct Mapping Guide

## Overview

This document maps the Arduino GenesisEngine library to its Python equivalent for Raspberry Pi.
Each section references specific files and line numbers from `../GenesisEngine/`.

**Examples to port:**
1. Jukebox (from `SDCardPlayer`) - VGM file playback
2. SimpleSynth - Direct chip control via keyboard/commands
3. EmulatorBridge - Real-time audio from BlastEm (local IPC instead of serial)

---

## Directory Structure Mapping

```
Arduino: ../GenesisEngine/              Python: ./genesis_engine/
├── src/                                ├── __init__.py
│   ├── GenesisEngine.h/cpp        →    ├── engine.py
│   ├── GenesisBoard.h/cpp         →    ├── board.py
│   ├── VGMParser.h/cpp            →    ├── vgm_parser.py
│   ├── VGMCommands.h              →    ├── vgm_commands.py
│   ├── PCMDataBank.h/cpp          →    ├── pcm_bank.py
│   ├── sources/                        ├── sources/
│   │   ├── VGMSource.h            →    │   ├── base.py
│   │   ├── SDSource.h/cpp         →    │   ├── file_source.py
│   │   ├── ProgmemSource.h        →    │   └── (merged into file_source.py)
│   │   └── VGZSource.h/cpp        →    │   └── vgz_source.py
│   └── synth/                          └── synth/
│       ├── FMPatch.h/cpp          →        ├── fm_patch.py
│       ├── FMFrequency.h/cpp      →        ├── fm_frequency.py
│       ├── FMOperator.h           →        ├── fm_operator.py
│       ├── PSGFrequency.h/cpp     →        ├── psg_frequency.py
│       ├── PSGEnvelope.h          →        ├── psg_envelope.py
│       └── DefaultPatches.h/cpp   →        └── default_patches.py
└── examples/                       └── examples/
    ├── SDCardPlayer/              →    ├── jukebox.py
    ├── SimpleSynth/               →    ├── simple_synth.py
    └── EmulatorBridge/            →    └── emulator_bridge.py
```

---

## Core Module Mappings

### 1. `vgm_commands.py` ← `src/VGMCommands.h`

**Source**: `../GenesisEngine/src/VGMCommands.h` (122 lines)

| Arduino Constant (line) | Python Constant |
|-------------------------|-----------------|
| `VGM_MAGIC` (L15) | `VGM_MAGIC = 0x206D6756` |
| `VGM_SAMPLE_RATE` (L18) | `VGM_SAMPLE_RATE = 44100` |
| `VGM_HEADER_*` (L21-40) | `VGM_HEADER_EOF_OFFSET = 0x04`, etc. |
| `VGM_CMD_*` (L43-80) | `VGM_CMD_PSG_WRITE = 0x50`, etc. |
| `VGM_WAIT_*` (L93-95) | `VGM_WAIT_NTSC = 735`, etc. |
| `YM2612_CLOCK_NTSC` (L83) | `YM2612_CLOCK_NTSC = 7670453` |
| `SN76489_CLOCK_NTSC` (L86) | `SN76489_CLOCK_NTSC = 3579545` |

---

### 2. `board.py` ← `src/GenesisBoard.h/cpp`

**Source**: `../GenesisEngine/src/GenesisBoard.h` (171 lines), `src/GenesisBoard.cpp` (524 lines)

#### Class Mapping

| Arduino | Python |
|---------|--------|
| `GenesisBoard(pinWR_P, pinWR_Y, pinIC_Y, pinA0_Y, pinA1_Y, pinSCK, pinSDI)` | `GenesisBoard(wr_p=17, wr_y=27, ic_y=22, a0_y=23, a1_y=24)` |

#### Method Mapping

| Arduino Method | Source Location | Python Method |
|----------------|-----------------|---------------|
| `begin()` | `GenesisBoard.cpp:45-89` | `begin()` |
| `reset()` | `GenesisBoard.cpp:91-115` | `reset()` |
| `writeYM2612(port, reg, val)` | `GenesisBoard.cpp:117-175` | `write_ym2612(port, reg, val)` |
| `writeDAC(sample)` | `GenesisBoard.cpp:177-195` | `write_dac(sample)` |
| `beginDACStream()` | `GenesisBoard.cpp:197-215` | `begin_dac_stream()` |
| `endDACStream()` | `GenesisBoard.cpp:217-225` | `end_dac_stream()` |
| `writePSG(val)` | `GenesisBoard.cpp:227-265` | `write_psg(val)` |
| `silencePSG()` | `GenesisBoard.cpp:267-280` | `silence_psg()` |
| `muteAll()` | `GenesisBoard.cpp:282-310` | `mute_all()` |

#### Critical Implementation Details

**YM2612 Write Sequence** (`GenesisBoard.cpp:117-175`):
```
1. GPIO.output(a1_y, port)          # Port select (L125)
2. GPIO.output(a0_y, LOW)           # Address mode (L128)
3. spi.xfer2([reg])                 # Shift out register (L131)
4. GPIO.output(wr_y, LOW)           # Write strobe (L134)
5. GPIO.output(wr_y, HIGH)          # (L137)
6. time.sleep(0.000005)             # 5µs wait (L140)
7. GPIO.output(a0_y, HIGH)          # Data mode (L143)
8. spi.xfer2([val])                 # Shift out value (L146)
9. GPIO.output(wr_y, LOW)           # Write strobe (L149)
10. GPIO.output(wr_y, HIGH)         # (L152)
```

**PSG Bit Reversal** (`GenesisBoard.cpp:240-245`):
```python
def _reverse_bits(self, b: int) -> int:
    b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
    b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
    b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
    return b
```

---

### 3. `pcm_bank.py` ← `src/PCMDataBank.h/cpp`

**Source**: `../GenesisEngine/src/PCMDataBank.h` (100 lines), `src/PCMDataBank.cpp` (328 lines)

**Simplification**: Pi has gigabytes of RAM - no downsampling or PSRAM detection needed.

| Arduino Method | Source Location | Python Method |
|----------------|-----------------|---------------|
| `loadDataBlock()` | `PCMDataBank.cpp:45-145` | `load_data_block(data: bytes)` |
| `readByte()` | `PCMDataBank.cpp:147-175` | `read_byte() -> int` |
| `seek()` | `PCMDataBank.cpp:177-190` | `seek(position: int)` |
| `clear()` | `PCMDataBank.cpp:192-205` | `clear()` |
| `hasData()` | `PCMDataBank.h:65` | `has_data` property |

**Key behavior** (`PCMDataBank.cpp:165`): Return `0x80` (silence) when no data or past end.

---

### 4. `sources/base.py` ← `src/sources/VGMSource.h`

**Source**: `../GenesisEngine/src/sources/VGMSource.h` (99 lines)

| Arduino Virtual Method | Source Location | Python Abstract Method |
|------------------------|-----------------|------------------------|
| `open()` | L35 | `open() -> bool` |
| `close()` | L36 | `close()` |
| `read()` | L38 | `read(count: int = 1) -> bytes` |
| `peek()` | L40 | `peek() -> int` |
| `available()` | L41 | `available() -> bool` |
| `seek()` | L44 | `seek(position: int) -> bool` |
| `position()` | L45 | `position: int` property |
| `size()` | L46 | `size: int` property |
| `canSeek()` | L47 | `can_seek: bool` property |
| `readUInt16()` | L50-54 | `read_uint16() -> int` |
| `readUInt32()` | L56-62 | `read_uint32() -> int` |
| `skip()` | L64-68 | `skip(count: int)` |

---

### 5. `sources/file_source.py` ← `src/sources/SDSource.h/cpp`

**Source**: `../GenesisEngine/src/sources/SDSource.h` (76 lines), `SDSource.cpp`

| Arduino Method | Source Location | Python Method |
|----------------|-----------------|---------------|
| `openFile()` | `SDSource.cpp:25-55` | `__init__(path: str)` + `open()` |
| `read()` | `SDSource.h:45-50` | `read(count: int = 1) -> bytes` |
| `seek()` | `SDSource.h:55-60` | `seek(position: int) -> bool` |
| `setDataStart()` | `SDSource.h:65` | `set_data_start(offset: int)` |
| `isVGZ()` | `SDSource.cpp:35-40` | Check for `0x1F 0x8B` magic |

---

### 6. `sources/vgz_source.py` ← `src/sources/VGZSource.h/cpp`

**Source**: `../GenesisEngine/src/sources/VGZSource.h` (108 lines), `VGZSource.cpp`

**Simplification**: Python's `gzip` module handles decompression automatically.

```python
import gzip

class VGZSource(VGMSource):
    def open(self) -> bool:
        self._file = gzip.open(self.path, 'rb')
        return True
```

---

### 7. `vgm_parser.py` ← `src/VGMParser.h/cpp`

**Source**: `../GenesisEngine/src/VGMParser.h` (131 lines), `VGMParser.cpp` (445 lines)

#### Method Mapping

| Arduino Method | Source Location | Python Method |
|----------------|-----------------|---------------|
| `VGMParser(board)` | L35 | `__init__(board: GenesisBoard)` |
| `setSource()` | `VGMParser.cpp:35-40` | `set_source(source: VGMSource)` |
| `parseHeader()` | `VGMParser.cpp:42-120` | `parse_header() -> bool` |
| `processUntilWait()` | `VGMParser.cpp:122-280` | `process_until_wait() -> int` |
| `isFinished()` | L55 | `is_finished: bool` property |
| `hasLoop()` | L60 | `has_loop: bool` property |
| `seekToLoop()` | `VGMParser.cpp:282-310` | `seek_to_loop() -> bool` |
| `getLoopCount()` | L65 | `loop_count: int` property |
| `getTotalSamples()` | L70 | `total_samples: int` property |

#### Header Parsing (`VGMParser.cpp:42-120`)

Read these fields at these offsets (all little-endian):
- `0x00`: Magic (verify == `0x206D6756`)
- `0x04`: EOF offset (relative)
- `0x08`: Version (BCD format)
- `0x0C`: SN76489 clock (non-zero = has PSG)
- `0x18`: Total samples
- `0x1C`: Loop offset (relative to 0x1C)
- `0x20`: Loop samples
- `0x2C`: YM2612 clock (v1.10+, non-zero = has FM)
- `0x34`: Data offset (v1.50+, relative to 0x34, default 0x40)

#### Command Dispatch (`VGMParser.cpp:122-280`)

| Command | Arduino Handler | Python Behavior |
|---------|-----------------|-----------------|
| `0x50` | L145-155 | `board.write_psg(val)` with attenuation |
| `0x52` | L157-165 | `board.write_ym2612(0, reg, val)` |
| `0x53` | L167-175 | `board.write_ym2612(1, reg, val)` |
| `0x61` | L177-182 | Return 16-bit LE wait samples |
| `0x62` | L184-186 | Return 735 (NTSC frame) |
| `0x63` | L188-190 | Return 882 (PAL frame) |
| `0x66` | L192-196 | Set finished, return 0 |
| `0x67` | L198-230 | Load PCM data block |
| `0x70-0x7F` | L232-236 | Return `(cmd & 0x0F) + 1` |
| `0x80-0x8F` | L238-250 | Write DAC, return `(cmd & 0x0F)` |
| `0xE0` | L252-260 | Seek PCM bank (4-byte LE offset) |

#### PSG Attenuation (`VGMParser.cpp:148-154`)

When both FM and PSG present:
```python
if self.has_fm and (val & 0x90) == 0x90:  # Attenuation command
    atten = val & 0x0F
    if atten <= 13:
        atten += 2  # Reduce by 2 levels
    val = (val & 0xF0) | atten
```

---

### 8. `engine.py` ← `src/GenesisEngine.h/cpp`

**Source**: `../GenesisEngine/src/GenesisEngine.h` (181 lines), `GenesisEngine.cpp` (299 lines)

#### State Enum (`GenesisEngine.h:25-30`)

```python
class EngineState(Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    FINISHED = 3
```

#### Method Mapping

| Arduino Method | Source Location | Python Method |
|----------------|-----------------|---------------|
| `GenesisEngine(board)` | L35 | `__init__(board: GenesisBoard)` |
| `play(data, length)` | `GenesisEngine.cpp:45-80` | `play_data(data: bytes)` |
| `playFile(path)` | `GenesisEngine.cpp:117-150` | `play(path: str)` |
| `stop()` | `GenesisEngine.cpp:152-165` | `stop()` |
| `pause()` | `GenesisEngine.cpp:167-178` | `pause()` |
| `resume()` | `GenesisEngine.cpp:180-195` | `resume()` |
| `update()` | `GenesisEngine.cpp:197-260` | `update()` |
| `getState()` | L55 | `state: EngineState` property |
| `isPlaying()` | L60 | `is_playing: bool` property |
| `setLooping()` | L80 | `looping: bool` property |
| `getDurationSeconds()` | L85 | `duration_seconds: float` property |
| `getPositionSeconds()` | L90 | `position_seconds: float` property |

#### Timing System (`GenesisEngine.cpp:197-260`)

**Critical formula** (`GenesisEngine.cpp:210-215`):
```cpp
// Arduino (fixed-point to avoid float on AVR)
uint32_t targetSamples = (elapsedMicros / 10000) * 441 +
                         ((elapsedMicros % 10000) * 441) / 10000;
```

```python
# Python equivalent
elapsed_ns = time.perf_counter_ns() - self._start_time_ns
target_samples = (elapsed_ns * 441) // 10_000_000_000
```

**Update loop** (`GenesisEngine.cpp:220-255`):
```python
def update(self):
    if self.state != EngineState.PLAYING:
        return

    elapsed_ns = time.perf_counter_ns() - self._start_time_ns
    target_samples = (elapsed_ns * 441) // 10_000_000_000

    while self._samples_played < target_samples:
        if self._waiting_samples > 0:
            consume = min(self._waiting_samples, target_samples - self._samples_played)
            self._waiting_samples -= consume
            self._samples_played += consume
        else:
            if self._parser.is_finished:
                if self.looping and self._parser.has_loop:
                    self._parser.seek_to_loop()
                else:
                    self.state = EngineState.FINISHED
                    return
            self._waiting_samples = self._parser.process_until_wait()
```

---

## Synth Module Mappings

### 9. `synth/fm_patch.py` ← `src/synth/FMPatch.h/cpp`

**Source**: `../GenesisEngine/src/synth/FMPatch.h` (139 lines), `FMPatch.cpp`

| Arduino | Python |
|---------|--------|
| `struct FMPatch` | `@dataclass class FMPatch` |
| `FMPatchUtils::loadToChannel()` | `FMPatch.load_to_channel(board, channel)` |
| `FMPatchUtils::getCarrierMask()` | `FMPatch.get_carrier_mask() -> List[bool]` |
| `FMPanMode` enum | `FMPanMode(Enum)` |

### 10. `synth/fm_frequency.py` ← `src/synth/FMFrequency.h/cpp`

**Source**: `../GenesisEngine/src/synth/FMFrequency.h` (123 lines), `FMFrequency.cpp`

| Arduino | Python |
|---------|--------|
| `FMFrequency::midiToFM()` | `midi_to_fm(note) -> Tuple[int, int]` |
| `FMFrequency::writeToChannel()` | `write_to_channel(board, channel, note)` |
| `FMFrequency::keyOn()` | `key_on(board, channel)` |
| `FMFrequency::keyOff()` | `key_off(board, channel)` |
| `fmFreqTable[128]` | `FM_FREQ_TABLE: List[Tuple[int, int]]` |

### 11. `synth/psg_frequency.py` ← `src/synth/PSGFrequency.h/cpp`

**Source**: `../GenesisEngine/src/synth/PSGFrequency.h` (117 lines), `PSGFrequency.cpp`

| Arduino | Python |
|---------|--------|
| `PSGFrequency::midiToTone()` | `midi_to_tone(note) -> int` |
| `PSGFrequency::writeToChannel()` | `write_to_channel(board, channel, note)` |
| `PSGFrequency::setVolume()` | `set_volume(board, channel, volume)` |
| `PSGFrequency::playNote()` | `play_note(board, channel, note, volume)` |
| `psgToneTable[128]` | `PSG_TONE_TABLE: List[int]` |

### 12. `synth/default_patches.py` ← `src/synth/DefaultPatches.h/cpp`

**Source**: `../GenesisEngine/src/synth/DefaultPatches.h` (53 lines), `DefaultPatches.cpp`

| Arduino | Python |
|---------|--------|
| `defaultFMPatches[8]` | `DEFAULT_FM_PATCHES: List[FMPatch]` |
| `DEFAULT_FM_PATCH_COUNT` | `len(DEFAULT_FM_PATCHES)` |

---

## Example Mappings

### Example 1: `jukebox.py` ← `examples/SDCardPlayer/SDCardPlayer.ino`

**Source**: `../GenesisEngine/examples/SDCardPlayer/SDCardPlayer.ino` (1087 lines)

| Arduino Function | Source Location | Python Function |
|------------------|-----------------|-----------------|
| `setup()` | L196-254 | `main()` initialization |
| `loop()` | L260-333 | `while True:` main loop |
| `scanFiles()` | L339-377 | `scan_files(directory)` |
| `playFileByIndex()` | L495-503 | `play_by_index(index)` |
| `playFileByName()` | L505-549 | `play_by_name(name)` |
| `processCommand()` | L797-993 | Command parsing with `input()` or argparse |

**Arduino main loop pattern** (`SDCardPlayer.ino:260-333`):
```cpp
void loop() {
    player.update();           // Timing critical
    // Check serial commands...
    // Handle playback state...
}
```

**Python equivalent**:
```python
def main():
    board = GenesisBoard()
    player = GenesisEngine(board)
    board.begin()

    # Scan for files
    vgm_files = list(Path(music_dir).glob("*.vgm"))
    vgm_files += list(Path(music_dir).glob("*.vgz"))

    # Play files
    for vgm_file in vgm_files:
        player.play(str(vgm_file))
        while player.is_playing:
            player.update()
            time.sleep(0.001)
```

---

### Example 2: `simple_synth.py` ← `examples/SimpleSynth/SimpleSynth.ino`

**Source**: `../GenesisEngine/examples/SimpleSynth/SimpleSynth.ino` (197 lines)

| Arduino Function | Source Location | Python Function |
|------------------|-----------------|-----------------|
| `setup()` | L47-63 | `main()` initialization |
| `loop()` | L65-121 | `while True:` command loop |
| `loadPatch()` | L123-136 | `load_patch(patch_num)` |
| `playFMNote()` | L138-155 | `play_fm_note(note)` |
| `stopFMNote()` | L157-163 | `stop_fm_note()` |
| `playPSGNote()` | L165-171 | `play_psg_note(note)` |
| `silenceAll()` | L173-182 | `silence_all()` |

**Arduino command handling** (`SimpleSynth.ino:65-121`):
```cpp
void loop() {
    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 'n': playFMNote(Serial.parseInt()); break;
            case 's': stopFMNote(); break;
            // ...
        }
    }
}
```

**Python equivalent**:
```python
def main():
    board = GenesisBoard()
    board.begin()
    board.reset()
    load_patch(0)

    print("Commands: n<note> s p<num> t<note> q")
    while True:
        cmd = input("> ").strip()
        if cmd.startswith('n'):
            play_fm_note(int(cmd[1:]))
        elif cmd == 's':
            stop_fm_note()
        # ...
```

---

### Example 3: `emulator_bridge.py` ← `examples/EmulatorBridge/EmulatorBridge.ino`

**Source**: `../GenesisEngine/examples/EmulatorBridge/EmulatorBridge.ino` (444 lines)
**Protocol**: `../GenesisEngine/examples/EmulatorBridge/BridgeProtocol.h` (113 lines)

#### Key Difference: Local IPC vs Serial

Arduino uses USB serial to communicate with BlastEm running on a PC.
On Pi, BlastEm runs locally, so we use Unix domain socket or named pipe instead.

| Arduino | Pi (Python) |
|---------|-------------|
| USB Serial @ 1Mbaud | Unix socket or FIFO |
| Ring buffer for USB jitter | Not needed (local IPC is fast) |
| State machine (BUFFERING) | Direct processing |

#### Protocol Constants (`BridgeProtocol.h`)

| Arduino | Python |
|---------|--------|
| `CMD_PING` (0xAA) | `CMD_PING = 0xAA` |
| `CMD_ACK` (0x0F) | `CMD_ACK = 0x0F` |
| `CMD_PSG_WRITE` (0x50) | Same as VGM commands |
| `CMD_YM2612_PORT0` (0x52) | Same as VGM commands |
| `CMD_YM2612_PORT1` (0x53) | Same as VGM commands |
| `CMD_END_STREAM` (0x66) | `CMD_END_STREAM = 0x66` |
| `FLOW_READY` (0x06) | `FLOW_READY = 0x06` |

#### Python Architecture

```python
import socket

def main():
    board = GenesisBoard()
    board.begin()

    # Create Unix socket for BlastEm to connect
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind('/tmp/genesis_bridge.sock')
    sock.listen(1)

    print("Waiting for BlastEm connection on /tmp/genesis_bridge.sock")
    conn, _ = sock.accept()

    while True:
        data = conn.recv(1)
        if not data:
            break

        cmd = data[0]
        if cmd == CMD_PING:
            conn.send(bytes([CMD_ACK, BOARD_TYPE_PI, FLOW_READY]))
            board.reset()
        elif cmd == 0x50:  # PSG
            val = conn.recv(1)[0]
            board.write_psg(val)
        elif cmd == 0x52:  # YM2612 port 0
            reg, val = conn.recv(2)
            board.write_ym2612(0, reg, val)
        elif cmd == 0x53:  # YM2612 port 1
            reg, val = conn.recv(2)
            board.write_ym2612(1, reg, val)
        elif cmd == 0x66:  # End stream
            board.reset()
            conn.send(bytes([FLOW_READY]))
```

**Note**: BlastEm will need a small modification or a proxy script to connect to the Unix socket instead of serial port.

---

## Hardware Configuration

### Default GPIO Mapping (BCM numbering)

| Function | Arduino Default | Pi GPIO | Physical Pin |
|----------|----------------|---------|--------------|
| WR_P | 2 | 17 | 11 |
| WR_Y | 3 | 27 | 13 |
| IC_Y | 4 | 22 | 15 |
| A0_Y | 5 | 23 | 16 |
| A1_Y | 6 | 24 | 18 |
| SPI MOSI | 11/51 | 10 (SPI0) | 19 |
| SPI SCLK | 13/52 | 11 (SPI0) | 23 |

### SPI Configuration

```python
import spidev

spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0
spi.max_speed_hz = 8_000_000  # 8 MHz (same as Arduino)
spi.mode = 0  # CPOL=0, CPHA=0
```

---

## Testing Verification

For each module, verify behavior matches Arduino:

### board.py
- [ ] `reset()` pulses IC_Y low for 500µs (`GenesisBoard.cpp:100-105`)
- [ ] `write_ym2612()` follows exact sequence (`GenesisBoard.cpp:117-175`)
- [ ] `write_psg()` applies bit reversal (`GenesisBoard.cpp:240-245`)
- [ ] Timing delays match (5µs YM, 9µs PSG) (`GenesisBoard.cpp:20-25`)

### vgm_parser.py
- [ ] Header parsing reads all fields (`VGMParser.cpp:42-120`)
- [ ] All commands handled per command table (`VGMParser.cpp:122-280`)
- [ ] PSG attenuation applied (`VGMParser.cpp:148-154`)
- [ ] Loop seeking works (`VGMParser.cpp:282-310`)

### engine.py
- [ ] Timing formula matches (`GenesisEngine.cpp:210-215`)
- [ ] State transitions match (`GenesisEngine.cpp`)
- [ ] Loop handling matches (`GenesisEngine.cpp:235-250`)

---

## Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "spidev>=3.5",
    "RPi.GPIO>=0.7.0",
]

[project.optional-dependencies]
pigpio = ["pigpio>=1.78"]  # For better timing accuracy
```

## Setup Commands

```bash
# Enable SPI on Raspberry Pi
sudo raspi-config  # Interface Options → SPI → Enable

# Install (from source)
pip install -e .

# Optional: pigpio for better timing
sudo apt install pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```
