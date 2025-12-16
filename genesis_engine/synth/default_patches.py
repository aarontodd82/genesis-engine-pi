"""
Default FM patches - classic Genesis-style sounds for immediate use.
"""

from .fm_operator import FMOperator
from .fm_patch import FMPatch, FMPanMode


def _op(mul, dt, tl, rs, ar, dr, sr, rr, sl, ssg=0) -> FMOperator:
    """Helper to create operator with positional args."""
    return FMOperator(mul=mul, dt=dt, tl=tl, rs=rs, ar=ar, dr=dr, sr=sr, rr=rr, sl=sl, ssg=ssg)


# Default FM Patches - Classic Genesis-style sounds
DEFAULT_FM_PATCHES = [
    # Patch 0: Bright EP (Electric Piano)
    # Algorithm 5, good for keys
    FMPatch(
        algorithm=5,
        feedback=6,
        operators=[
            # S1 (modulator)
            _op(mul=1, dt=3, tl=35, rs=1, ar=31, dr=12, sr=0, rr=6, sl=2),
            # S3 (carrier)
            _op(mul=1, dt=3, tl=25, rs=1, ar=31, dr=8, sr=2, rr=7, sl=2),
            # S2 (carrier)
            _op(mul=2, dt=3, tl=28, rs=1, ar=31, dr=10, sr=2, rr=7, sl=3),
            # S4 (carrier)
            _op(mul=1, dt=3, tl=20, rs=1, ar=31, dr=10, sr=2, rr=8, sl=2),
        ],
        pan=FMPanMode.CENTER,
        ams=0,
        pms=0,
    ),

    # Patch 1: Synth Bass
    # Algorithm 0, punchy bass
    FMPatch(
        algorithm=0,
        feedback=5,
        operators=[
            _op(mul=0, dt=3, tl=25, rs=0, ar=31, dr=8, sr=0, rr=5, sl=1),
            _op(mul=1, dt=3, tl=30, rs=0, ar=31, dr=10, sr=0, rr=5, sl=2),
            _op(mul=0, dt=3, tl=20, rs=0, ar=31, dr=6, sr=0, rr=5, sl=1),
            _op(mul=1, dt=3, tl=15, rs=0, ar=31, dr=12, sr=2, rr=7, sl=3),
        ],
        pan=FMPanMode.CENTER,
        ams=0,
        pms=0,
    ),

    # Patch 2: Brass
    # Algorithm 4, warm brass
    FMPatch(
        algorithm=4,
        feedback=4,
        operators=[
            _op(mul=1, dt=3, tl=40, rs=1, ar=25, dr=5, sr=0, rr=4, sl=1),
            _op(mul=1, dt=3, tl=20, rs=1, ar=28, dr=6, sr=1, rr=5, sl=2),
            _op(mul=2, dt=4, tl=35, rs=1, ar=25, dr=5, sr=0, rr=4, sl=1),
            _op(mul=1, dt=2, tl=18, rs=1, ar=28, dr=6, sr=1, rr=5, sl=2),
        ],
        pan=FMPanMode.CENTER,
        ams=0,
        pms=0,
    ),

    # Patch 3: Lead Synth
    # Algorithm 7, all carriers for thick sound
    FMPatch(
        algorithm=7,
        feedback=0,
        operators=[
            _op(mul=1, dt=3, tl=28, rs=2, ar=31, dr=8, sr=0, rr=6, sl=2),
            _op(mul=2, dt=4, tl=30, rs=2, ar=31, dr=10, sr=0, rr=6, sl=3),
            _op(mul=4, dt=2, tl=35, rs=2, ar=31, dr=12, sr=0, rr=6, sl=4),
            _op(mul=1, dt=3, tl=25, rs=2, ar=31, dr=8, sr=0, rr=6, sl=2),
        ],
        pan=FMPanMode.CENTER,
        ams=0,
        pms=3,  # Slight vibrato susceptibility
    ),

    # Patch 4: Organ
    # Algorithm 7, sine-like with different harmonics
    FMPatch(
        algorithm=7,
        feedback=0,
        operators=[
            _op(mul=1, dt=3, tl=25, rs=0, ar=31, dr=0, sr=0, rr=8, sl=0),
            _op(mul=2, dt=3, tl=30, rs=0, ar=31, dr=0, sr=0, rr=8, sl=0),
            _op(mul=4, dt=3, tl=35, rs=0, ar=31, dr=0, sr=0, rr=8, sl=0),
            _op(mul=8, dt=3, tl=40, rs=0, ar=31, dr=0, sr=0, rr=8, sl=0),
        ],
        pan=FMPanMode.CENTER,
        ams=0,
        pms=2,  # Slight vibrato for organ effect
    ),

    # Patch 5: Strings
    # Algorithm 2, slow attack pad
    FMPatch(
        algorithm=2,
        feedback=3,
        operators=[
            _op(mul=1, dt=3, tl=35, rs=0, ar=18, dr=4, sr=0, rr=4, sl=1),
            _op(mul=2, dt=4, tl=40, rs=0, ar=20, dr=5, sr=0, rr=4, sl=2),
            _op(mul=3, dt=2, tl=45, rs=0, ar=22, dr=6, sr=0, rr=4, sl=2),
            _op(mul=1, dt=3, tl=22, rs=0, ar=16, dr=6, sr=1, rr=5, sl=2),
        ],
        pan=FMPanMode.CENTER,
        ams=0,
        pms=4,  # Nice vibrato for strings
    ),

    # Patch 6: Pluck/Guitar
    # Algorithm 0, quick decay
    FMPatch(
        algorithm=0,
        feedback=6,
        operators=[
            _op(mul=1, dt=3, tl=28, rs=2, ar=31, dr=15, sr=5, rr=8, sl=5),
            _op(mul=3, dt=3, tl=35, rs=2, ar=31, dr=18, sr=6, rr=8, sl=6),
            _op(mul=1, dt=4, tl=30, rs=2, ar=31, dr=16, sr=5, rr=8, sl=5),
            _op(mul=1, dt=3, tl=18, rs=2, ar=31, dr=14, sr=4, rr=9, sl=4),
        ],
        pan=FMPanMode.CENTER,
        ams=0,
        pms=0,
    ),

    # Patch 7: Bell/Chime
    # Algorithm 4, metallic harmonics
    FMPatch(
        algorithm=4,
        feedback=3,
        operators=[
            _op(mul=1, dt=3, tl=30, rs=2, ar=31, dr=6, sr=2, rr=5, sl=3),
            _op(mul=1, dt=3, tl=22, rs=2, ar=31, dr=8, sr=2, rr=6, sl=3),
            _op(mul=7, dt=6, tl=45, rs=2, ar=31, dr=10, sr=3, rr=6, sl=5),
            _op(mul=3, dt=0, tl=25, rs=2, ar=31, dr=9, sr=2, rr=7, sl=4),
        ],
        pan=FMPanMode.CENTER,
        ams=1,
        pms=2,  # Subtle tremolo for bell shimmer
    ),
]
