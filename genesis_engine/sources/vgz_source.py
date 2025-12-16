"""
VGZSource - Read VGZ (gzip-compressed VGM) files.

Python's gzip module handles decompression automatically.
"""

import gzip
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional

from .base import VGMSource


class VGZSource(VGMSource):
    """
    Read VGZ (gzip-compressed VGM) files.

    Decompresses to memory for full seeking support.
    """

    def __init__(self, path: str):
        """
        Initialize with a VGZ file path.

        Args:
            path: Path to VGZ file
        """
        self._path = Path(path)
        self._data: Optional[bytes] = None
        self._position: int = 0
        self._data_start: int = 0

    def open(self) -> bool:
        """
        Open and decompress the VGZ file.

        Returns:
            True if successfully opened and decompressed
        """
        try:
            with gzip.open(self._path, "rb") as f:
                self._data = f.read()
            self._position = 0
            return True
        except (OSError, IOError, gzip.BadGzipFile):
            return False

    def close(self) -> None:
        """Close and release decompressed data."""
        self._data = None
        self._position = 0

    @property
    def is_open(self) -> bool:
        """Check if file is open and decompressed."""
        return self._data is not None

    def read(self, count: int = 1) -> bytes:
        """
        Read bytes from decompressed data.

        Args:
            count: Number of bytes to read

        Returns:
            Bytes read
        """
        if self._data is None:
            return b""
        end = min(self._position + count, len(self._data))
        data = self._data[self._position:end]
        self._position = end
        return data

    def peek(self) -> int:
        """
        Peek at next byte without advancing position.

        Returns:
            Next byte value, or -1 if at EOF
        """
        if self._data is None or self._position >= len(self._data):
            return -1
        return self._data[self._position]

    def available(self) -> bool:
        """
        Check if more data is available.

        Returns:
            True if not at end of decompressed data
        """
        if self._data is None:
            return False
        return self._position < len(self._data)

    def seek(self, position: int) -> bool:
        """
        Seek to a position relative to data start.

        With full decompression into memory, seeking is trivial.

        Args:
            position: Byte offset from data start

        Returns:
            True if seek succeeded
        """
        if self._data is None:
            return False
        target = self._data_start + position
        if target < 0 or target > len(self._data):
            return False
        self._position = target
        return True

    @property
    def position(self) -> int:
        """Current read position relative to data start."""
        return self._position - self._data_start

    @property
    def size(self) -> int:
        """Total decompressed size."""
        return len(self._data) if self._data else 0

    @property
    def can_seek(self) -> bool:
        """VGZSource supports seeking (after decompression)."""
        return True

    def set_data_start(self, offset: int) -> None:
        """
        Set the offset where VGM data begins.

        Args:
            offset: Byte offset of data section start
        """
        self._data_start = offset

    @property
    def path(self) -> Path:
        """Path to the VGZ file."""
        return self._path

    @property
    def filename(self) -> str:
        """Filename without path."""
        return self._path.name
