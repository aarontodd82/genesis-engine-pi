"""
FMOperator - FM synthesis operator parameters.
"""

from dataclasses import dataclass


@dataclass
class FMOperator:
    """
    FM synthesis operator parameters.

    Each YM2612 channel has 4 operators. These parameters control
    the ADSR envelope, frequency ratio, and output level.

    Attributes:
        mul: Multiplier (0-15): 0=0.5x, 1=1x, 2=2x, etc.
        dt: Detune (0-7): 0-3=down, 4=none, 5-7=up. TFI uses 0-7 with 3=center.
        tl: Total Level (0-127): 0=loudest, 127=silent. Main volume control.
        rs: Rate Scaling (0-3): Higher values = faster decay at high notes.
        ar: Attack Rate (0-31): 31=instant attack, lower=slower.
        dr: Decay Rate (0-31): Rate of decay from peak to sustain level.
        sr: Sustain Rate (0-31): "Second decay" rate after sustain level reached.
        rr: Release Rate (0-15): Rate of decay after key-off.
        sl: Sustain Level (0-15): 0=max volume, 15=silent. Level held during sustain.
        ssg: SSG-EG mode (0-15): 0=off, 1-15=various looping/inverting envelopes.
    """

    mul: int = 1      # Multiplier (0-15)
    dt: int = 3       # Detune (0-7, 3 = no detune in TFI convention)
    tl: int = 0       # Total Level (0-127)
    rs: int = 0       # Rate Scaling (0-3)
    ar: int = 31      # Attack Rate (0-31)
    dr: int = 0       # Decay Rate (0-31)
    sr: int = 0       # Sustain Rate / D2R (0-31)
    rr: int = 15      # Release Rate (0-15)
    sl: int = 0       # Sustain Level (0-15)
    ssg: int = 0      # SSG-EG (0-15)

    def to_registers(self) -> dict:
        """
        Convert to YM2612 register values.

        Returns:
            Dict mapping register offset to value
        """
        return {
            0x30: ((self.dt & 0x07) << 4) | (self.mul & 0x0F),  # DT1/MUL
            0x40: self.tl & 0x7F,                                 # TL
            0x50: ((self.rs & 0x03) << 6) | (self.ar & 0x1F),    # RS/AR
            0x60: self.dr & 0x1F,                                 # D1R (AM bit not used here)
            0x70: self.sr & 0x1F,                                 # D2R
            0x80: ((self.sl & 0x0F) << 4) | (self.rr & 0x0F),    # D1L/RR
            0x90: self.ssg & 0x0F,                                # SSG-EG
        }
