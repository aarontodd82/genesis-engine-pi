#!/usr/bin/env python3
"""
EmulatorBridge - Real-time audio from BlastEm emulator.

Receives real-time register writes from BlastEm and plays them on
the GenesisBoard. Supports both TCP (network) and Unix domain sockets.

Auto-discovery: Registers as 'genesis-engine.local' via mDNS/Bonjour
so BlastEm can find it automatically on the network.

Usage:
    # Start the bridge (auto-discovers hardware):
    python emulator_bridge.py

    # BlastEm will auto-connect over the network

Protocol:
    - PING (0xAA): Connection request
    - ACK (0x0F) + board_type + READY: Connection response
    - PSG write (0x50 + byte): Write to SN76489
    - YM2612 port 0 (0x52 + reg + val): Write to YM2612
    - YM2612 port 1 (0x53 + reg + val): Write to YM2612
    - End stream (0x66): Reset chips
"""

from __future__ import annotations

import argparse
import selectors
import socket
import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from genesis_engine import GenesisBoard

# Try to import zeroconf for mDNS
try:
    from zeroconf import ServiceInfo, Zeroconf
    HAS_ZEROCONF = True
except ImportError:
    HAS_ZEROCONF = False


# Protocol constants from BridgeProtocol.h
CMD_PING = 0xAA
CMD_ACK = 0x0F
CMD_PSG_WRITE = 0x50
CMD_YM2612_PORT0 = 0x52
CMD_YM2612_PORT1 = 0x53
CMD_END_STREAM = 0x66
FLOW_READY = 0x06
BOARD_TYPE_PI = 6  # Raspberry Pi board type

# Network defaults
DEFAULT_TCP_PORT = 7654
SERVICE_NAME = "GenesisEngine"
SERVICE_TYPE = "_genesis-audio._tcp.local."


