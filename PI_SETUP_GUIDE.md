# GenesisEngine-Pi: Complete Setup Guide

This guide assumes you know nothing about Raspberry Pi. It will walk you through every step from a blank SD card to running the GenesisEngine library.

**What you'll need:**
- Raspberry Pi 4 (any RAM size)
- MicroSD card (16GB or larger recommended)
- USB-C power supply for Pi 4 (5V 3A)
- MicroSD card reader for your Windows PC
- Ethernet cable OR WiFi network name/password
- GenesisEngine board + jumper wires (for hardware testing)

---

## Part 1: Creating the SD Card

### Step 1.1: Download Raspberry Pi Imager

1. Open your web browser
2. Go to: https://www.raspberrypi.com/software/
3. Click the **"Download for Windows"** button
4. Run the downloaded `imager_x.x.x.exe` file
5. Click **Yes** if Windows asks for permission
6. Click **Install**, then **Finish**

### Step 1.2: Insert Your SD Card

1. Insert your microSD card into your card reader
2. Plug the card reader into your Windows PC
3. Windows might pop up asking to format - click **Cancel**

### Step 1.3: Write the Operating System

1. Open **Raspberry Pi Imager** (search for it in Start menu)

2. Click **"CHOOSE DEVICE"**
   - Select **"Raspberry Pi 4"**

3. Click **"CHOOSE OS"**
   - Select **"Raspberry Pi OS (64-bit)"** (the first option, includes desktop)

4. Click **"CHOOSE STORAGE"**
   - Select your SD card (careful not to select your main drive!)
   - It will show the size, like "31.9 GB" for a 32GB card

5. Click **"NEXT"**

6. **IMPORTANT:** A popup asks "Would you like to apply OS customisation settings?"
   - Click **"EDIT SETTINGS"**

7. In the **"GENERAL"** tab, fill in:
   ```
   ☑ Set hostname: raspberrypi
   ☑ Set username and password
       Username: pi
       Password: [choose something you'll remember, like "genesis123"]
   ☑ Configure wireless LAN (if using WiFi)
       SSID: [your WiFi network name, exactly as it appears]
       Password: [your WiFi password]
       Wireless LAN country: US
   ☑ Set locale settings
       Time zone: [your timezone, e.g., America/New_York]
       Keyboard layout: us
   ```

8. Click the **"SERVICES"** tab:
   ```
   ☑ Enable SSH
   ● Use password authentication
   ```

9. Click **"SAVE"**

10. Click **"YES"** to apply the settings

11. Click **"YES"** to confirm (this will erase everything on the SD card)

12. Wait for it to write and verify (takes 5-10 minutes)

13. When it says "Write Successful", click **"CONTINUE"**

14. Remove the SD card from your computer

---

## Part 2: First Boot of the Raspberry Pi

### Step 2.1: Connect Everything

1. Insert the microSD card into the Pi (slot is on the bottom)
2. Connect an Ethernet cable to the Pi (recommended for first setup)
   - OR just use WiFi if you configured it in Step 1.3
3. **DO NOT** connect the GenesisEngine board yet
4. Plug in the USB-C power cable (the Pi has no power button - it turns on automatically)

### Step 2.2: Wait for Boot

