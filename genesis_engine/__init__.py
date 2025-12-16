"""
GenesisEngine-Pi - Raspberry Pi driver for GenesisEngine sound boards.

Basic usage:
    from genesis_engine import GenesisEngine, GenesisBoard

    board = GenesisBoard()
    player = GenesisEngine(board)

    board.begin()
    player.play("/path/to/music.vgm")
    player.looping = True

    while player.is_playing:
        player.update()
"""

from .board import GenesisBoard
from .engine import GenesisEngine, EngineState
from .vgm_parser import VGMParser
from .pcm_bank import PCMDataBank

__version__ = "0.1.0"
__all__ = [
    "GenesisBoard",
    "GenesisEngine",
    "EngineState",
    "VGMParser",
    "PCMDataBank",
]
