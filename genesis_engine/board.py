"""
GenesisBoard - Low-level hardware driver for YM2612 and SN76489 chips.

Uses SPI for the shift register and GPIO for control signals.
"""

import time
from typing import Optional

# These imports will fail on non-Pi systems - handle gracefully for development
try:
    import spidev
    import RPi.GPIO as GPIO
    _HAS_HARDWARE = True
except ImportError:
    _HAS_HARDWARE = False
    spidev = None  # type: ignore
    GPIO = None  # type: ignore


class GenesisBoard:
    """
    Hardware driver for GenesisEngine sound board.

    Controls YM2612 (FM) and SN76489 (PSG) chips via shift register.

    Default GPIO pins (BCM numbering):
        WR_P (PSG write):    17 (physical pin 11)
        WR_Y (YM2612 write): 27 (physical pin 13)
        IC_Y (YM2612 reset): 22 (physical pin 15)
        A0_Y (addr/data):    23 (physical pin 16)
        A1_Y (port select):  24 (physical pin 18)
        SPI0_MOSI:           10 (physical pin 19)
        SPI0_SCLK:           11 (physical pin 23)
    """

    # Timing delays (microseconds) - from GenesisBoard.cpp:20-25
    YM_BUSY_US = 5   # Wait after YM2612 write
    PSG_BUSY_US = 9  # Wait after PSG write

    def __init__(
        self,
        wr_p: int = 17,
        wr_y: int = 27,
        ic_y: int = 22,
        a0_y: int = 23,
        a1_y: int = 24,
        spi_bus: int = 0,
        spi_device: int = 0,
    ):
        """
        Initialize the board with GPIO pin assignments.

        Args:
            wr_p: GPIO pin for PSG write strobe (active low)
            wr_y: GPIO pin for YM2612 write strobe (active low)
            ic_y: GPIO pin for YM2612 reset (active low)
            a0_y: GPIO pin for YM2612 address/data select
            a1_y: GPIO pin for YM2612 port select
            spi_bus: SPI bus number (0 or 1)
            spi_device: SPI device/chip select (0 or 1)
        """
        self._wr_p = wr_p
        self._wr_y = wr_y
        self._ic_y = ic_y
        self._a0_y = a0_y
        self._a1_y = a1_y
        self._spi_bus = spi_bus
        self._spi_device = spi_device

        self._spi: Optional[spidev.SpiDev] = None
        self._initialized = False
        self._in_dac_stream = False

    def begin(self) -> None:
        """
        Initialize GPIO and SPI hardware.

        Must be called before any other methods.
        """
        if not _HAS_HARDWARE:
            raise RuntimeError("RPi.GPIO and spidev not available - not running on Raspberry Pi?")

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Control pins - active low outputs, start HIGH
        GPIO.setup(self._wr_p, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self._wr_y, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self._ic_y, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self._a0_y, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self._a1_y, GPIO.OUT, initial=GPIO.LOW)

        # Setup SPI
        self._spi = spidev.SpiDev()
        self._spi.open(self._spi_bus, self._spi_device)
        self._spi.max_speed_hz = 8_000_000  # 8 MHz - plenty fast for shift register
        self._spi.mode = 0  # CPOL=0, CPHA=0

        self._initialized = True

        # Reset chips to known state
        self.reset()

    def cleanup(self) -> None:
        """Clean up GPIO and SPI resources."""
        if self._spi:
            self._spi.close()
            self._spi = None
        if _HAS_HARDWARE and self._initialized:
            GPIO.cleanup()
        self._initialized = False

    def reset(self) -> None:
        """
        Reset both chips to initial state.

        Pulses IC_Y low for 500µs to reset YM2612, then silences PSG.
        """
        self._check_initialized()

        # Reset YM2612: pulse IC low for 500µs
        GPIO.output(self._ic_y, GPIO.LOW)
        time.sleep(0.0005)  # 500µs
        GPIO.output(self._ic_y, GPIO.HIGH)
        time.sleep(0.001)  # 1ms settle time

        # Silence PSG
        self.silence_psg()

        self._in_dac_stream = False

    def write_ym2612(self, port: int, reg: int, val: int) -> None:
        """
        Write to a YM2612 register.

        The YM2612 has two ports (0 and 1) for channels 1-3 and 4-6.
        Writing is a two-step process: set address, then set data.

        Args:
            port: Port number (0 or 1)
            reg: Register address (0x00-0xFF)
            val: Value to write (0x00-0xFF)
        """
        self._check_initialized()

        # FM writes invalidate DAC stream setup (changes A0/A1 pins)
        self._in_dac_stream = False

        # Set port select (A1)
        GPIO.output(self._a1_y, GPIO.HIGH if port else GPIO.LOW)

        # Address phase - GenesisBoard.cpp:128-137
        GPIO.output(self._a0_y, GPIO.LOW)  # Address mode
        self._spi.xfer2([reg])
        self._pulse_wr_y()

        # Wait for address latch - GenesisBoard.cpp:140
        time.sleep(self.YM_BUSY_US / 1_000_000)

        # Data phase - GenesisBoard.cpp:143-152
        GPIO.output(self._a0_y, GPIO.HIGH)  # Data mode
        self._spi.xfer2([val])
        self._pulse_wr_y()

    def write_dac(self, sample: int) -> None:
        """
        Write an 8-bit sample to the DAC (YM2612 channel 6).

        For streaming, call begin_dac_stream() first for better performance.

        Args:
            sample: 8-bit sample value (0x00-0xFF, 0x80 = silence)
        """
        self._check_initialized()

        if not self._in_dac_stream:
            self.begin_dac_stream()

        # Just write data (address already set) - GenesisBoard.cpp:190-193
        self._spi.xfer2([sample])
        self._pulse_wr_y()

    def begin_dac_stream(self) -> None:
        """
        Prepare for DAC streaming (optimized for rapid sample writes).

        Sets up address register once so write_dac() only needs to send data.
        """
        self._check_initialized()

        # Set up for DAC register (0x2A on port 0)
        GPIO.output(self._a1_y, GPIO.LOW)   # Port 0
        GPIO.output(self._a0_y, GPIO.LOW)   # Address mode
        self._spi.xfer2([0x2A])             # DAC data register
        self._pulse_wr_y()

        time.sleep(self.YM_BUSY_US / 1_000_000)

        GPIO.output(self._a0_y, GPIO.HIGH)  # Data mode for streaming
        self._in_dac_stream = True

    def end_dac_stream(self) -> None:
        """
        End DAC streaming mode.

        """
        self._in_dac_stream = False

    def write_psg(self, val: int) -> None:
        """
        Write to the SN76489 PSG chip.

        Note: Bit reversal is applied due to board wiring (QA→D7).

        Args:
            val: PSG command byte (0x00-0xFF)
        """
        self._check_initialized()

        # Apply bit reversal - GenesisBoard.cpp:240-245
        val = self._reverse_bits(val)

        # Shift out and pulse WR_P
        self._spi.xfer2([val])
        self._pulse_wr_p()

    def silence_psg(self) -> None:
        """
        Silence all PSG channels.

        Sets all 4 channels (3 tone + 1 noise) to maximum attenuation.
        """
        # Channel attenuation commands: 0x9F, 0xBF, 0xDF, 0xFF
        for channel in range(4):
            self.write_psg(0x9F | (channel << 5))

    def mute_all(self) -> None:
        """
        Silence all sound from both chips.

        Keys off all FM channels, silences DAC, and silences PSG.
        """
        self._check_initialized()

        # End DAC stream first so FM writes work correctly
        self._in_dac_stream = False

        # Key off all FM channels
        for channel in range(6):
            # Channel mapping for key on/off register:
            # Channels 0-2 use values 0-2, channels 3-5 use values 4-6
            ch_val = channel if channel < 3 else channel + 1
            self.write_ym2612(0, 0x28, ch_val)  # Key off (operator mask = 0)

        # Silence DAC (0x80 = center/silent) and disable DAC output
        self.write_ym2612(0, 0x2A, 0x80)
        self.write_ym2612(0, 0x2B, 0x00)

        # Silence PSG
        self.silence_psg()

    def _pulse_wr_y(self) -> None:
        """Pulse YM2612 write strobe low then high."""
        GPIO.output(self._wr_y, GPIO.LOW)
        GPIO.output(self._wr_y, GPIO.HIGH)

    def _pulse_wr_p(self) -> None:
        """Pulse PSG write strobe low then high with required delay."""
        GPIO.output(self._wr_p, GPIO.LOW)
        time.sleep(self.PSG_BUSY_US / 1_000_000)  # PSG needs longer pulse
        GPIO.output(self._wr_p, GPIO.HIGH)

    @staticmethod
    def _reverse_bits(b: int) -> int:
        """
        Reverse bits in a byte (for PSG wiring).

        """
        b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
        b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
        b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
        return b

    def _check_initialized(self) -> None:
        """Raise error if begin() hasn't been called."""
        if not self._initialized:
            raise RuntimeError("GenesisBoard.begin() must be called first")
