import numpy as np

TEST_WAV = 'test.wav'

SAMPLE_RATE = 48_000
TONES_PER_SECOND = 1200 # Run valid_speeds.py for list of valid speeds.
SAMPLES_PER_TONE = SAMPLE_RATE // TONES_PER_SECOND
assert SAMPLE_RATE // TONES_PER_SECOND == SAMPLE_RATE / TONES_PER_SECOND

TONE_BITS = 1
FREQ_MIN = 1200
FREQ_MAX = 2200
FREQ_BASE = FREQ_MIN
FREQ_SPACE = (FREQ_MAX - FREQ_MIN) / (2**TONE_BITS - 1)

DO_COMPRESS = False

SYNC_END_TONE = 2**TONE_BITS
SYNC_SWEEP_BEGIN = FREQ_MAX
SYNC_SWEEP_END = FREQ_MIN
SYNC_SWEEP_SAMPLES = SAMPLE_RATE//2
SYNC_FFT_SPLIT = 40
SYNC_CALIBRATION_OFFSET = int(0.0005*SAMPLE_RATE)

INPUT_READ_FRACTION = 8  # e.g. 4 means 1/4th of the tone (left and right from the midpoint) is considered (so half in total)
INPUT_READ_SIZE = SAMPLES_PER_TONE // INPUT_READ_FRACTION
TONE_CALIBRATION_OFFSET = -0.1

ANTICLICK_STOP_AT_FULL_PERIOD = True
ANTICLICK_FADE = True
ANTICLICK_FADE_AMOUNT = 8  # 16 means 1/16th of a tone used for fade-in and fade-out
GUASSIAN = True  # When enabled, all anticlick options are ignored
GUASSIAN_KERNEL_SIZE = SAMPLES_PER_TONE // 4

RECORD_BUFFER_SIZE = 128*1024
RECORD_PROCESS_SIZE = RECORD_BUFFER_SIZE // 2

# Short, quiet noise to wake up audio interface and prevent artifacts at start and end of transmission
NOISE_SAMPLES = SAMPLE_RATE // 3
NOISE_LEVEL = 1e4

USE_GRAY_ENCODING = False

OUTPUT_MAX = np.iinfo(np.int16).max

# Must process at least once before buffer is overwritten completely, or data is lost
# assert RECORD_PROCESS_INTERVAL * SAMPLE_RATE < RECORD_BUFFER_SIZE

DEBUG_SYNC_TONES = True
