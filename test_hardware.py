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
