#!/usr/bin/env python3
"""
SimpleSynth - Direct chip control demo.

Demonstrates using the synthesis utilities for direct control of the
YM2612 (FM) and SN76489 (PSG) chips without VGM playback.

Usage:
    python simple_synth.py

Commands:
    n<note>   Play FM note (e.g., "n60" for middle C)
    s         Stop FM note
    p<num>    Change FM patch (0-7)
    t<note>   Play PSG tone on channel 0
    q         Silence all
    ?         Show help
    exit      Quit
"""

import sys
from pathlib import Path

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from genesis_engine import GenesisBoard
from genesis_engine.synth import (
    FMPatch,
    write_to_channel as fm_write_to_channel,
    key_on as fm_key_on,
    key_off as fm_key_off,
    play_note as psg_play_note,
    DEFAULT_FM_PATCHES,
)


class SimpleSynth:
    """Direct chip control synthesizer."""

    def __init__(self):
        """Initialize synth."""
        self.board = GenesisBoard()
        self.current_patch_num = 0
        self.current_patch: FMPatch = DEFAULT_FM_PATCHES[0]
        self.current_fm_note = 0
        self.fm_note_on = False

    def load_patch(self, patch_num: int) -> None:
        """Load an FM patch."""
        if patch_num < 0 or patch_num >= len(DEFAULT_FM_PATCHES):
            print(f"Invalid patch number. Valid range: 0-{len(DEFAULT_FM_PATCHES)-1}")
            return

        self.current_patch = DEFAULT_FM_PATCHES[patch_num]
        self.current_patch.load_to_channel(self.board, 0)
        self.current_patch_num = patch_num
        print(f"Loaded patch {patch_num}")

    def play_fm_note(self, note: int) -> None:
        """Play a note on FM channel 0."""
        if note < 0 or note > 127:
            print("Invalid note. Valid range: 0-127")
            return

        # Stop previous note if playing
        if self.fm_note_on:
            fm_key_off(self.board, 0)

        # Set frequency and key on
        fm_write_to_channel(self.board, 0, note)
        fm_key_on(self.board, 0)

        self.current_fm_note = note
        self.fm_note_on = True
        print(f"FM note {note}")

    def stop_fm_note(self) -> None:
        """Stop the current FM note."""
        if self.fm_note_on:
            fm_key_off(self.board, 0)
            self.fm_note_on = False
            print("FM note off")

    def play_psg_note(self, note: int) -> None:
        """Play a note on PSG channel 0."""
        if note < 0 or note > 127:
            print("Invalid note. Valid range: 0-127")
            return

        # Play on PSG channel 0 at medium volume (attenuation 2)
        psg_play_note(self.board, 0, note, 2)
        print(f"PSG note {note}")

    def silence_all(self) -> None:
        """Silence all sound."""
        fm_key_off(self.board, 0)
        self.fm_note_on = False
        self.board.silence_psg()
        print("Silenced")

    def print_help(self) -> None:
        """Print help message."""
        print("""
=== SimpleSynth Help ===
n<note>  - Play FM note (0-127, 60=middle C)
s        - Stop FM note
p<num>   - Change FM patch (0-7)
t<note>  - Play PSG tone (0-127)
q        - Silence all
?        - Show this help
exit     - Quit

Patches: 0=EP, 1=Bass, 2=Brass, 3=Lead
         4=Organ, 5=Strings, 6=Pluck, 7=Bell
Current patch: """ + str(self.current_patch_num))

    def process_command(self, cmd: str) -> bool:
        """
        Process a command.

        Returns:
            False if should quit, True otherwise
        """
        cmd = cmd.strip()
        if not cmd:
            return True

        char = cmd[0].lower()
        arg = cmd[1:].strip()

        if char == 'n':
            # Play FM note
            try:
                note = int(arg)
                self.play_fm_note(note)
            except ValueError:
                print("Usage: n<note> (e.g., n60)")

        elif char == 's':
            self.stop_fm_note()

        elif char == 'p':
            # Change patch
            try:
                patch = int(arg)
                self.load_patch(patch)
            except ValueError:
                print("Usage: p<num> (e.g., p0)")

        elif char == 't':
            # Play PSG tone
            try:
                note = int(arg)
                self.play_psg_note(note)
            except ValueError:
                print("Usage: t<note> (e.g., t60)")

        elif char == 'q':
            self.silence_all()

        elif char == '?':
            self.print_help()

        elif cmd.lower() in ('exit', 'quit'):
            return False

        else:
            print(f"Unknown command: {cmd}")

        return True

    def run(self) -> None:
        """Main run loop."""
        print("SimpleSynth - GenesisEngine Direct Control Demo")
        print()

        # Initialize hardware
        try:
            self.board.begin()
            self.board.reset()
            print("GenesisBoard initialized")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            print("Running in simulation mode (no hardware)")
            return

        # Load initial patch
        self.load_patch(0)

        print("Commands: n<note> s p<num> t<note> q ?")
        print("Ready!")
        print()

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
        self.silence_all()
        self.board.cleanup()
        print("Goodbye!")


def main():
    """Entry point."""
    synth = SimpleSynth()
    synth.run()


if __name__ == "__main__":
    main()
