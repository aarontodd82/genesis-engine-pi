"""
PSG frequency utilities for SN76489.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..board import GenesisBoard


# Pre-calculated tone table for MIDI notes 0-127
# Formula: N = 3579545 / (32 * freq)
# Based on NTSC PSG clock (3579545 Hz)
# Values > 1023 are clamped to 1023
PSG_TONE_TABLE: list[int] = [
    # Octave -1 (MIDI 0-11) - too low, clamp to max
    1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023,
    # Octave 0 (MIDI 12-23)
    1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023, 1023,
    # Octave 1 (MIDI 24-35)
    1023, 1023, 1023, 1023, 967, 912, 861, 813, 767, 724, 683, 645,
    # Octave 2 (MIDI 36-47)
    609, 575, 542, 512, 483, 456, 431, 407, 384, 362, 342, 323,
    # Octave 3 (MIDI 48-59)
    305, 287, 271, 256, 242, 228, 215, 203, 192, 181, 171, 161,
    # Octave 4 (MIDI 60-71) - Middle C at 60
    152, 144, 136, 128, 121, 114, 108, 102, 96, 91, 85, 81,
    # Octave 5 (MIDI 72-83)
    76, 72, 68, 64, 60, 57, 54, 51, 48, 45, 43, 40,
    # Octave 6 (MIDI 84-95)
    38, 36, 34, 32, 30, 28, 27, 25, 24, 23, 21, 20,
    # Octave 7 (MIDI 96-107)
    19, 18, 17, 16, 15, 14, 13, 13, 12, 11, 11, 10,
    # Octave 8+ (MIDI 108-127) - very high, values get small
    9, 9, 8, 8, 8, 7, 7, 6, 6, 6, 5, 5,
    5, 5, 4, 4, 4, 4, 3, 3,
]


def midi_to_tone(midi_note: int) -> int:
    """
    Convert MIDI note to SN76489 tone value.

    Args:
        midi_note: MIDI note number (0-127)

    Returns:
        10-bit tone value (1-1023)
    """
    midi_note = max(0, min(127, midi_note))
    return PSG_TONE_TABLE[midi_note]


def write_tone(board: "GenesisBoard", channel: int, tone: int) -> None:
    """
    Write raw tone value to PSG channel.

    Args:
        board: GenesisBoard instance
        channel: PSG tone channel (0-2)
        tone: 10-bit tone value (1-1023)
    """
    if channel > 2:
        return

    # Clamp tone to valid range
    if tone > 1023:
        tone = 1023
    if tone < 1:
        tone = 1

    # SN76489 tone format:
    # First byte:  1 CC 0 DDDD  (CC=channel, DDDD=low 4 bits of tone)
    # Second byte: 0 0 DD DDDD  (remaining 6 bits of tone)
    board.write_psg(0x80 | (channel << 5) | (tone & 0x0F))
    board.write_psg((tone >> 4) & 0x3F)


def write_to_channel(board: "GenesisBoard", channel: int, midi_note: int) -> None:
    """
    Write tone to PSG channel from MIDI note.

    Sets the frequency for a tone channel. Does NOT affect volume.

    Args:
        board: GenesisBoard instance
        channel: PSG tone channel (0-2)
        midi_note: MIDI note number (0-127)
    """
    if channel > 2:
        return
    tone = midi_to_tone(midi_note)
    write_tone(board, channel, tone)


def set_volume(board: "GenesisBoard", channel: int, volume: int) -> None:
    """
    Set PSG channel volume.

    Args:
        board: GenesisBoard instance
        channel: PSG channel (0-3, where 3 is noise)
        volume: Attenuation level (0=loudest, 15=silent)
    """
    if channel > 3:
        return
    if volume > 15:
        volume = 15

    # SN76489 volume format: 1 CC 1 VVVV (CC=channel, VVVV=attenuation)
    board.write_psg(0x90 | (channel << 5) | volume)


def set_noise(board: "GenesisBoard", white: bool, shift: int) -> None:
    """
    Configure and enable noise channel.

    Args:
        board: GenesisBoard instance
        white: True for white noise, False for periodic noise
        shift: Frequency source (0-3):
               0 = N/512 (high frequency)
               1 = N/1024 (medium frequency)
               2 = N/2048 (low frequency)
               3 = Use tone channel 2's frequency
    """
    if shift > 3:
        shift = 3

    # SN76489 noise format: 1110 0 W SS
    # W = white noise (1) or periodic (0)
    # SS = shift rate (0-3)
    noise_byte = 0xE0 | (0x04 if white else 0x00) | shift
    board.write_psg(noise_byte)


def play_note(
    board: "GenesisBoard", channel: int, midi_note: int, volume: int = 0
) -> None:
    """
    Play a note on PSG channel with volume.

    Sets both tone and volume in one call.

    Args:
        board: GenesisBoard instance
        channel: PSG tone channel (0-2)
        midi_note: MIDI note number (0-127)
        volume: Attenuation (0=loudest, 15=silent)
    """
    if channel > 2:
        return
    write_to_channel(board, channel, midi_note)
    set_volume(board, channel, volume)


def silence(board: "GenesisBoard", channel: int) -> None:
    """
    Silence a PSG channel.

    Args:
        board: GenesisBoard instance
        channel: PSG channel (0-3)
    """
    if channel > 3:
        return
    set_volume(board, channel, 15)  # 15 = maximum attenuation = silent
