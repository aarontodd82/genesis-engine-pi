"""
Synthesis utilities for direct chip control.

Provides MIDI-to-chip conversion, patch management,
and envelope generators for building synthesizers.
"""

from .fm_operator import FMOperator
from .fm_patch import FMPatch, FMPanMode
from .fm_frequency import (
    midi_to_fm,
    write_to_channel,
    key_on,
    key_off,
    FM_FREQ_TABLE,
)
from .psg_frequency import (
    midi_to_tone,
    write_tone,
    write_to_channel as psg_write_to_channel,
    set_volume,
    set_noise,
    play_note,
    silence,
    PSG_TONE_TABLE,
)
from .psg_envelope import PSGEnvelope, PSGEnvelopeState, EnvelopePhase
from .default_patches import DEFAULT_FM_PATCHES

__all__ = [
    # FM Operator
    "FMOperator",
    # FM Patch
    "FMPatch",
    "FMPanMode",
    # FM Frequency
    "midi_to_fm",
    "write_to_channel",
    "key_on",
    "key_off",
    "FM_FREQ_TABLE",
    # PSG Frequency
    "midi_to_tone",
    "write_tone",
    "psg_write_to_channel",
    "set_volume",
    "set_noise",
    "play_note",
    "silence",
    "PSG_TONE_TABLE",
    # PSG Envelope
    "PSGEnvelope",
    "PSGEnvelopeState",
    "EnvelopePhase",
    # Default Patches
    "DEFAULT_FM_PATCHES",
]
