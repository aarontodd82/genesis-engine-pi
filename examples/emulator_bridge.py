#!/usr/bin/env python3
"""
EmulatorBridge - Real-time audio from BlastEm emulator.

Receives real-time register writes from BlastEm and plays them on
the GenesisBoard. Uses a Unix domain socket for communication.

Usage:
    # Start this script first:
    python emulator_bridge.py

    # Then configure BlastEm to connect to /tmp/genesis_bridge.sock
    # (Requires BlastEm modification or a bridge script)

Protocol:
    - PING (0xAA): Connection request
    - ACK (0x0F) + board_type + READY: Connection response
    - PSG write (0x50 + byte): Write to SN76489
    - YM2612 port 0 (0x52 + reg + val): Write to YM2612
    - YM2612 port 1 (0x53 + reg + val): Write to YM2612
    - End stream (0x66): Reset chips
"""

from __future__ import annotations

import socket
import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from genesis_engine import GenesisBoard


# Protocol constants from BridgeProtocol.h
CMD_PING = 0xAA
CMD_ACK = 0x0F
CMD_PSG_WRITE = 0x50
CMD_YM2612_PORT0 = 0x52
CMD_YM2612_PORT1 = 0x53
CMD_END_STREAM = 0x66
FLOW_READY = 0x06
BOARD_TYPE_PI = 6  # New type for Raspberry Pi


class EmulatorBridge:
    """Bridge between BlastEm emulator and GenesisBoard."""

    SOCKET_PATH = "/tmp/genesis_bridge.sock"

    def __init__(self):
        """Initialize bridge."""
        self.board = GenesisBoard()
        self.sock: Optional[socket.socket] = None
        self.conn: Optional[socket.socket] = None
        self.connected = False

    def start_server(self) -> None:
        """Start the Unix domain socket server."""
        # Remove old socket file if it exists
        if os.path.exists(self.SOCKET_PATH):
            os.unlink(self.SOCKET_PATH)

        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(self.SOCKET_PATH)
        self.sock.listen(1)

        print(f"Listening on {self.SOCKET_PATH}")
        print("Waiting for BlastEm connection...")

    def wait_for_connection(self) -> None:
        """Wait for and accept a connection."""
        self.conn, _ = self.sock.accept()
        self.conn.setblocking(True)
        print("Client connected!")

    def process_commands(self) -> None:
        """Process incoming commands from the emulator."""
        while True:
            try:
                data = self.conn.recv(1)
                if not data:
                    print("Connection closed")
                    break

                cmd = data[0]

                # PING - connection handshake
                if cmd == CMD_PING:
                    print("Received PING, sending ACK")
                    self.board.reset()
                    self.conn.send(bytes([CMD_ACK, BOARD_TYPE_PI, FLOW_READY]))
                    self.connected = True

                # PSG write
                elif cmd == CMD_PSG_WRITE:
                    val = self.conn.recv(1)[0]
                    if self.connected:
                        self.board.write_psg(val)

                # YM2612 port 0
                elif cmd == CMD_YM2612_PORT0:
                    data = self.conn.recv(2)
                    reg, val = data[0], data[1]
                    if self.connected:
                        if reg == 0x2A:  # DAC data
                            self.board.write_dac(val)
                        else:
                            self.board.write_ym2612(0, reg, val)

                # YM2612 port 1
                elif cmd == CMD_YM2612_PORT1:
                    data = self.conn.recv(2)
                    reg, val = data[0], data[1]
                    if self.connected:
                        self.board.write_ym2612(1, reg, val)

                # End stream
                elif cmd == CMD_END_STREAM:
                    print("Received END_STREAM, resetting")
                    self.board.reset()
                    self.conn.send(bytes([FLOW_READY]))

                # Wait commands (from VGM streaming - optional support)
                elif cmd == 0x61:  # Wait N samples
                    self.conn.recv(2)  # Discard timing (real-time from emulator)
                elif cmd == 0x62 or cmd == 0x63:  # Wait frame
                    pass  # No data to read
                elif 0x70 <= cmd <= 0x7F:  # Short wait
                    pass  # No data to read

            except (ConnectionResetError, BrokenPipeError):
                print("Connection lost")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.conn:
            self.conn.close()
        if self.sock:
            self.sock.close()
        if os.path.exists(self.SOCKET_PATH):
            os.unlink(self.SOCKET_PATH)
        self.board.mute_all()
        self.board.cleanup()

    def run(self) -> None:
        """Main run loop."""
        print("EmulatorBridge - Real-time audio from BlastEm")
        print()

        # Initialize hardware
        try:
            self.board.begin()
            print("GenesisBoard initialized")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            return

        # Start server
        try:
            self.start_server()

            while True:
                self.wait_for_connection()
                self.connected = False

                try:
                    self.process_commands()
                except Exception as e:
                    print(f"Error in command loop: {e}")

                # Client disconnected - wait for reconnection
                if self.conn:
                    self.conn.close()
                    self.conn = None

                self.board.reset()
                print("Waiting for reconnection...")

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()

        print("Goodbye!")


def main():
    """Entry point."""
    bridge = EmulatorBridge()
    bridge.run()


if __name__ == "__main__":
    main()
