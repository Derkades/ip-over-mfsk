import settings

ljust = 25
print('min freq:'.ljust(ljust), settings.FREQ_BASE)
print('max freq:'.ljust(ljust), settings.FREQ_BASE + settings.FREQ_SPACE * 2**settings.TONE_BITS)
print('samples per tone:'.ljust(ljust), settings.SAMPLE_RATE // settings.TONES_PER_SECOND)
rate = settings.TONE_BITS * settings.TONES_PER_SECOND
overhead = settings.OUTPUT_SURROUNDING_NOISE_SECONDS * 2
print('data rate:'.ljust(ljust), str(rate), 'bits/s')
print('transmission overhead:'.ljust(ljust), overhead, 'seconds')
print('time to transfer 1 KiB:'.ljust(ljust), int(1024*8/rate + overhead), 'seconds')
