#!/usr/bin/env python3
"""
Jukebox - Play VGM files with interactive menu and playlist support.

Plays VGM/VGZ files from a directory and provides an
interactive command interface for playback control.

Usage:
    python jukebox.py [music_directory]

Commands:
    list              List VGM files and playlists
    play <n>          Play file or playlist by number
    play <filename>   Play file by name
    playlist <name>   Load and start playlist (<name>.txt)
    stop              Stop playback
    pause             Pause/resume playback
    next              Next track
    prev              Previous track
    loop              Toggle loop mode
    info              Show current track info
    help              Show command list
    quit              Exit

Playlist Format:
    Create a .txt file starting with #PLAYLIST:

    #PLAYLIST
    :shuffle
    :loop
    song1.vgm,2
    song2.vgm
    song3.vgz,3

    - :shuffle - randomize track order
    - :loop - restart playlist when finished
    - filename,N - play track N times (uses loop points)
"""

import sys
import time
import random
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from genesis_engine import GenesisEngine, GenesisBoard, EngineState


@dataclass
class PlaylistEntry:
    """A single track in a playlist."""
    file_index: int  # Index into files list
    plays: int       # How many times to play this track


class Jukebox:
    """Interactive VGM file player with playlist support."""

    # Delay between songs in playlist (seconds)
    PLAYLIST_SONG_DELAY = 0.75

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
        self.playlists: List[Path] = []
        self.current_index: int = -1
        self.running = False

        # Playlist state
        self.playlist_active = False
        self.playlist_entries: List[PlaylistEntry] = []
        self.playlist_pos: int = 0
        self.playlist_shuffle = False
        self.playlist_loop = False
        self.current_plays: int = 0
        self.last_loop_count: int = 0

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

    def scan_playlists(self) -> None:
        """Scan for playlist files."""
        print("Scanning for playlists...", end=" ")

        self.playlists = []
        if not self.music_dir.exists():
            print("0 found")
            return

        for txt_file in self.music_dir.glob("*.txt"):
            try:
                with open(txt_file, 'r') as f:
                    first_line = f.readline().strip()
                    if first_line == "#PLAYLIST":
                        self.playlists.append(txt_file)
            except Exception:
                pass

        self.playlists.sort()
        print(f"{len(self.playlists)} found")

    def find_file_index(self, name: str) -> int:
        """Find a file index by name (case-insensitive)."""
        name_lower = name.lower()
        for i, f in enumerate(self.files):
            if f.name.lower() == name_lower:
                return i
        return -1

    def load_playlist(self, name: str) -> bool:
        """
        Load a playlist file.

        Args:
            name: Playlist name (without .txt extension)

        Returns:
            True if loaded successfully
        """
        # Build path
        playlist_path = self.music_dir / f"{name}.txt"
        if not playlist_path.exists():
            print(f"ERROR: Playlist not found: {name}")
            return False

        # Reset playlist state
        self.playlist_entries = []
        self.playlist_pos = 0
        self.playlist_shuffle = False
        self.playlist_loop = False
        self.playlist_active = False
        self.current_plays = 0
        self.last_loop_count = 0

        print(f"Loading playlist: {name}")

        try:
            with open(playlist_path, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"ERROR: Failed to read playlist: {e}")
            return False

        # Check header
        if not lines or lines[0].strip() != "#PLAYLIST":
            print("ERROR: Not a playlist (missing #PLAYLIST header)")
            return False

        # Parse lines
        for line in lines[1:]:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Handle directives
            if line.startswith(':'):
                directive = line[1:].lower()
                if directive == "shuffle":
                    self.playlist_shuffle = True
                    print("  Shuffle: ON")
                elif directive == "loop":
                    self.playlist_loop = True
                    print("  Loop: ON")
                continue

            # Parse track line: filename or filename,plays
            parts = line.split(',', 1)
            filename = parts[0].strip()
            plays = 1
            if len(parts) > 1:
                try:
                    plays = int(parts[1].strip())
                    if plays < 1:
                        plays = 1
                except ValueError:
                    plays = 1

            # Find file in our file list
            file_idx = self.find_file_index(filename)
            if file_idx < 0:
                print(f"  Warning: file not found: {filename}")
                continue

            self.playlist_entries.append(PlaylistEntry(file_idx, plays))

        if not self.playlist_entries:
            print("ERROR: Playlist has no valid tracks")
            return False

        print(f"  Loaded {len(self.playlist_entries)} tracks")

        # Shuffle if requested
        if self.playlist_shuffle:
            random.shuffle(self.playlist_entries)

        return True

    def start_playlist(self) -> None:
        """Start playing the loaded playlist."""
        if not self.playlist_entries:
            return

        self.playlist_active = True
        self.playlist_pos = 0
        self.current_plays = 0
        self.last_loop_count = 0

        # Start first track
        entry = self.playlist_entries[0]
        self.play_by_index(entry.file_index)

        # Enable looping if we need to play more than once
        if entry.plays > 1 and self.player.has_loop:
            self.player.looping = True

        self._print_playlist_status()

    def play_next_in_playlist(self) -> None:
        """Advance to the next track in the playlist."""
        if not self.playlist_active or not self.playlist_entries:
            return

        entry = self.playlist_entries[self.playlist_pos]
        self.current_plays += 1

        # Check if we need to play this track again
        if self.current_plays < entry.plays:
            # Track will loop automatically (looping is already enabled)
            self._print_playlist_status()
            return

        # Move to next track
        self.playlist_pos += 1
        self.current_plays = 0
        self.last_loop_count = 0

        # Check if playlist is complete
        if self.playlist_pos >= len(self.playlist_entries):
            if self.playlist_loop:
                # Restart playlist
                self.playlist_pos = 0
                print("[Playlist: restarting]")
            else:
                # Playlist finished
                self.playlist_active = False
                print("[Playlist: finished]")
                return

        # Brief pause between songs
        time.sleep(self.PLAYLIST_SONG_DELAY)

        # Play next track
        entry = self.playlist_entries[self.playlist_pos]
        self.play_by_index(entry.file_index)

        # Enable looping if we need to play more than once
        if entry.plays > 1 and self.player.has_loop:
            self.player.looping = True

        self._print_playlist_status()

    def _print_playlist_status(self) -> None:
        """Print current playlist position."""
        if not self.playlist_active:
            return

        entry = self.playlist_entries[self.playlist_pos]
        status = f"[Playlist: track {self.playlist_pos + 1}/{len(self.playlist_entries)}"
        if entry.plays > 1:
            status += f", play {self.current_plays + 1}/{entry.plays}"
        status += "]"
        print(status)

    def print_file_list(self) -> None:
        """Print list of available files and playlists."""
        print()
        if not self.files:
            print("No VGM files found")
            print(f"Place .vgm or .vgz files in {self.music_dir}")
            return

        print("Songs:")
        print("------")
        for i, f in enumerate(self.files):
            marker = ""
            if i == self.current_index and self.player.is_playing:
                marker = " [PLAYING]"
            print(f"  {i+1:2}. {f.name}{marker}")

        # Show playlists (numbered after songs)
        if self.playlists:
            print()
            print("Playlists:")
            print("----------")
            for i, p in enumerate(self.playlists):
                num = len(self.files) + i + 1
                print(f"  {num:2}. {p.stem}")

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
        cmd = cmd.strip()
        parts = cmd.lower().split(maxsplit=1)

        if not parts:
            return True

        command = parts[0]
        arg = parts[1] if len(parts) > 1 else ""
        # Get original case arg for filenames
        orig_parts = cmd.split(maxsplit=1)
        orig_arg = orig_parts[1] if len(orig_parts) > 1 else ""

        if command in ("help", "?"):
            self.print_help()

        elif command in ("list", "ls"):
            self.print_file_list()

        elif command == "stop":
            self.player.stop()
            self.playlist_active = False  # Stop also exits playlist mode
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
            if self.playlist_active:
                # In playlist mode: advance to next track
                self.player.stop()
                self.playlist_pos += 1
                self.current_plays = 0
                self.last_loop_count = 0
                if self.playlist_pos >= len(self.playlist_entries):
                    if self.playlist_loop:
                        self.playlist_pos = 0
                    else:
                        self.playlist_active = False
                        print("[Playlist: finished]")
                        return True
                time.sleep(self.PLAYLIST_SONG_DELAY)
                entry = self.playlist_entries[self.playlist_pos]
                self.play_by_index(entry.file_index)
                if entry.plays > 1 and self.player.has_loop:
                    self.player.looping = True
                self._print_playlist_status()
            elif self.current_index < len(self.files) - 1:
                self.play_by_index(self.current_index + 1)
            else:
                print("Already at last file")

        elif command == "prev":
            if self.playlist_active:
                # In playlist mode: go to previous track
                self.player.stop()
                if self.playlist_pos > 0:
                    self.playlist_pos -= 1
                elif self.playlist_loop:
                    self.playlist_pos = len(self.playlist_entries) - 1
                else:
                    print("Already at first track")
                    return True
                self.current_plays = 0
                self.last_loop_count = 0
                time.sleep(self.PLAYLIST_SONG_DELAY)
                entry = self.playlist_entries[self.playlist_pos]
                self.play_by_index(entry.file_index)
                if entry.plays > 1 and self.player.has_loop:
                    self.player.looping = True
                self._print_playlist_status()
            elif self.current_index > 0:
                self.play_by_index(self.current_index - 1)
            else:
                print("Already at first file")

        elif command == "rescan":
            self.scan_files()
            self.scan_playlists()
            self.print_file_list()

        elif command == "playlist":
            if orig_arg:
                if self.load_playlist(orig_arg):
                    self.start_playlist()
            else:
                print("Usage: playlist <name> (loads <name>.txt)")

        elif command == "play":
            if arg.isdigit():
                num = int(arg)
                if 1 <= num <= len(self.files):
                    self.playlist_active = False  # Exit playlist mode
                    self.play_by_index(num - 1)
                elif num > len(self.files) and num <= len(self.files) + len(self.playlists):
                    # It's a playlist number
                    plist_idx = num - len(self.files) - 1
                    if self.load_playlist(self.playlists[plist_idx].stem):
                        self.start_playlist()
                else:
                    print(f"Invalid number. Valid range: 1-{len(self.files) + len(self.playlists)}")
            elif orig_arg:
                # Try to find file by name
                file_idx = self.find_file_index(orig_arg)
                if file_idx >= 0:
                    self.playlist_active = False  # Exit playlist mode
                    self.play_by_index(file_idx)
                else:
                    print(f"File not found: {orig_arg}")
            else:
                print("Usage: play <number> or play <filename>")

        elif command in ("quit", "exit", "q"):
            return False

        elif command.isdigit():
            # Just a number - play that file or playlist
            num = int(command)
            if 1 <= num <= len(self.files):
                self.playlist_active = False  # Exit playlist mode
                self.play_by_index(num - 1)
            elif num > len(self.files) and num <= len(self.files) + len(self.playlists):
                # It's a playlist number
                plist_idx = num - len(self.files) - 1
                if self.load_playlist(self.playlists[plist_idx].stem):
                    self.start_playlist()
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' for available commands")

        else:
            print(f"Unknown command: {command}")
            print("Type 'help' for available commands")

        return True

    def print_help(self) -> None:
        """Print help message."""
        print("""
Commands:
---------
  list            List VGM files and playlists
  play <n>        Play file or playlist by number
  play <name>     Play file by name
  playlist <name> Load and start playlist (<name>.txt)
  stop            Stop playback
  pause           Pause/resume playback
  next            Next file (or track in playlist)
  prev            Previous file (or track in playlist)
  loop            Toggle loop mode
  info            Show current track info
  rescan          Rescan directory for files
  help            Show this help
  quit            Exit

Tip: Just type a number to play that file or playlist
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

        if self.playlist_active:
            entry = self.playlist_entries[self.playlist_pos]
            status = f"Playlist: track {self.playlist_pos + 1}/{len(self.playlist_entries)}"
            if entry.plays > 1:
                status += f", play {self.current_plays + 1}/{entry.plays}"
            if self.playlist_shuffle:
                status += " [shuffle]"
            if self.playlist_loop:
                status += " [loop]"
            print(status)
        else:
            print(f"Loop: {'ON' if self.player.looping else 'OFF'}")
        print()

    def update_thread(self) -> None:
        """Background thread for player updates and playlist monitoring."""
        was_playing = False

        while self.running:
            self.player.update()

            # Monitor for loop events in playlist mode (for multi-play tracks)
            if self.playlist_active and self.player.is_playing:
                loop_count = self.player.loop_count
                if loop_count > self.last_loop_count:
                    self.last_loop_count = loop_count
                    # A loop occurred - this counts as completing a play
                    entry = self.playlist_entries[self.playlist_pos]
                    self.current_plays += 1
                    if self.current_plays >= entry.plays:
                        # Done with this track, advance to next
                        self.player.stop()
                        self.play_next_in_playlist()
                    else:
                        # Still more plays needed
                        self._print_playlist_status()

            # Handle playback finished
            if was_playing and self.player.is_finished:
                if self.playlist_active:
                    self.play_next_in_playlist()
                else:
                    print("Playback finished")
                    print("> ", end="", flush=True)
                was_playing = False
            elif self.player.is_playing:
                was_playing = True

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

        # Scan for files and playlists
        self.scan_files()
        self.scan_playlists()

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
