"""
VGM format constants and command definitions.

VGM specification: https://vgmrips.net/wiki/VGM_Specification
"""

# =============================================================================
# VGM File Format
# =============================================================================

# Magic number "Vgm " in little-endian
VGM_MAGIC = 0x206D6756

# Playback sample rate
VGM_SAMPLE_RATE = 44100

# Microseconds per sample (1000000 / 44100 = 22.6757...)
VGM_USEC_PER_SAMPLE = 22.6757

# =============================================================================
# VGM Header Offsets (all values are little-endian)
# =============================================================================

VGM_HEADER_EOF_OFFSET = 0x04      # End of file offset (relative)
VGM_HEADER_VERSION = 0x08         # Version (BCD format, e.g., 0x00000171 = v1.71)
VGM_HEADER_SN76489_CLOCK = 0x0C   # SN76489 clock (0 = not used)
VGM_HEADER_YM2413_CLOCK = 0x10    # YM2413 clock (0 = not used)
VGM_HEADER_GD3_OFFSET = 0x14      # GD3 tag offset (relative)
VGM_HEADER_TOTAL_SAMPLES = 0x18   # Total samples
VGM_HEADER_LOOP_OFFSET = 0x1C     # Loop offset (relative to 0x1C)
VGM_HEADER_LOOP_SAMPLES = 0x20    # Loop length in samples
VGM_HEADER_RATE = 0x24            # Rate (v1.01+)
VGM_HEADER_YM2612_CLOCK = 0x2C    # YM2612 clock (v1.10+, 0 = not used)
VGM_HEADER_DATA_OFFSET = 0x34     # VGM data offset (v1.50+, relative to 0x34)

# Default data offset for older VGM versions
VGM_DEFAULT_DATA_OFFSET = 0x40

# =============================================================================
# VGM Commands
# =============================================================================

# Chip write commands
VGM_CMD_PSG_WRITE = 0x50          # SN76489 write: 0x50 dd
VGM_CMD_YM2612_PORT0 = 0x52       # YM2612 port 0: 0x52 aa dd
VGM_CMD_YM2612_PORT1 = 0x53       # YM2612 port 1: 0x53 aa dd

# Wait commands
VGM_CMD_WAIT_N = 0x61             # Wait N samples: 0x61 nn nn (16-bit LE)
VGM_CMD_WAIT_NTSC = 0x62          # Wait 735 samples (1/60 sec NTSC frame)
VGM_CMD_WAIT_PAL = 0x63           # Wait 882 samples (1/50 sec PAL frame)

# End of data
VGM_CMD_END = 0x66                # End of VGM data

# Data block
VGM_CMD_DATA_BLOCK = 0x67         # Data block: 0x67 0x66 tt ss ss ss ss [data]

# Short waits: 0x70-0x7F = wait (n+1) samples where n = cmd & 0x0F
VGM_CMD_WAIT_SHORT_BASE = 0x70

# DAC write + wait: 0x80-0x8F = write DAC and wait n samples where n = cmd & 0x0F
VGM_CMD_DAC_WAIT_BASE = 0x80

# PCM seek
VGM_CMD_PCM_SEEK = 0xE0           # Seek in PCM data: 0xE0 oo oo oo oo (32-bit LE)

# =============================================================================
# Wait Sample Counts
# =============================================================================

VGM_WAIT_NTSC = 735               # Samples per NTSC frame (1/60 sec)
VGM_WAIT_PAL = 882                # Samples per PAL frame (1/50 sec)

# =============================================================================
# Chip Clock Frequencies
# =============================================================================

# YM2612 FM chip
YM2612_CLOCK_NTSC = 7670453       # NTSC Genesis (53.693175 MHz / 7)
YM2612_CLOCK_PAL = 7600489        # PAL Mega Drive (53.203424 MHz / 7)

# SN76489 PSG chip
SN76489_CLOCK_NTSC = 3579545      # NTSC (same as NTSC colorburst)
SN76489_CLOCK_PAL = 3546895       # PAL

# =============================================================================
# YM2612 Registers
# =============================================================================

YM2612_REG_KEY_ON = 0x28          # Key on/off register
YM2612_REG_DAC_DATA = 0x2A        # DAC data register
YM2612_REG_DAC_ENABLE = 0x2B      # DAC enable (bit 7)
