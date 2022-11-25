import numpy as np

TEST_WAV = 'test.wav'

SAMPLE_RATE = 44_100
TONES_PER_SECOND = 7  # 1, 2, 3, 4, 5, 6, 7, 10, 14, 15, 18
SAMPLES_PER_TONE = SAMPLE_RATE // TONES_PER_SECOND
assert SAMPLE_RATE // TONES_PER_SECOND == SAMPLE_RATE / TONES_PER_SECOND

TONE_BITS = 4
FREQ_BASE = 512
FREQ_SPACE = 192
FREQ_MIN = FREQ_BASE
FREQ_MAX = FREQ_BASE + FREQ_SPACE * 2**TONE_BITS

DO_COMPRESS = False

SYNC_START_TONE = -1  # Not used when SYNC_SWEEP is True
SYNC_END_TONE = 2**TONE_BITS
SYNC_SWEEP = True
SYNC_SWEEP_MAX = FREQ_MAX
SYNC_SWEEP_MIN = FREQ_MIN
SYNC_FFT_SPLIT = 32
SYNC_SWEEP_MIN_DOWN = SYNC_FFT_SPLIT // 4

INPUT_READ_FRACTION = 4  # e.g. 4 means 1/4th of the tone (left and right from the midpoint) is considered (so half in total)
INPUT_READ_SIZE = SAMPLES_PER_TONE // INPUT_READ_FRACTION
TONE_CALIBRATION_OFFSET = 0

ANTICLICK_STOP_AT_FULL_PERIOD = True
ANTICLICK_FADE = True
ANTICLICK_FADE_AMOUNT = 8  # 16 means 1/16th of a tone used for fade-in and fade-out
GUASSIAN = True  # When enabled, all anticlick options are ignored
GUASSIAN_KERNEL_SIZE = SAMPLES_PER_TONE // 4

RECORD_BUFFER_SIZE = 128*1024
RECORD_PROCESS_SIZE = RECORD_BUFFER_SIZE // 2

# Short, quiet noise to wake up audio interface
PRE_NOISE_SAMPLES = SAMPLE_RATE // 3
PRE_NOISE_LEVEL = 1e4

OUTPUT_MAX = np.iinfo(np.int16).max

# Must process at least once before buffer is overwritten completely, or data is lost
# assert RECORD_PROCESS_INTERVAL * SAMPLE_RATE < RECORD_BUFFER_SIZE

DEBUG_SYNC_TONES = True
