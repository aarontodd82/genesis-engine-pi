"""
PCMDataBank - Storage and playback of PCM/DAC samples.
"""


class PCMDataBank:
    """Storage for PCM sample data used by YM2612 DAC."""

    # Silence value for DAC (center point of 8-bit unsigned)
    SILENCE = 0x80

    def __init__(self):
        """Initialize empty PCM data bank."""
        self._data: bytearray = bytearray()
        self._position: int = 0

    def load_data_block(self, data: bytes) -> bool:
        """
        Load PCM data from a VGM data block.

        Args:
            data: Raw PCM sample data

        Returns:
            True (always succeeds on Pi)
        """
        self._data = bytearray(data)
        self._position = 0
        return True

    def read_byte(self) -> int:
        """
        Read the next PCM sample byte.

        Returns:
            Sample value (0x00-0xFF), or 0x80 (silence) if no data
        """
        if not self._data or self._position >= len(self._data):
            return self.SILENCE

        val = self._data[self._position]
        self._position += 1
        return val

    def seek(self, position: int) -> None:
        """
        Seek to a position in the PCM data.

        Args:
            position: Byte offset into PCM data
        """
        self._position = min(position, len(self._data))

    def clear(self) -> None:
        """Clear all PCM data."""
        self._data = bytearray()
        self._position = 0

    @property
    def has_data(self) -> bool:
        """Check if PCM data is loaded."""
        return len(self._data) > 0

    @property
    def position(self) -> int:
        """Current read position in PCM data."""
        return self._position

    @property
    def size(self) -> int:
        """Total size of loaded PCM data."""
        return len(self._data)
