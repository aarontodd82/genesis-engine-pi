"""
GenesisEngine - High-level VGM player.
"""

import time
from enum import Enum
from pathlib import Path
from typing import Optional

from .board import GenesisBoard
from .vgm_parser import VGMParser
from .sources.file_source import FileSource
from .sources.vgz_source import VGZSource
from .sources.base import VGMSource
from .vgm_commands import VGM_SAMPLE_RATE


class EngineState(Enum):
    """Playback state machine states."""

    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    FINISHED = 3


class GenesisEngine:
    """
    High-level VGM player.

    Manages playback timing, source selection, and state.
    Call update() frequently (e.g., in a loop) to process commands.

    Example:
        board = GenesisBoard()
        player = GenesisEngine(board)

        board.begin()
        player.play("/path/to/music.vgm")
        player.looping = True

        while player.is_playing:
            player.update()
            time.sleep(0.001)
    """

    def __init__(self, board: GenesisBoard):
        """
        Initialize engine with a board reference.

        Args:
            board: GenesisBoard instance
        """
        self._board = board
        self._parser = VGMParser(board)
        self._source: Optional[VGMSource] = None

        self._state = EngineState.STOPPED
        self._looping = False

        # Timing
        self._start_time_ns: int = 0
        self._pause_time_ns: int = 0
        self._samples_played: int = 0
        self._waiting_samples: int = 0

    def play(self, path: str) -> bool:
        """
        Start playing a VGM/VGZ file.

        Args:
            path: Path to VGM or VGZ file

        Returns:
            True if playback started successfully
        """
        # Stop any current playback
        self.stop()

        # Create appropriate source
        path_obj = Path(path)
        if path_obj.suffix.lower() == ".vgz":
            self._source = VGZSource(path)
        else:
            self._source = FileSource(path)

        if not self._source.open():
            return False

        self._parser.set_source(self._source)

        if not self._parser.parse_header():
            self._source.close()
            return False

        # Start playback
        self._state = EngineState.PLAYING
        self._start_time_ns = time.perf_counter_ns()
        self._samples_played = 0
        self._waiting_samples = 0

        return True

    def play_data(self, data: bytes) -> bool:
        """
        Start playing VGM data from memory.

        Args:
            data: Raw VGM file data

        Returns:
            True if playback started successfully
        """
        # TODO: Implement memory-based source
        raise NotImplementedError("Memory playback not yet implemented")

    def stop(self) -> None:
        """Stop playback and silence chips."""
        self._board.mute_all()
        self._state = EngineState.STOPPED

        if self._source:
            self._source.close()
            self._source = None

    def pause(self) -> None:
        """Pause playback."""
        if self._state == EngineState.PLAYING:
            self._pause_time_ns = time.perf_counter_ns()
            self._state = EngineState.PAUSED

    def resume(self) -> None:
        """Resume paused playback."""
        if self._state == EngineState.PAUSED:
            # Adjust start time to account for pause duration
            pause_duration = time.perf_counter_ns() - self._pause_time_ns
            self._start_time_ns += pause_duration
            self._state = EngineState.PLAYING

    def update(self) -> None:
        """
        Process VGM commands up to current time.

        Must be called frequently (every loop iteration) for accurate timing.
        """
        if self._state != EngineState.PLAYING:
            return

        # Calculate target samples based on elapsed time
        # Formula from GenesisEngine.cpp:210-215
        elapsed_ns = time.perf_counter_ns() - self._start_time_ns
        target_samples = (elapsed_ns * 441) // 10_000_000_000

        # Process commands until caught up
        while self._samples_played < target_samples:
            # Consume waiting samples first
            if self._waiting_samples > 0:
                consume = min(self._waiting_samples, target_samples - self._samples_played)
                self._waiting_samples -= consume
                self._samples_played += consume
                continue

            # Check for end of track
            if self._parser.is_finished:
                if self._looping and self._parser.has_loop:
                    self._parser.seek_to_loop()
                else:
                    self._state = EngineState.FINISHED
                    return

            # Process next batch of commands
            self._waiting_samples = self._parser.process_until_wait()

    @property
    def state(self) -> EngineState:
        """Get current playback state."""
        return self._state

    @property
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._state == EngineState.PLAYING

    @property
    def is_paused(self) -> bool:
        """Check if paused."""
        return self._state == EngineState.PAUSED

    @property
    def is_stopped(self) -> bool:
        """Check if stopped."""
        return self._state == EngineState.STOPPED

    @property
    def is_finished(self) -> bool:
        """Check if playback finished (reached end without looping)."""
        return self._state == EngineState.FINISHED

    @property
    def looping(self) -> bool:
        """Get loop mode."""
        return self._looping

    @looping.setter
    def looping(self, value: bool) -> None:
        """Set loop mode."""
        self._looping = value

    @property
    def duration_seconds(self) -> float:
        """Get total track duration in seconds."""
        return self._parser.total_samples / VGM_SAMPLE_RATE

    @property
    def position_seconds(self) -> float:
        """Get current playback position in seconds."""
        return self._samples_played / VGM_SAMPLE_RATE

    @property
    def loop_count(self) -> int:
        """Get number of times track has looped."""
        return self._parser.loop_count

    @property
    def has_loop(self) -> bool:
        """Check if track has a loop point."""
        return self._parser.has_loop

    @property
    def has_ym2612(self) -> bool:
        """Check if track uses YM2612 (FM)."""
        return self._parser.has_ym2612

    @property
    def has_sn76489(self) -> bool:
        """Check if track uses SN76489 (PSG)."""
        return self._parser.has_sn76489
