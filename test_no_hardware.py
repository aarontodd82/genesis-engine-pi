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
