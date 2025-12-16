"""
VGMSource - Abstract base class for VGM data sources.
"""

from abc import ABC, abstractmethod


class VGMSource(ABC):
    """
    Abstract base class for reading VGM data.

    Provides a common interface for reading VGM data from various sources
    (files, memory, compressed archives, etc.).
    """

    @abstractmethod
    def open(self) -> bool:
        """
        Open the data source.

        Returns:
            True if successfully opened
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the data source."""
        pass

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Check if the source is currently open."""
        pass

    @abstractmethod
    def read(self, count: int = 1) -> bytes:
        """
        Read bytes from the source.

        Args:
            count: Number of bytes to read

        Returns:
            Bytes read (may be fewer than requested at EOF)
        """
        pass

    @abstractmethod
    def peek(self) -> int:
        """
        Peek at the next byte without advancing position.

        Returns:
            Next byte value, or -1 if at EOF
        """
        pass

    @abstractmethod
    def available(self) -> bool:
        """
        Check if more data is available.

        Returns:
            True if more data can be read
        """
        pass

    def seek(self, position: int) -> bool:
        """
        Seek to a position in the source.

        Args:
            position: Byte offset from start

        Returns:
            True if seek succeeded
        """
        return False

    @property
    def position(self) -> int:
        """Current read position."""
        return 0

    @property
    def size(self) -> int:
        """Total size of data."""
        return 0

    @property
    def can_seek(self) -> bool:
        """Check if seeking is supported."""
        return False

    # Utility methods (non-abstract)

    def read_uint16(self) -> int:
        """
        Read a 16-bit little-endian unsigned integer.

        Returns:
            16-bit value, or 0 if insufficient data
        """
        data = self.read(2)
        if len(data) < 2:
            return 0
        return int.from_bytes(data, "little")

    def read_uint32(self) -> int:
        """
        Read a 32-bit little-endian unsigned integer.

        Returns:
            32-bit value, or 0 if insufficient data
        """
        data = self.read(4)
        if len(data) < 4:
            return 0
        return int.from_bytes(data, "little")

    def skip(self, count: int) -> None:
        """
        Skip bytes in the source.

        Args:
            count: Number of bytes to skip
        """
        self.read(count)  # Simple implementation: just read and discard
