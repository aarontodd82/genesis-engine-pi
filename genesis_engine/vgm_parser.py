"""
VGMParser - Parse and execute VGM commands.
"""

from typing import Callable, Optional

from .board import GenesisBoard
from .pcm_bank import PCMDataBank
from .sources.base import VGMSource
from .vgm_commands import (
    VGM_MAGIC,
    VGM_HEADER_VERSION,
    VGM_HEADER_SN76489_CLOCK,
    VGM_HEADER_YM2612_CLOCK,
    VGM_HEADER_TOTAL_SAMPLES,
    VGM_HEADER_LOOP_OFFSET,
    VGM_HEADER_LOOP_SAMPLES,
    VGM_HEADER_DATA_OFFSET,
    VGM_DEFAULT_DATA_OFFSET,
    VGM_CMD_PSG_WRITE,
    VGM_CMD_YM2612_PORT0,
    VGM_CMD_YM2612_PORT1,
    VGM_CMD_WAIT_N,
    VGM_CMD_WAIT_NTSC,
    VGM_CMD_WAIT_PAL,
    VGM_CMD_END,
    VGM_CMD_DATA_BLOCK,
    VGM_CMD_WAIT_SHORT_BASE,
    VGM_CMD_DAC_WAIT_BASE,
    VGM_CMD_PCM_SEEK,
    VGM_WAIT_NTSC,
    VGM_WAIT_PAL,
    YM2612_REG_DAC_DATA,
)