def get_local_ip() -> str:
    """Get the local IP address for mDNS registration."""
    try:
        # Connect to a public address to determine local IP
        # (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class EmulatorBridge:
    """Bridge between BlastEm emulator and GenesisBoard."""

    SOCKET_PATH = "/tmp/genesis_bridge.sock"

    def __init__(self, tcp_port: int = DEFAULT_TCP_PORT, enable_unix: bool = True):
        """Initialize bridge.

        Args:
            tcp_port: TCP port to listen on (default 7654)
            enable_unix: Also listen on Unix domain socket (Linux only)
        """
        self.board = GenesisBoard()
        self.tcp_port = tcp_port
        self.enable_unix = enable_unix and (os.name != 'nt')  # Unix sockets not on Windows

        self.tcp_sock: Optional[socket.socket] = None
        self.unix_sock: Optional[socket.socket] = None
        self.selector = selectors.DefaultSelector()

        self.zeroconf: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None

        # Active client connections
        self.clients: dict[socket.socket, dict] = {}

    def start_servers(self) -> None:
        """Start TCP and Unix domain socket servers."""
        # TCP server (for network connections)
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_sock.bind(("0.0.0.0", self.tcp_port))
        self.tcp_sock.listen(5)
        self.tcp_sock.setblocking(False)
        self.selector.register(self.tcp_sock, selectors.EVENT_READ, data="tcp_accept")

        local_ip = get_local_ip()
        print(f"TCP server listening on {local_ip}:{self.tcp_port}")

        # Unix domain socket (for local connections on Linux)
        if self.enable_unix:
            if os.path.exists(self.SOCKET_PATH):
                os.unlink(self.SOCKET_PATH)

            self.unix_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.unix_sock.bind(self.SOCKET_PATH)
            self.unix_sock.listen(5)
            self.unix_sock.setblocking(False)
            self.selector.register(self.unix_sock, selectors.EVENT_READ, data="unix_accept")

            print(f"Unix socket listening on {self.SOCKET_PATH}")

    def register_mdns(self) -> None:
        """Register service with mDNS for auto-discovery."""
        if not HAS_ZEROCONF:
            print("Note: zeroconf not installed, mDNS disabled")
            print("      Install with: pip install zeroconf")
            return

        try:
            local_ip = get_local_ip()
            hostname = socket.gethostname()

            self.service_info = ServiceInfo(
                SERVICE_TYPE,
                f"{SERVICE_NAME}.{SERVICE_TYPE}",
                addresses=[socket.inet_aton(local_ip)],
                port=self.tcp_port,
                properties={
                    "version": "1.0",
                    "board": "pi",
                },
                server=f"{hostname}.local.",
            )

            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info)

            print(f"mDNS registered as: {hostname}.local")
            print(f"Service type: {SERVICE_TYPE}")

        except Exception as e:
            print(f"Warning: mDNS registration failed: {e}")
            self.zeroconf = None

    def accept_connection(self, sock: socket.socket, conn_type: str) -> None:
        """Accept a new client connection."""
        conn, addr = sock.accept()
        conn.setblocking(False)

        if conn_type == "tcp_accept":
            print(f"TCP client connected from {addr[0]}:{addr[1]}")
        else:
            print("Unix socket client connected")

        self.selector.register(conn, selectors.EVENT_READ, data="client")
        self.clients[conn] = {"connected": False, "addr": addr}

    def handle_client(self, conn: socket.socket) -> bool:
        """Handle data from a client. Returns False if client disconnected."""
        try:
            data = conn.recv(1)
            if not data:
                return False

            cmd = data[0]
            client = self.clients[conn]

            # PING - connection handshake
            if cmd == CMD_PING:
                print("Received PING, sending ACK")
                self.board.reset()
                conn.send(bytes([CMD_ACK, BOARD_TYPE_PI, FLOW_READY]))
                client["connected"] = True

            # PSG write
            elif cmd == CMD_PSG_WRITE:
                val = self._recv_byte(conn)
                if val is not None and client["connected"]:
                    self.board.write_psg(val)

            # YM2612 port 0
            elif cmd == CMD_YM2612_PORT0:
                data = self._recv_bytes(conn, 2)
                if data and client["connected"]:
                    reg, val = data[0], data[1]
                    if reg == 0x2A:  # DAC data
                        self.board.write_dac(val)
                    else:
                        self.board.write_ym2612(0, reg, val)

            # YM2612 port 1
            elif cmd == CMD_YM2612_PORT1:
                data = self._recv_bytes(conn, 2)
                if data and client["connected"]:
                    reg, val = data[0], data[1]
                    self.board.write_ym2612(1, reg, val)

            # End stream
            elif cmd == CMD_END_STREAM:
                print("Received END_STREAM, resetting")
                self.board.reset()
                conn.send(bytes([FLOW_READY]))

            # Wait commands (from VGM streaming - ignore timing)
            elif cmd == 0x61:  # Wait N samples
                self._recv_bytes(conn, 2)
            elif cmd == 0x62 or cmd == 0x63:  # Wait frame
                pass
            elif 0x70 <= cmd <= 0x7F:  # Short wait
                pass

            return True

        except (ConnectionResetError, BrokenPipeError, OSError):
            return False

    def _recv_byte(self, conn: socket.socket) -> Optional[int]:
        """Receive a single byte."""
        try:
            data = conn.recv(1)
            return data[0] if data else None
        except (BlockingIOError, OSError):
            return None

    def _recv_bytes(self, conn: socket.socket, count: int) -> Optional[bytes]:
        """Receive exactly count bytes."""
        try:
            data = b""
            while len(data) < count:
                chunk = conn.recv(count - len(data))
                if not chunk:
                    return None
                data += chunk
            return data
        except (BlockingIOError, OSError):
            return None

    def remove_client(self, conn: socket.socket) -> None:
        """Remove a disconnected client."""
        addr = self.clients.get(conn, {}).get("addr", "unknown")
        print(f"Client disconnected: {addr}")

        try:
            self.selector.unregister(conn)
        except (KeyError, ValueError):
            pass

        try:
            conn.close()
        except OSError:
            pass

        if conn in self.clients:
            del self.clients[conn]

        # Reset hardware when last client disconnects
        if not self.clients:
            self.board.reset()

    def cleanup(self) -> None:
        """Clean up resources."""
        # Close all client connections
        for conn in list(self.clients.keys()):
            self.remove_client(conn)

        # Unregister mDNS
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
            except Exception:
                pass

        # Close server sockets
        if self.tcp_sock:
            try:
                self.selector.unregister(self.tcp_sock)
                self.tcp_sock.close()
            except Exception:
                pass

        if self.unix_sock:
            try:
                self.selector.unregister(self.unix_sock)
                self.unix_sock.close()
            except Exception:
                pass
            if os.path.exists(self.SOCKET_PATH):
                os.unlink(self.SOCKET_PATH)

        self.selector.close()

        # Cleanup hardware
        self.board.mute_all()
        self.board.cleanup()

    def run(self) -> None:
        """Main run loop."""
        print("=" * 50)
        print("GenesisEngine - Emulator Bridge")
        print("=" * 50)
        print()

        # Initialize hardware
        try:
            self.board.begin()
            print("GenesisBoard initialized")
        except RuntimeError as e:
            print(f"ERROR: {e}")
            return

        print()

        # Start servers
        try:
            self.start_servers()
            self.register_mdns()

            print()
            print("Waiting for BlastEm connection...")
            print("(Press Ctrl+C to quit)")
            print()

            while True:
                # Wait for events on any socket
                events = self.selector.select(timeout=1.0)

                for key, mask in events:
                    if key.data == "tcp_accept":
                        self.accept_connection(key.fileobj, "tcp_accept")
                    elif key.data == "unix_accept":
                        self.accept_connection(key.fileobj, "unix_accept")
                    elif key.data == "client":
                        if not self.handle_client(key.fileobj):
                            self.remove_client(key.fileobj)

        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()

        print("Goodbye!")


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="GenesisEngine Emulator Bridge - Real-time audio from BlastEm"
    )
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=DEFAULT_TCP_PORT,
        help=f"TCP port to listen on (default: {DEFAULT_TCP_PORT})"
    )
    parser.add_argument(
        "--no-unix",
        action="store_true",
        help="Disable Unix domain socket (Linux only)"
    )

    args = parser.parse_args()

    bridge = EmulatorBridge(
        tcp_port=args.port,
        enable_unix=not args.no_unix
    )
    bridge.run()


if __name__ == "__main__":
    main()
