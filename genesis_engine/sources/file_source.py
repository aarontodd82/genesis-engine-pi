"""
FileSource - Read VGM data from local files.
"""

from pathlib import Path
from typing import BinaryIO, Optional

from .base import VGMSource


class FileSource(VGMSource):
    """Read VGM data from a local file."""

    def __init__(self, path: str):
        """
        Initialize with a file path.

        Args:
            path: Path to VGM/VGZ file
        """
        self._path = Path(path)
        self._file: Optional[BinaryIO] = None
        self._data_start: int = 0  # Offset where VGM data begins

    def open(self) -> bool:
        """
        Open the file for reading.

        Returns:
            True if file opened successfully
        """
        try:
            self._file = open(self._path, "rb")
            return True
        except (OSError, IOError):
            return False

    def close(self) -> None:
        """Close the file."""
        if self._file:
            self._file.close()
            self._file = None

    @property
    def is_open(self) -> bool:
        """Check if file is open."""
        return self._file is not None

    def read(self, count: int = 1) -> bytes:
        """
        Read bytes from the file.

        Args:
            count: Number of bytes to read

        Returns:
            Bytes read
        """
        if not self._file:
            return b""
        return self._file.read(count)

    def peek(self) -> int:
        """
        Peek at the next byte without advancing position.

        Returns:
            Next byte value, or -1 if at EOF
        """
        if not self._file:
            return -1
        pos = self._file.tell()
        data = self._file.read(1)
        self._file.seek(pos)
        return data[0] if data else -1

    def available(self) -> bool:
        """
        Check if more data is available.

        Returns:
            True if not at EOF
        """
        if not self._file:
            return False
        pos = self._file.tell()
        self._file.seek(0, 2)  # Seek to end
        end = self._file.tell()
        self._file.seek(pos)  # Restore position
        return pos < end

    def seek(self, position: int) -> bool:
        """
        Seek to a position relative to data start.

        Args:
            position: Byte offset from data start

        Returns:
            True if seek succeeded
        """
        if not self._file:
            return False
        try:
            self._file.seek(self._data_start + position)
            return True
        except (OSError, IOError):
            return False

    @property
    def position(self) -> int:
        """Current read position relative to data start."""
        if not self._file:
            return 0
        return self._file.tell() - self._data_start

    @property
    def size(self) -> int:
        """Total file size."""
        if not self._file:
            return 0
        pos = self._file.tell()
        self._file.seek(0, 2)
        total = self._file.tell()
        self._file.seek(pos)
        return total

    @property
    def can_seek(self) -> bool:
        """FileSource supports seeking."""
        return True

    def set_data_start(self, offset: int) -> None:
        """
        Set the offset where VGM data begins.

        After parsing the VGM header, set this so seek() operations
        are relative to the data section.

        Args:
            offset: Byte offset of data section start
        """
        self._data_start = offset

    def is_vgz(self) -> bool:
        """
        Check if file is VGZ (gzip compressed).

        Checks for gzip magic bytes (0x1F 0x8B) at file start.

        Returns:
            True if file appears to be VGZ
        """
        if not self._file:
            return False
        pos = self._file.tell()
        self._file.seek(0)
        magic = self._file.read(2)
        self._file.seek(pos)
        return magic == b"\x1f\x8b"

    @property
    def path(self) -> Path:
        """Path to the file."""
        return self._path

    @property
    def filename(self) -> str:
        """Filename without path."""
        return self._path.name
