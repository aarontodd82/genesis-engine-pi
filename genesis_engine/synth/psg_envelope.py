"""
PSGEnvelope - Software envelope generator for PSG channels.

The SN76489 has no built-in envelope, so we implement one in software.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class EnvelopePhase(IntEnum):
    """Envelope phase."""
    IDLE = 0
    ATTACK = 1
    DECAY = 2
    SUSTAIN = 3
    RELEASE = 4


@dataclass
class PSGEnvelope:
    """
    Software envelope definition for PSG.

    Rates are in "steps per tick" where a tick is typically 1/60 sec.
    Volume goes from 0 (loudest) to 15 (silent).
    """

    attack_rate: int = 15     # Steps per tick during attack (higher = faster)
    decay_rate: int = 1       # Steps per tick during decay
    sustain_level: int = 0    # Sustain volume (0-15)
    release_rate: int = 1     # Steps per tick during release
    loop: bool = False        # Loop sustain phase


class PSGEnvelopeState:
    """Runtime state for a PSG envelope."""

    def __init__(self):
        self._envelope: Optional[PSGEnvelope] = None
        self._phase = EnvelopePhase.IDLE
        self._volume: int = 15  # 15 = silent
        self._accumulator: int = 0

    def trigger(self, envelope: PSGEnvelope) -> None:
        """Start the envelope from attack phase."""
        self._envelope = envelope
        self._phase = EnvelopePhase.ATTACK
        self._volume = 15  # Start silent
        self._accumulator = 0

    def release(self) -> None:
        """Enter release phase."""
        if self._phase != EnvelopePhase.IDLE:
            self._phase = EnvelopePhase.RELEASE

    def update(self) -> int:
        """
        Update envelope and return current volume.

        Call this once per tick (typically 60Hz).

        Returns:
            Volume level (0=loudest, 15=silent)
        """
        if not self._envelope or self._phase == EnvelopePhase.IDLE:
            return 15

        if self._phase == EnvelopePhase.ATTACK:
            self._accumulator += self._envelope.attack_rate
            steps = self._accumulator >> 4
            self._accumulator &= 0x0F
            self._volume = max(0, self._volume - steps)
            if self._volume <= 0:
                self._volume = 0
                self._phase = EnvelopePhase.DECAY

        elif self._phase == EnvelopePhase.DECAY:
            self._accumulator += self._envelope.decay_rate
            steps = self._accumulator >> 4
            self._accumulator &= 0x0F
            self._volume = min(15, self._volume + steps)
            if self._volume >= self._envelope.sustain_level:
                self._volume = self._envelope.sustain_level
                self._phase = EnvelopePhase.SUSTAIN

        elif self._phase == EnvelopePhase.SUSTAIN:
            if self._envelope.loop:
                pass  # Hold at sustain
            else:
                self._phase = EnvelopePhase.IDLE

        elif self._phase == EnvelopePhase.RELEASE:
            self._accumulator += self._envelope.release_rate
            steps = self._accumulator >> 4
            self._accumulator &= 0x0F
            self._volume = min(15, self._volume + steps)
            if self._volume >= 15:
                self._volume = 15
                self._phase = EnvelopePhase.IDLE

        return self._volume

    @property
    def is_active(self) -> bool:
        """Check if envelope is still producing sound."""
        return self._phase != EnvelopePhase.IDLE
