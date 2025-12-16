"""
FM frequency utilities for YM2612.
"""

from typing import Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..board import GenesisBoard


# Pre-calculated frequency table for MIDI notes 0-127
# Each entry is (fnum, block) for the YM2612
# Based on A4=440Hz, NTSC clock (7670453 Hz)
# Formula: freq = (fnum * clock) / (144 * 2^(21-block))
FM_FREQ_TABLE: list[Tuple[int, int]] = [
    # Octave -1 (MIDI 0-11)
    (617, 0), (654, 0), (693, 0), (734, 0), (778, 0), (824, 0),
    (873, 0), (925, 0), (980, 0), (1038, 0), (1100, 0), (1165, 0),
    # Octave 0 (MIDI 12-23)
    (617, 1), (654, 1), (693, 1), (734, 1), (778, 1), (824, 1),
    (873, 1), (925, 1), (980, 1), (1038, 1), (1100, 1), (1165, 1),
    # Octave 1 (MIDI 24-35)
    (617, 2), (654, 2), (693, 2), (734, 2), (778, 2), (824, 2),
    (873, 2), (925, 2), (980, 2), (1038, 2), (1100, 2), (1165, 2),
    # Octave 2 (MIDI 36-47)
    (617, 3), (654, 3), (693, 3), (734, 3), (778, 3), (824, 3),
    (873, 3), (925, 3), (980, 3), (1038, 3), (1100, 3), (1165, 3),
    # Octave 3 (MIDI 48-59)
    (617, 4), (654, 4), (693, 4), (734, 4), (778, 4), (824, 4),
    (873, 4), (925, 4), (980, 4), (1038, 4), (1100, 4), (1165, 4),
    # Octave 4 (MIDI 60-71) - Middle C starts here
    (617, 5), (654, 5), (693, 5), (734, 5), (778, 5), (824, 5),
    (873, 5), (925, 5), (980, 5), (1038, 5), (1100, 5), (1165, 5),
    # Octave 5 (MIDI 72-83)
    (617, 6), (654, 6), (693, 6), (734, 6), (778, 6), (824, 6),
    (873, 6), (925, 6), (980, 6), (1038, 6), (1100, 6), (1165, 6),
    # Octave 6 (MIDI 84-95)
    (617, 7), (654, 7), (693, 7), (734, 7), (778, 7), (824, 7),
    (873, 7), (925, 7), (980, 7), (1038, 7), (1100, 7), (1165, 7),
    # Octave 7 (MIDI 96-107) - clamped to block 7
    (617, 7), (654, 7), (693, 7), (734, 7), (778, 7), (824, 7),
    (873, 7), (925, 7), (980, 7), (1038, 7), (1100, 7), (1165, 7),
    # Octave 8+ (MIDI 108-119) - clamped
    (617, 7), (654, 7), (693, 7), (734, 7), (778, 7), (824, 7),
    (873, 7), (925, 7), (980, 7), (1038, 7), (1100, 7), (1165, 7),
    # MIDI 120-127 - clamped
    (617, 7), (654, 7), (693, 7), (734, 7), (778, 7), (824, 7),
    (873, 7), (925, 7),
]


def midi_to_fm(midi_note: int) -> Tuple[int, int]:
    """
    Convert MIDI note to YM2612 F-number and block.

    Args:
        midi_note: MIDI note number (0-127, 60=middle C)

    Returns:
        Tuple of (fnum, block)
    """
    midi_note = max(0, min(127, midi_note))
    return FM_FREQ_TABLE[midi_note]


def write_to_channel(board: "GenesisBoard", channel: int, midi_note: int) -> None:
    """
    Write frequency to FM channel.

    Looks up the MIDI note in the frequency table and writes to the
    YM2612's frequency registers. Does NOT trigger key on.

    Args:
        board: GenesisBoard instance
        channel: FM channel (0-5)
        midi_note: MIDI note number (0-127)
    """
    fnum, block = midi_to_fm(midi_note)

    # Determine port and channel offset
    if channel < 3:
        port = 0
        ch_offset = channel
    else:
        port = 1
        ch_offset = channel - 3

    # Write frequency registers
    # Register 0xA4+ch: block (bits 5-3) and fnum high (bits 2-0)
    # Register 0xA0+ch: fnum low (bits 7-0)
    freq_hi = ((block & 0x07) << 3) | ((fnum >> 8) & 0x07)
    freq_lo = fnum & 0xFF

    # IMPORTANT: Write high byte first (latches on low byte write)
    board.write_ym2612(port, 0xA4 + ch_offset, freq_hi)
    board.write_ym2612(port, 0xA0 + ch_offset, freq_lo)


def key_on(board: "GenesisBoard", channel: int, operator_mask: int = 0xF0) -> None:
    """
    Key on (start note) for FM channel.

    Triggers the attack phase of the envelope for specified operators.
    Call this after setting frequency to start the note.

    Args:
        board: GenesisBoard instance
        channel: FM channel (0-5)
        operator_mask: Which operators to key on (default 0xF0 = all four)
    """
    # Key on register (0x28) on port 0
    # Bits 7-4: operator enable, bits 2-0: channel
    ch_val = channel if channel < 3 else (channel - 3 + 4)
    board.write_ym2612(0, 0x28, operator_mask | ch_val)


def key_off(board: "GenesisBoard", channel: int) -> None:
    """
    Key off (release note) for FM channel.

    Triggers the release phase of the envelope.

    Args:
        board: GenesisBoard instance
        channel: FM channel (0-5)
    """
    ch_val = channel if channel < 3 else (channel - 3 + 4)
    board.write_ym2612(0, 0x28, ch_val)  # Operator mask = 0
