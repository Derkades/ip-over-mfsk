import numpy as np

# Path to file used for test audio
TEST_WAV = 'test.wav'

# Sample rate used for playback, recording, and interacting with wave files.
# Sensible values are 48000 and 44100.
SAMPLE_RATE = 48_000

# Set to True to use MFSK, which transfers multiple bits per tone and uses a
# Fourier transform to decode incoming data. Set to False to use FSK, which
# transfers a single bit per tone and uses filters (band pass, comb, low pass)
# to decode incoming data.
MFSK = False

if MFSK:
    # Number of tones per second, must be an integer divisor of sample rate.
    # Run valid_speeds.py for list of valid speeds.
    TONES_PER_SECOND = 48

    # Number of bits to transfer per tone. Valid values are 1, 2, 4, 8 for
    # 2, 4, 16, 256 frequencies respectively.
    TONE_BITS = 4
    # Minimum frequency and maximum frequency to use for data transfer.
    # A greater frequency range will produce better results, especially when
    # using a high number of tone bits. Used to calculate FREQ_BASE
    # and FREQ_SPACE
    FREQ_MIN = 500
    FREQ_MAX = 6000

    # Base frequency and space between frequencies for each bit combination.
    # Calculated from settings above
    FREQ_BASE = FREQ_MIN
    FREQ_SPACE = (FREQ_MAX - FREQ_MIN) / (2**TONE_BITS - 1)

    # A sync signal is used to measure the start time of the first sample in
    # an incoming signal. A sweep is used, from one frequency
    # (SYNC_SWEEP_BEGIN) to another (SYNC_SWEEP_END)
    SYNC_SWEEP_BEGIN = FREQ_MAX
    SYNC_SWEEP_END = FREQ_MIN

    # Number of samples, how long the sweep should be.
    SYNC_SWEEP_SAMPLES = SAMPLE_RATE

    # In how many windows to split incoming sweep to calculate
    # frequencies. Setting this too low or too high decreases accuracy.
    SYNC_FFT_SPLIT = 60

    # Time offset for first tone (in number of samples)
    SYNC_CALIBRATION_OFFSET = int(0.0005*SAMPLE_RATE)

    # Tone used to denote end of transmission
    SYNC_END_TONE = 2**TONE_BITS

    # Fraction of tone to read for FFT. e.g. 4 means 1/4th of the tone (left
    # and right from the midpoint) is considered (so half in total). A smaller
    # value avoids edge artifacts. A too small value means there are not
    # enough samples to measure frequency accurately.
    INPUT_READ_FRACTION = 8
    # Input read size, in samples
    INPUT_READ_SIZE = SAMPLE_RATE // TONES_PER_SECOND // INPUT_READ_FRACTION
    # Tone offset, for example enter a small negative number if the
    # interpreted tones are all slightly too high.
    TONE_CALIBRATION_OFFSET = 0

    # Gray-encode bytes before sending, and gray-decode after receiving. Seems
    # to make no difference in transmission reliability.
    USE_GRAY_ENCODING = False
else:
    # Number of tones per second, must be an integer divisor of sample rate.
    # Run valid_speeds.py for list of valid speeds.
    # Equal to resulting baud rate
    TONES_PER_SECOND = 1920
    # Frequency used for mark (1-bit). Should generally be set to match the
    # baud rate, or double
    FREQ_MARK = TONES_PER_SECOND
    # Frequency used for space (0-bit). Should generally be set to match the
    # baud rate, or double (opposite of mark frequency)
    FREQ_SPACE = TONES_PER_SECOND*2
    # Start marker to identify start of incoming transmission. Should be long
    # enough for the start marker to not occur in the message coincidentally,
    # but short enough to not introduce unnecessary overhead.
    START_MARKER = b'RAPHBIN'

# Samples per tone, calculated from sample rate and tones per
# second. Verified to integer divisible.
SAMPLES_PER_TONE = SAMPLE_RATE // TONES_PER_SECOND
assert SAMPLE_RATE // TONES_PER_SECOND == SAMPLE_RATE / TONES_PER_SECOND

# Use convolution with Gaussian kernel for smoother frequency transitions.
GAUSSIAN = True
if GAUSSIAN:
    # Size of Gaussian kernel. Larger means larger (smoother) transitions,
    # but fewer samples for the actual tone itself.
    GUASSIAN_KERNEL_SIZE = SAMPLES_PER_TONE // 4
else:
    # Reduce clicking by making sure the sine wave stops at the end of a period
    ANTICLICK_STOP_AT_FULL_PERIOD = True
    # Reduce clicking by adding a fade-in and fade-out to every tone
    ANTICLICK_FADE = True
    # e.g. 16 means 1/16th of a tone used for fade-in and fade-out
    ANTICLICK_FADE_AMOUNT = 8

# Size of buffer when recording (number of samples). Should be large enough
# to fit the entire sync sweep tone, but it does not have to be large
# enough to fit an entire transmission.
RECORD_BUFFER_SIZE = 128*1024
# How often to process the buffer. Should always be smaller than
# RECORD_BUFFER_SIZE, or data is missed. Processing is resource-intensive and
# should not be done more frequently than necessary.
RECORD_PROCESS_SIZE = RECORD_BUFFER_SIZE // 2

# Compress data using optimized gzip before sending. Data is transparently
# decompressed after receiving. Useful for testing transmission stability,
# since compressed bits are more "random" and more likely to include very
# low and very high byte values, unlike ASCII.
DO_COMPRESS = False

# Short, quiet noise to wake up audio interface and prevent artifacts at start
# and end of transmission
NOISE_SAMPLES = SAMPLE_RATE // 3
NOISE_LEVEL = 1e4

# Maximum value of a signed short (2 bytes)
OUTPUT_MAX = np.iinfo(np.int16).max
