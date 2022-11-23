import numpy as np

SAMPLE_RATE = 44_100
TEST_WAV = 'test.wav'
FREQ_BASE = 1024
FREQ_SPACE = 128
OUTPUT_MAX = np.iinfo(np.int16).max
DO_COMPRESS = False
TONES_PER_SECOND = 4
TONE_BITS = 4
SYNC_TONES = 4
INPUT_READ_FRACTION = 6  # e.g. 4 means 1/4th of the tone (left and right from the midpoint) is considered (so half in total)

ANTICLICK_STOP_AT_FULL_PERIOD = False
ANTICLICK_FADE = True
ANTICLICK_FADE_AMOUNT = 16  # 16 means 1/16th of a tone used for fade-in and fade-out

RECORD_CHUNK_SIZE = 1
RECORD_BUFFER_SIZE = 128*1024
RECORD_PROCESS_INTERVAL = RECORD_BUFFER_SIZE // 4

SAMPLES_PER_TONE = SAMPLE_RATE // TONES_PER_SECOND
INPUT_READ_SIZE = SAMPLES_PER_TONE // INPUT_READ_FRACTION
SYNC_START_TONE = -1
SYNC_END_TONE = 2**TONE_BITS

# Must process at least once before buffer is overwritten completely, or data is lost
# assert RECORD_PROCESS_INTERVAL * SAMPLE_RATE < RECORD_BUFFER_SIZE
