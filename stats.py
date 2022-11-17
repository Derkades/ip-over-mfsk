import settings

ljust = 25
print('min freq:'.ljust(ljust), settings.FREQ_BASE)
print('max freq:'.ljust(ljust), settings.FREQ_BASE + settings.FREQ_SPACE * 2**settings.TONE_BITS)
print('samples per tone:'.ljust(ljust), settings.SAMPLES_PER_TONE)
rate = settings.TONE_BITS * settings.TONES_PER_SECOND
print('data rate:'.ljust(ljust), str(rate), 'bits/s', str(rate//8), 'bytes/s')
print('transmission overhead:'.ljust(ljust), settings.OUTPUT_PRE_NOISE_SECONDS, 'seconds')
print('text message:'.ljust(ljust), int(128*8/rate + settings.OUTPUT_PRE_NOISE_SECONDS), 'seconds')
print('small pdf:'.ljust(ljust), int(128*1024*8/rate/60 + settings.OUTPUT_PRE_NOISE_SECONDS), 'minutes')
print('low quality song:'.ljust(ljust), int(1.5*1024*1024*8/rate//60 + settings.OUTPUT_PRE_NOISE_SECONDS), 'minutes')
