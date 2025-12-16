#!/usr/bin/env python3
"""
Jukebox - Play VGM files with interactive menu.

Plays VGM/VGZ files from a directory and provides an
interactive command interface for playback control.

Usage:
    python jukebox.py [music_directory]

Commands:
    list              List VGM files
    play <n>          Play file by number
    play <filename>   Play file by name
    stop              Stop playback
    pause             Pause/resume playback
    next              Next track
    prev              Previous track
    loop              Toggle loop mode
    info              Show current track info
    help              Show command list
    quit              Exit
"""

import sys
import time
import threading
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from genesis_engine import GenesisEngine, GenesisBoard, EngineState


class Jukebox:
    """Interactive VGM file player."""

    def __init__(self, music_dir: str = "./music"):
        """
        Initialize jukebox.

        Args:
            music_dir: Directory containing VGM/VGZ files
        """
        self.music_dir = Path(music_dir)
        self.board = GenesisBoard()
        self.player = GenesisEngine(self.board)
        self.files: List[Path] = []
        self.current_index: int = -1
        self.running = False

    def scan_files(self) -> None:
        """Scan for VGM/VGZ files."""
        print(f"Scanning for VGM files in {self.music_dir}...")

        self.files = []
        if self.music_dir.exists():
            self.files = sorted(
                list(self.music_dir.glob("*.vgm")) +
                list(self.music_dir.glob("*.VGM")) +
                list(self.music_dir.glob("*.vgz")) +
                list(self.music_dir.glob("*.VGZ"))
            )

        print(f"Found {len(self.files)} files")

    def print_file_list(self) -> None:
        """Print list of available files."""
        print()
        if not self.files:
            print("No VGM files found")
            print(f"Place .vgm or .vgz files in {self.music_dir}")
            return

        print("Songs:")
        print("------")
        for i, f in enumerate(self.files):
            marker = " [PLAYING]" if i == self.current_index and self.player.is_playing else ""
            print(f"  {i+1:2}. {f.name}{marker}")
        print()

    def play_by_index(self, index: int) -> None:
        """Play file by index."""
        if index < 0 or index >= len(self.files):
            print(f"Invalid file number. Valid range: 1-{len(self.files)}")
            return

        self.play_file(self.files[index])
        self.current_index = index

    def play_file(self, path: Path) -> None:
        """Play a VGM file."""
        print(f"Playing: {path.name}")

        if not self.player.play(str(path)):
            print(f"ERROR: Failed to play {path.name}")
            return

        # Show file info
        duration = int(self.player.duration_seconds)
        print(f"  Duration: {duration // 60}:{duration % 60:02d}")

        if self.player.has_ym2612:
            print("  Chips: YM2612 (FM)")
        if self.player.has_sn76489:
            print("  Chips: SN76489 (PSG)")
        if self.player.has_loop:
            print("  Loop: Yes")
        print()

    def process_command(self, cmd: str) -> bool:
        """
        Process user command.

        Returns:
            False if should quit, True otherwise
        """
        cmd = cmd.strip().lower()
        parts = cmd.split(maxsplit=1)

        if not parts:
            return True

        command = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        if command in ("help", "?"):
            self.print_help()

        elif command in ("list", "ls"):
            self.print_file_list()

        elif command == "stop":
            self.player.stop()
            print("Stopped")

        elif command == "pause":
            if self.player.is_paused:
                self.player.resume()
                print("Resumed")
            elif self.player.is_playing:
                self.player.pause()
                print("Paused")
            else:
                print("Nothing playing")

        elif command == "loop":
            self.player.looping = not self.player.looping
            print(f"Loop: {'ON' if self.player.looping else 'OFF'}")

        elif command == "info":
            self.print_info()

        elif command == "next":
            if self.current_index < len(self.files) - 1:
                self.play_by_index(self.current_index + 1)
            else:
                print("Already at last file")

        elif command == "prev":
            if self.current_index > 0:
                self.play_by_index(self.current_index - 1)
            else:
                print("Already at first file")

        elif command == "rescan":
            self.scan_files()
            self.print_file_list()

        elif command == "play":
            if arg.isdigit():
                self.play_by_index(int(arg) - 1)
            elif arg:
                # Try to find file by name
                for i, f in enumerate(self.files):
                    if f.name.lower() == arg.lower():
                        self.play_by_index(i)
                        break
                else:
                    print(f"File not found: {arg}")
            else:
                print("Usage: play <number> or play <filename>")

        elif command in ("quit", "exit", "q"):
            return False

        elif command.isdigit():
            # Just a number - play that track
            self.play_by_index(int(command) - 1)

        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")

        return True

    def print_help(self) -> None:
        """Print help message."""
        print("""
Commands:
---------
  list            List VGM files
  play <n>        Play file by number
  play <name>     Play file by name
  stop            Stop playback
  pause           Pause/resume playback
  next            Next file
  prev            Previous file
  loop            Toggle loop mode
  info            Show current track info
  rescan          Rescan directory for files
  help            Show this help
  quit            Exit

Tip: Just type a number to play that file
""")

    def print_info(self) -> None:
        """Print current playback info."""
        print()
        if self.player.is_stopped or self.player.is_finished:
            print("Status: Stopped")
        elif self.player.is_paused:
            print("Status: Paused")
        elif self.player.is_playing:
            print("Status: Playing")

        if 0 <= self.current_index < len(self.files):
            print(f"File: {self.files[self.current_index].name}")

        if self.player.is_playing or self.player.is_paused:
            pos = int(self.player.position_seconds)
            dur = int(self.player.duration_seconds)
            print(f"Position: {pos // 60}:{pos % 60:02d} / {dur // 60}:{dur % 60:02d}")

        print(f"Loop: {'ON' if self.player.looping else 'OFF'}")
        print()

    def update_thread(self) -> None:
        """Background thread for player updates."""
        while self.running:
            self.player.update()
            time.sleep(0.001)  # 1ms between updates

    def run(self) -> None:
        """Main run loop."""
        print()
        print("========================================")
        print("  Genesis Engine Jukebox")
        print("========================================")
        print()

        # Initialize hardware
        try:
            self.board.begin()
            print("GenesisBoard initialized")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            print("Running in simulation mode (no hardware)")

        # Scan for files
        self.scan_files()

        print()
        print("Type 'help' for commands, 'list' to see files")
        print()

        # Start update thread
        self.running = True
        update_thread = threading.Thread(target=self.update_thread, daemon=True)
        update_thread.start()

        # Command loop
        try:
            while True:
                try:
                    cmd = input("> ")
                    if not self.process_command(cmd):
                        break
                except EOFError:
                    break
        except KeyboardInterrupt:
            print("\nInterrupted")

        # Cleanup
        self.running = False
        self.player.stop()
        self.board.cleanup()
        print("Goodbye!")


def main():
    """Entry point."""
    music_dir = sys.argv[1] if len(sys.argv) > 1 else "./music"
    jukebox = Jukebox(music_dir)
    jukebox.run()


if __name__ == "__main__":
    main()
