import settings

ljust = 25
print('min freq:'.ljust(ljust), settings.FREQ_BASE)
print('max freq:'.ljust(ljust), settings.FREQ_BASE + settings.FREQ_SPACE * 2**settings.TONE_BITS)
print('samples per tone:'.ljust(ljust), settings.SAMPLES_PER_TONE)
rate = settings.TONE_BITS * settings.TONES_PER_SECOND
print('data rate:'.ljust(ljust), str(rate), 'bits/s', str(rate//8), 'bytes/s')
overhead = (settings.PRE_NOISE_SAMPLES + settings.SYNC_SWEEP_DURATION) / settings.SAMPLE_RATE
print('transmission overhead:'.ljust(ljust), overhead, 'seconds')
print('text message:'.ljust(ljust), int(128*8/rate + overhead), 'seconds')
print('small pdf:'.ljust(ljust), int(128*1024*8/rate/60 + overhead), 'minutes')
print('low quality song:'.ljust(ljust), int(1.5*1024*1024*8/rate/60 + overhead), 'minutes')
print('record buffer size:'.ljust(ljust), settings.RECORD_BUFFER_SIZE, 'samples')
print('record buffer time:'.ljust(ljust), settings.RECORD_BUFFER_SIZE / settings.SAMPLE_RATE, 'seconds')
print('max process time:'.ljust(ljust), int(settings.RECORD_PROCESS_SIZE / settings.SAMPLE_RATE * 1000), 'ms')