class VGMParser:
    """
    VGM format parser and command dispatcher.

    Reads VGM data from a source and dispatches chip write commands
    to the GenesisBoard. Handles timing by returning wait sample counts.
    """

    def __init__(self, board: GenesisBoard):
        """
        Initialize parser with a board reference.

        Args:
            board: GenesisBoard instance for chip writes
        """
        self._board = board
        self._source: Optional[VGMSource] = None
        self._pcm_bank = PCMDataBank()

        # Header data
        self._version: int = 0
        self._total_samples: int = 0
        self._loop_offset: int = 0
        self._loop_samples: int = 0
        self._data_offset: int = 0
        self._has_ym2612: bool = False
        self._has_sn76489: bool = False

        # State
        self._finished: bool = False
        self._loop_count: int = 0

    def set_source(self, source: VGMSource) -> None:
        """
        Set the VGM data source.

        Args:
            source: VGMSource instance to read from
        """
        self._source = source
        self._finished = False
        self._loop_count = 0
        self._pcm_bank.clear()

    def parse_header(self) -> bool:
        """
        Parse the VGM file header.

        Reads version, chip clocks, total samples, loop info, and data offset.
        Must be called after set_source() and before process_until_wait().

        Returns:
            True if header is valid
        """
        if not self._source or not self._source.is_open:
            return False

        # Verify magic number
        magic = self._source.read_uint32()
        if magic != VGM_MAGIC:
            return False

        # Skip to version (offset 0x08)
        self._source.skip(4)  # Skip EOF offset
        self._version = self._source.read_uint32()

        # SN76489 clock (offset 0x0C)
        sn76489_clock = self._source.read_uint32()
        self._has_sn76489 = sn76489_clock != 0

        # Skip YM2413 clock (0x10), GD3 offset (0x14)
        self._source.skip(8)

        # Total samples (offset 0x18)
        self._total_samples = self._source.read_uint32()

        # Loop offset (offset 0x1C) - relative to 0x1C
        loop_offset_rel = self._source.read_uint32()
        self._loop_offset = (0x1C + loop_offset_rel) if loop_offset_rel else 0

        # Loop samples (offset 0x20)
        self._loop_samples = self._source.read_uint32()

        # Skip to YM2612 clock (offset 0x2C)
        self._source.skip(8)  # Skip rate (0x24), SN flags (0x28)
        ym2612_clock = self._source.read_uint32()
        self._has_ym2612 = ym2612_clock != 0

        # Data offset (offset 0x34) - v1.50+ only
        self._source.skip(4)  # Skip YM2151 clock (0x30)
        if self._version >= 0x150:
            data_offset_rel = self._source.read_uint32()
            self._data_offset = 0x34 + data_offset_rel if data_offset_rel else VGM_DEFAULT_DATA_OFFSET
        else:
            self._data_offset = VGM_DEFAULT_DATA_OFFSET

        # Seek to data start
        self._source.seek(self._data_offset)
        self._source.set_data_start(self._data_offset)

        return True

    def process_until_wait(self) -> int:
        """
        Process VGM commands until a wait is encountered.

        Executes chip write commands immediately and returns when a
        wait command is reached.

        Returns:
            Number of samples to wait (0 if finished)
        """
        if not self._source or self._finished:
            return 0

        while self._source.available():
            data = self._source.read(1)
            if not data:
                self._finished = True
                return 0

            cmd = data[0]

            # PSG write - VGMParser.cpp:145-155
            if cmd == VGM_CMD_PSG_WRITE:
                val = self._source.read(1)[0]
                # Apply PSG attenuation if both FM and PSG present
                # VGMParser.cpp:148-154
                if self._has_ym2612 and (val & 0x90) == 0x90:
                    atten = val & 0x0F
                    if atten <= 13:
                        atten += 2
                    val = (val & 0xF0) | atten
                self._board.write_psg(val)

            # YM2612 port 0 - VGMParser.cpp:157-165
            elif cmd == VGM_CMD_YM2612_PORT0:
                reg = self._source.read(1)[0]
                val = self._source.read(1)[0]
                if reg == YM2612_REG_DAC_DATA:
                    self._board.write_dac(val)
                else:
                    self._board.write_ym2612(0, reg, val)

            # YM2612 port 1 - VGMParser.cpp:167-175
            elif cmd == VGM_CMD_YM2612_PORT1:
                reg = self._source.read(1)[0]
                val = self._source.read(1)[0]
                self._board.write_ym2612(1, reg, val)

            # Wait N samples - VGMParser.cpp:177-182
            elif cmd == VGM_CMD_WAIT_N:
                return self._source.read_uint16()

            # Wait NTSC frame - VGMParser.cpp:184-186
            elif cmd == VGM_CMD_WAIT_NTSC:
                return VGM_WAIT_NTSC

            # Wait PAL frame - VGMParser.cpp:188-190
            elif cmd == VGM_CMD_WAIT_PAL:
                return VGM_WAIT_PAL

            # End of data - VGMParser.cpp:192-196
            elif cmd == VGM_CMD_END:
                self._finished = True
                return 0

            # Data block (PCM data) - VGMParser.cpp:198-230
            elif cmd == VGM_CMD_DATA_BLOCK:
                self._source.read(1)  # Skip 0x66 marker
                data_type = self._source.read(1)[0]
                data_size = self._source.read_uint32()
                if data_type == 0x00:  # YM2612 PCM data
                    pcm_data = self._source.read(data_size)
                    self._pcm_bank.load_data_block(pcm_data)
                else:
                    self._source.skip(data_size)

            # Short waits 0x70-0x7F - VGMParser.cpp:232-236
            elif 0x70 <= cmd <= 0x7F:
                return (cmd & 0x0F) + 1

            # DAC write + wait 0x80-0x8F - VGMParser.cpp:238-250
            elif 0x80 <= cmd <= 0x8F:
                sample = self._pcm_bank.read_byte()
                self._board.write_dac(sample)
                wait = cmd & 0x0F
                if wait > 0:
                    return wait

            # PCM seek - VGMParser.cpp:252-260
            elif cmd == VGM_CMD_PCM_SEEK:
                offset = self._source.read_uint32()
                self._pcm_bank.seek(offset)

            # Unknown commands - skip based on known patterns
            else:
                # Handle other chip writes by skipping appropriate bytes
                if 0x30 <= cmd <= 0x3F:
                    self._source.skip(1)  # 1-byte data
                elif 0x40 <= cmd <= 0x4E:
                    self._source.skip(2)  # 2-byte data
                elif cmd == 0x4F:
                    self._source.skip(1)  # Game Gear stereo
                elif 0x51 <= cmd <= 0x5F:
                    self._source.skip(2)  # Other chips (2-byte)
                elif 0xA0 <= cmd <= 0xBF:
                    self._source.skip(2)  # Other chips (2-byte)
                elif 0xC0 <= cmd <= 0xDF:
                    self._source.skip(3)  # Other chips (3-byte)
                elif 0xE1 <= cmd <= 0xFF:
                    self._source.skip(4)  # Other chips (4-byte)
                # else: Unknown, skip nothing

        self._finished = True
        return 0

    def seek_to_loop(self) -> bool:
        """
        Seek to the loop point.

        Returns:
            True if loop point exists and seek succeeded
        """
        if not self._source or not self.has_loop:
            return False

        # Calculate loop offset relative to data start
        loop_rel = self._loop_offset - self._data_offset
        if self._source.seek(loop_rel):
            self._finished = False
            self._loop_count += 1
            return True
        return False

    @property
    def is_finished(self) -> bool:
        """Check if end of VGM data reached."""
        return self._finished

    @property
    def has_loop(self) -> bool:
        """Check if VGM has a loop point."""
        return self._loop_offset > 0 and self._loop_samples > 0

    @property
    def loop_count(self) -> int:
        """Get number of times loop has occurred."""
        return self._loop_count

    @property
    def total_samples(self) -> int:
        """Get total sample count from header."""
        return self._total_samples

    @property
    def loop_samples(self) -> int:
        """Get loop length in samples."""
        return self._loop_samples

    @property
    def version(self) -> int:
        """Get VGM version (BCD format)."""
        return self._version

    @property
    def has_ym2612(self) -> bool:
        """Check if VGM uses YM2612 (FM)."""
        return self._has_ym2612

    @property
    def has_sn76489(self) -> bool:
        """Check if VGM uses SN76489 (PSG)."""
        return self._has_sn76489

    @property
    def pcm_bank(self) -> PCMDataBank:
        """Get the PCM data bank."""
        return self._pcm_bank
