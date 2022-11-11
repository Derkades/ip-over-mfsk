import numpy as np

START_MARKER = b'RAPHBIN'
SAMPLE_RATE = 48_000
TEST_WAV = 'test.wav'
FREQ_BASE = 1024
FREQ_SPACE = 512
OUTPUT_MAX = np.iinfo(np.int16).max

# Do not change
BIT_RATE = 16