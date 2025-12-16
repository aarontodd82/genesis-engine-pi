"""
FMPatch - Complete FM voice/patch definition.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, TYPE_CHECKING

from .fm_operator import FMOperator

if TYPE_CHECKING:
    from ..board import GenesisBoard


class FMPanMode(IntEnum):
    """Stereo panning modes."""

    CENTER = 0  # Both speakers (register value 0xC0)
    LEFT = 1    # Left only (register value 0x80)
    RIGHT = 2   # Right only (register value 0x40)


# YM2612 operator register offsets
# Maps FMPatch.operators index to register offset within a channel
# Index 0 (S1) -> offset 0, Index 1 (S3) -> offset 8,
# Index 2 (S2) -> offset 4, Index 3 (S4) -> offset 12
OPERATOR_OFFSETS = [0, 8, 4, 12]


@dataclass
class FMPatch:
    """
    Complete FM voice/patch definition.

    Contains all parameters needed to fully define an FM sound:
    - Algorithm: How the 4 operators connect (0-7)
    - Feedback: Self-modulation amount for operator 1 (0-7)
    - 4 operators with envelope and tuning parameters
    - Pan: Stereo placement
    - AMS/PMS: LFO sensitivity for tremolo/vibrato
    """

    algorithm: int = 0
    feedback: int = 0
    operators: List[FMOperator] = field(
        default_factory=lambda: [FMOperator() for _ in range(4)]
    )
    pan: FMPanMode = FMPanMode.CENTER
    ams: int = 0  # Amplitude Modulation Sensitivity (0-3)
    pms: int = 0  # Phase Modulation Sensitivity (0-7)

    def get_lr_ams_pms(self) -> int:
        """
        Get the raw YM2612 L/R/AMS/PMS register value.

        Returns:
            Value for register 0xB4 + channel offset
        """
        if self.pan == FMPanMode.LEFT:
            lr = 0x80
        elif self.pan == FMPanMode.RIGHT:
            lr = 0x40
        else:
            lr = 0xC0  # Center = both speakers
        return lr | ((self.ams & 0x03) << 4) | (self.pms & 0x07)

    def load_to_channel(self, board: "GenesisBoard", channel: int) -> None:
        """
        Load this patch to an FM channel.

        Writes all operator parameters, algorithm, feedback, and panning
        to the YM2612. Does not affect frequency or key state.

        Args:
            board: GenesisBoard instance
            channel: FM channel (0-5)
        """
        if channel > 5:
            return

        # Determine port and channel offset
        if channel < 3:
            port = 0
            ch_offset = channel
        else:
            port = 1
            ch_offset = channel - 3

        # Write operator parameters
        for op_idx, op in enumerate(self.operators):
            op_offset = OPERATOR_OFFSETS[op_idx]
            regs = op.to_registers()
            for base_reg, value in regs.items():
                reg = base_reg + op_offset + ch_offset
                board.write_ym2612(port, reg, value)

        # Write algorithm and feedback (register 0xB0 + channel)
        fb_alg = ((self.feedback & 0x07) << 3) | (self.algorithm & 0x07)
        board.write_ym2612(port, 0xB0 + ch_offset, fb_alg)

        # Write L/R/AMS/PMS (register 0xB4 + channel)
        board.write_ym2612(port, 0xB4 + ch_offset, self.get_lr_ams_pms())

    @staticmethod
    def get_carrier_mask(algorithm: int) -> List[bool]:
        """
        Get which operators are carriers for a given algorithm.

        Carriers produce audible output; modulators only affect other operators.
        Essential for velocity scaling (only scale carrier volumes).

        Args:
            algorithm: Algorithm number (0-7)

        Returns:
            List of 4 bools indicating carrier status (indices match op order)
        """
        # Carrier patterns by algorithm (in op index order S1,S3,S2,S4):
        # ALG 0-3: S4 only
        # ALG 4:   S2, S4
        # ALG 5-6: S2, S3, S4
        # ALG 7:   All carriers
        if algorithm <= 3:
            return [False, False, False, True]
        elif algorithm == 4:
            return [False, False, True, True]
        elif algorithm <= 6:
            return [False, True, True, True]
        else:
            return [True, True, True, True]