1. The green LED on the Pi will flicker as it boots
2. First boot takes 1-3 minutes (it's resizing the filesystem)
3. Wait until the green LED mostly stops flickering

### Step 2.3: Find Your Pi's IP Address

You need to know the Pi's IP address to connect to it. Here are several ways:

**Method A: Using your router**
1. Log into your router's admin page (usually http://192.168.1.1 or similar)
2. Look for "Connected Devices" or "DHCP Clients"
3. Find "raspberrypi" and note its IP address (like 192.168.1.105)

**Method B: Using hostname (may not work on all networks)**
1. The Pi should be reachable at `raspberrypi.local`
2. Test by opening Command Prompt and typing: `ping raspberrypi.local`
3. If it responds, you can use `raspberrypi.local` instead of an IP address

**Method C: Using Advanced IP Scanner (free tool)**
1. Download from: https://www.advanced-ip-scanner.com/
2. Install and run it
3. Click "Scan"
4. Look for "raspberrypi" in the list

For this guide, I'll use `raspberrypi.local` but substitute your IP if that doesn't work.

### Step 2.4: Test SSH Connection

1. Open **Command Prompt** on Windows (search "cmd" in Start menu)

2. Type:
   ```
   ssh pi@raspberrypi.local
   ```

3. If it asks "Are you sure you want to continue connecting (yes/no/[fingerprint])?"
   - Type: `yes`
   - Press Enter

4. Enter your password (the one you set in Step 1.3)
   - **Note:** When typing passwords in SSH, nothing appears on screen - that's normal!
   - Press Enter after typing your password

5. You should see something like:
   ```
   pi@raspberrypi:~ $
   ```

6. Congratulations! You're now connected to your Pi!

7. Type `exit` and press Enter to disconnect (we'll reconnect from VS Code)

---

## Part 3: Setting Up VS Code for Remote Development

### Step 3.1: Install VS Code (if you don't have it)

1. Go to: https://code.visualstudio.com/
2. Click **"Download for Windows"**
3. Run the installer, accept all defaults

### Step 3.2: Install the Remote SSH Extension

1. Open VS Code
2. Click the **Extensions** icon in the left sidebar (looks like 4 squares)
3. In the search box, type: `Remote - SSH`
4. Find **"Remote - SSH"** by Microsoft (should be first result)
5. Click the blue **"Install"** button
6. Wait for it to install (10-20 seconds)

### Step 3.3: Connect to Your Pi

1. Press `Ctrl+Shift+P` to open the Command Palette
2. Type: `Remote-SSH: Connect to Host`
3. Press Enter
4. Click **"+ Add New SSH Host..."**
5. Type: `ssh pi@raspberrypi.local`
6. Press Enter
7. Select the first option for config file (usually `C:\Users\YourName\.ssh\config`)
8. Click **"Connect"** in the popup that appears (bottom right)

9. A new VS Code window opens
10. It asks "Select the platform of the remote host":
    - Click **"Linux"**
11. Enter your password when prompted
12. Wait while VS Code installs its server on the Pi (1-2 minutes first time)

13. You should see "SSH: raspberrypi.local" in the bottom-left corner of VS Code

### Step 3.4: Install Python Extension on Remote

1. In the VS Code window connected to the Pi:
2. Click the **Extensions** icon (left sidebar)
3. Search for: `Python`
4. Install **"Python"** by Microsoft (click "Install in SSH: raspberrypi.local")
5. Wait for it to install

---

## Part 4: Setting Up the Pi for Development

### Step 4.1: Open a Terminal in VS Code

1. In VS Code (connected to Pi), press `Ctrl+`` (backtick, key below Escape)
2. A terminal panel opens at the bottom
3. You should see: `pi@raspberrypi:~ $`

### Step 4.2: Update the System

Copy and paste these commands one at a time (right-click to paste in terminal):

```bash
sudo apt update
```
(Enter your password if asked - same password as before)

```bash
sudo apt upgrade -y
```
(This takes 2-5 minutes)

### Step 4.3: Install Required Packages

```bash
sudo apt install -y python3-pip python3-venv git python3-dev
```

### Step 4.4: Enable SPI

SPI is how the Pi talks to the GenesisEngine board.

```bash
sudo raspi-config
```

A blue menu appears. Use arrow keys and Enter to navigate:

1. Select **"3 Interface Options"** → Press Enter
2. Select **"I4 SPI"** → Press Enter
3. "Would you like the SPI interface to be enabled?" → Select **"Yes"** → Press Enter
4. Press Enter on "OK"
5. Press Tab to select **"Finish"** → Press Enter
6. If it asks to reboot, select **"Yes"**

If it didn't ask to reboot:
```bash
sudo reboot
```

The connection will drop. Wait 30 seconds, then reconnect:
- Press `Ctrl+Shift+P`
- Type: `Remote-SSH: Connect to Host`
- Select `raspberrypi.local`
- Enter password

### Step 4.5: Verify SPI is Enabled

Open a new terminal (Ctrl+`) and run:

```bash
ls /dev/spi*
```

You should see:
```
/dev/spidev0.0  /dev/spidev0.1
```

If you don't see these, SPI isn't enabled. Go back to Step 4.4.

---

## Part 5: Getting the Code onto the Pi

### Step 5.1: Create Project Directory

```bash
mkdir -p ~/projects
cd ~/projects
```

### Step 5.2: Copy Files from Windows

**Option A: Using Git (if you've pushed to GitHub)**

```bash
git clone https://github.com/aarontodd82/genesis-engine-pi.git
cd genesis-engine-pi
```

**Option B: Copy from Windows using SCP**

1. Open a NEW Command Prompt on Windows (not the VS Code terminal)
2. Navigate to where your project is:
   ```
   cd "C:\Users\aaron\OneDrive\Documents\FM-90s\GenesisEngine-Pi"
   ```
3. Copy to Pi:
   ```
   scp -r . pi@raspberrypi.local:~/projects/genesis-engine-pi/
   ```
4. Enter your password

**Option C: Copy using VS Code**

1. Open a local VS Code window (File → New Window)
2. Open the GenesisEngine-Pi folder on Windows
3. Select all files in the explorer (Ctrl+A)
4. Copy (Ctrl+C)
5. In your remote VS Code window, open ~/projects/ folder
6. Create new folder "genesis-engine-pi"
7. Paste (Ctrl+V)

### Step 5.3: Open the Project in VS Code

1. In VS Code (connected to Pi):
2. File → Open Folder
3. Navigate to: `/home/pi/projects/genesis-engine-pi`
4. Click **"OK"**
5. If it asks "Do you trust the authors?", click **"Yes"**

You should now see all the project files in the left sidebar!

---

## Part 6: Setting Up Python Environment

### Step 6.1: Create Virtual Environment

Open terminal (Ctrl+`) and run:

```bash
cd ~/projects/genesis-engine-pi
python3 -m venv venv
```

### Step 6.2: Activate Virtual Environment

```bash
source venv/bin/activate
```

Your prompt should now show `(venv)` at the beginning:
```
(venv) pi@raspberrypi:~/projects/genesis-engine-pi $
```

### Step 6.3: Install the Library in Development Mode

```bash
pip install -e .
```

This installs your library in "editable" mode. When you change the code, the changes take effect immediately without reinstalling.

### Step 6.4: Select Python Interpreter in VS Code

1. Press `Ctrl+Shift+P`
2. Type: `Python: Select Interpreter`
3. Choose the one that shows `./venv/bin/python`

---

## Part 7: Testing WITHOUT Hardware

Before connecting the GenesisEngine board, let's test that the code works.

### Step 7.1: Test Basic Imports

In VS Code terminal:

```bash
python3 -c "from genesis_engine import GenesisBoard; print('Import OK!')"
```

You should see: `Import OK!`

### Step 7.2: Test VGM Parsing (No Hardware Needed)

Create a simple test script. In VS Code:

1. Right-click in the file explorer → New File
2. Name it: `test_no_hardware.py`
3. Paste this content:

```python
#!/usr/bin/env python3
"""Test script that doesn't require hardware."""

import sys
sys.path.insert(0, '.')

# Test imports
print("Testing imports...")
from genesis_engine import GenesisEngine, GenesisBoard, EngineState
from genesis_engine.vgm_parser import VGMParser
from genesis_engine.sources.file_source import FileSource
from genesis_engine.synth import (
    FMPatch, FMOperator, DEFAULT_FM_PATCHES,
    midi_to_fm, midi_to_tone,
)
print("  All imports successful!")

# Test FM frequency table
print("\nTesting FM frequency conversion...")
for midi_note in [36, 48, 60, 72, 84]:  # C2, C3, C4, C5, C6
    fnum, block = midi_to_fm(midi_note)
    print(f"  MIDI {midi_note}: fnum={fnum}, block={block}")

# Test PSG frequency table
print("\nTesting PSG frequency conversion...")
for midi_note in [36, 48, 60, 72, 84]:
    tone = midi_to_tone(midi_note)
    print(f"  MIDI {midi_note}: tone={tone}")

# Test default patches
print("\nTesting default FM patches...")
for i, patch in enumerate(DEFAULT_FM_PATCHES):
    print(f"  Patch {i}: alg={patch.algorithm}, fb={patch.feedback}")

# Test patch register generation
print("\nTesting register generation for Patch 0...")
patch = DEFAULT_FM_PATCHES[0]
for op_idx, op in enumerate(patch.operators):
    regs = op.to_registers()
    print(f"  Operator {op_idx}: {len(regs)} registers")

print("\n" + "="*50)
print("All tests passed! Software is working correctly.")
print("="*50)
```

4. Save the file (Ctrl+S)

5. Run it:
```bash
python3 test_no_hardware.py
```

You should see output like:
```
Testing imports...
  All imports successful!

Testing FM frequency conversion...
  MIDI 36: fnum=617, block=3
  MIDI 48: fnum=617, block=4
  ...

All tests passed! Software is working correctly.
```

---

## Part 8: Hardware Wiring

**IMPORTANT: Power off the Pi before connecting wires!**

```bash
sudo shutdown now
```

Wait for the green LED to stop flashing, then unplug the power.

### Step 8.1: Pin Reference

The Raspberry Pi 4 GPIO header has 40 pins. Here's how to identify them:

```
Looking at the Pi with USB ports facing you:

                    3.3V (1)  (2) 5V
                   GPIO2 (3)  (4) 5V
                   GPIO3 (5)  (6) GND
                   GPIO4 (7)  (8) GPIO14
                     GND (9)  (10) GPIO15
           WR_P → GPIO17 (11) (12) GPIO18
           WR_Y → GPIO27 (13) (14) GND
           IC_Y → GPIO22 (15) (16) GPIO23 ← A0_Y
                    3.3V (17) (18) GPIO24 ← A1_Y
      SPI MOSI → GPIO10 (19) (20) GND
                   GPIO9 (21) (22) GPIO25
      SPI SCLK → GPIO11 (23) (24) GPIO8
                     GND (25) (26) GPIO7
```

### Step 8.2: Connections to GenesisEngine Board

Connect these pins from the Pi to your GenesisEngine board:

| Pi Pin | Pi GPIO | Function | GenesisBoard Pin |
|--------|---------|----------|------------------|
| 11 | GPIO17 | WR_P (PSG write strobe) | WR_P |
| 13 | GPIO27 | WR_Y (YM2612 write strobe) | WR_Y |
| 15 | GPIO22 | IC_Y (YM2612 reset) | IC_Y |
| 16 | GPIO23 | A0_Y (address/data select) | A0 |
| 18 | GPIO24 | A1_Y (port select) | A1 |
| 19 | GPIO10 | SPI MOSI (data out) | DATA or MOSI |
| 23 | GPIO11 | SPI SCLK (clock) | CLK or SCLK |
| 6, 9, 14, 20, or 25 | GND | Ground | GND |

**IMPORTANT:** The GenesisEngine board needs its own power supply! The Pi's 5V pin cannot provide enough current. Connect:
- GenesisBoard 5V → External 5V supply (not from Pi)
- GenesisBoard GND → Pi GND (must share ground!)

### Step 8.3: Double-Check Wiring

Before powering on:
1. Verify no wires are loose
2. Verify GND is connected between Pi and GenesisBoard
3. Verify the GenesisBoard has its own 5V power supply
4. Make sure no pins are shorted

### Step 8.4: Power Up Sequence

1. Connect GenesisBoard power supply (don't turn on yet)
2. Plug in Pi power
3. Wait for Pi to boot (green LED stops flickering)
4. Turn on GenesisBoard power supply

---

## Part 9: Testing WITH Hardware

### Step 9.1: Reconnect to Pi

After powering up the Pi:

1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type: `Remote-SSH: Connect to Host`
4. Select `raspberrypi.local`
5. Enter password

### Step 9.2: Create Hardware Test Script

Create a new file `test_hardware.py`:

```python
#!/usr/bin/env python3
"""Hardware connection test."""

import time
import sys

print("="*50)
print("GenesisEngine Hardware Test")
print("="*50)

# Check if we're on a Pi with hardware
try:
    import spidev
    import RPi.GPIO as GPIO
    print("✓ SPI and GPIO libraries available")
except ImportError as e:
    print(f"✗ Missing library: {e}")
    print("  Run: pip install spidev RPi.GPIO")
    sys.exit(1)

# Test SPI device exists
import os
if os.path.exists('/dev/spidev0.0'):
    print("✓ SPI device /dev/spidev0.0 exists")
else:
    print("✗ SPI device not found - is SPI enabled?")
    print("  Run: sudo raspi-config → Interface Options → SPI → Enable")
    sys.exit(1)

# Try to initialize the board
print("\nInitializing GenesisBoard...")
try:
    from genesis_engine import GenesisBoard
    board = GenesisBoard()
    board.begin()
    print("✓ GenesisBoard initialized successfully!")
except Exception as e:
    print(f"✗ Failed to initialize: {e}")
    sys.exit(1)

# Test reset
print("\nTesting chip reset...")
try:
    board.reset()
    print("✓ Reset successful")
except Exception as e:
    print(f"✗ Reset failed: {e}")

# Test PSG - play a beep
print("\nTesting PSG (you should hear a beep)...")
try:
    # Set channel 0 to a tone
    board.write_psg(0x8F)  # Channel 0, freq low nibble = 15
    board.write_psg(0x0A)  # Freq high bits
    board.write_psg(0x90)  # Channel 0, volume = 0 (loudest)
    print("  Playing tone...")
    time.sleep(0.5)
    board.write_psg(0x9F)  # Channel 0, volume = 15 (silent)
    print("✓ PSG test complete")
except Exception as e:
    print(f"✗ PSG test failed: {e}")

# Test YM2612 - simple FM beep
print("\nTesting YM2612 (you should hear an FM tone)...")
try:
    # Very basic FM sound - just enable a sine wave
    # Set up channel 0, operator 4 as a simple carrier

    # Algorithm 7 (all operators output)
    board.write_ym2612(0, 0xB0, 0x07)

    # Operator 4 settings (slot 4 = register offset 0x0C)
    board.write_ym2612(0, 0x3C, 0x01)  # DT1/MUL = 1
    board.write_ym2612(0, 0x4C, 0x00)  # TL = 0 (loudest)
    board.write_ym2612(0, 0x5C, 0x1F)  # RS/AR = 31 (instant attack)
    board.write_ym2612(0, 0x6C, 0x00)  # D1R = 0
    board.write_ym2612(0, 0x7C, 0x00)  # D2R = 0
    board.write_ym2612(0, 0x8C, 0x0F)  # D1L/RR = sustain 0, release 15

    # Set frequency (A4 = 440 Hz)
    board.write_ym2612(0, 0xA4, 0x22)  # Block 4, F-num high
    board.write_ym2612(0, 0xA0, 0x69)  # F-num low

    # Key on (all 4 operators)
    board.write_ym2612(0, 0x28, 0xF0)
    print("  Playing FM tone...")
    time.sleep(0.5)

    # Key off
    board.write_ym2612(0, 0x28, 0x00)
    print("✓ YM2612 test complete")
except Exception as e:
    print(f"✗ YM2612 test failed: {e}")

# Cleanup
print("\nCleaning up...")
board.mute_all()
board.cleanup()

print("\n" + "="*50)
print("Hardware test complete!")
print("If you heard both beeps, everything is working!")
print("="*50)
```

### Step 9.3: Run Hardware Test

```bash
cd ~/projects/genesis-engine-pi
source venv/bin/activate
python3 test_hardware.py
```

You should:
1. See all checkmarks (✓)
2. Hear a short beep from the PSG
3. Hear a short tone from the YM2612

### Step 9.4: If Something Goes Wrong

**"Permission denied" on SPI:**
```bash
sudo usermod -a -G spi pi
sudo reboot
```

**No sound from PSG:**
- Check WR_P connection (Pin 11 → WR_P)
- Check DATA/MOSI connection (Pin 19)
- Check SCLK connection (Pin 23)
- Check GND connection

**No sound from YM2612:**
- Check WR_Y connection (Pin 13 → WR_Y)
- Check IC_Y connection (Pin 15 → IC_Y)
- Check A0 connection (Pin 16 → A0)
- Check A1 connection (Pin 18 → A1)

**Both silent:**
- Check GenesisBoard has power
- Check GND is shared between Pi and GenesisBoard
- Check audio output connection from GenesisBoard

---

## Part 10: Running the Examples

### Step 10.1: Simple Synth

```bash
cd ~/projects/genesis-engine-pi
source venv/bin/activate
python3 examples/simple_synth.py
```

Commands to try:
- `n60` - Play middle C on FM
- `n72` - Play high C on FM
- `s` - Stop FM note
- `p1` - Switch to bass patch
- `n36` - Play low note
- `t60` - Play PSG tone
- `q` - Silence all
- `exit` - Quit

### Step 10.2: Jukebox (VGM Player)

First, get some VGM files:

```bash
mkdir -p ~/music
cd ~/music
# Download a test file (Sonic 1 Green Hill Zone)
wget https://vgmrips.net/packs/pack/sonic-the-hedgehog-sega-genesis -O sonic.zip
unzip sonic.zip
```

Or copy VGM files from your Windows machine:
```
scp "C:\path\to\your\music\*.vgm" pi@raspberrypi.local:~/music/
```

Run the jukebox:
```bash
cd ~/projects/genesis-engine-pi
source venv/bin/activate
python3 examples/jukebox.py ~/music
```

Commands:
- `list` - Show available files
- `1` - Play first file
- `next` / `prev` - Navigate tracks
- `pause` - Pause/resume
- `loop` - Toggle looping
- `stop` - Stop playback
- `quit` - Exit

---

## Part 11: Development Workflow

Now that everything is set up, here's how to work on the code:

### Making Changes

1. Edit files in VS Code (they're on the Pi)
2. Save (Ctrl+S)
3. Run in terminal: `python3 examples/simple_synth.py`
4. Changes take effect immediately (no reinstall needed)

### Syncing from Windows

If you prefer to edit on Windows:

1. Make changes on Windows
2. In Windows Command Prompt:
   ```
   cd "C:\Users\aaron\OneDrive\Documents\FM-90s\GenesisEngine-Pi"
   scp -r genesis_engine examples pi@raspberrypi.local:~/projects/genesis-engine-pi/
   ```
3. Test on Pi

### Adding Debug Output

Add print statements anywhere:
```python
print(f"DEBUG: Writing to register 0x{reg:02X} = 0x{val:02X}")
```

### Using the Debugger

1. Set a breakpoint by clicking left of a line number (red dot appears)
2. Press F5 to start debugging
3. Select "Python File"
4. Code stops at breakpoints
5. Use F10 (step over), F11 (step into), F5 (continue)

---

## Part 12: Shutting Down Safely

**Always shut down the Pi properly to avoid SD card corruption!**

```bash
sudo shutdown now
```

Wait for the green LED to stop, then unplug power.

To reboot instead:
```bash
sudo reboot
```

---

## Quick Reference

### Connect to Pi
```bash
# From Windows Command Prompt
ssh pi@raspberrypi.local
```

### VS Code Remote
- `Ctrl+Shift+P` → "Remote-SSH: Connect to Host" → `raspberrypi.local`

### Activate Virtual Environment
```bash
cd ~/projects/genesis-engine-pi
source venv/bin/activate
```

### Run Examples
```bash
python3 examples/simple_synth.py
python3 examples/jukebox.py ~/music
python3 examples/emulator_bridge.py
```

### GPIO Pin Quick Reference
```
Pin 11 (GPIO17) → WR_P
Pin 13 (GPIO27) → WR_Y
Pin 15 (GPIO22) → IC_Y
Pin 16 (GPIO23) → A0
Pin 18 (GPIO24) → A1
Pin 19 (GPIO10) → DATA/MOSI
Pin 23 (GPIO11) → CLK/SCLK
Pin 6/9/14/20/25 → GND
```

---

## Troubleshooting

### "Connection refused" when SSH-ing
- Pi might still be booting, wait 30 seconds
- Check that Pi is connected to network
- Verify IP address is correct

### "Permission denied" for GPIO/SPI
```bash
sudo usermod -a -G gpio,spi pi
sudo reboot
```

### VS Code can't connect
- Make sure SSH works from Command Prompt first
- Try using IP address instead of `raspberrypi.local`

### No sound at all
- Check audio cables from GenesisBoard
- Verify GenesisBoard has power
- Run `test_hardware.py` to diagnose

### VGM plays but sounds wrong
- Check all 7 data connections (5 control + 2 SPI)
- Verify wiring matches the pin table exactly
