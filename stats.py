import settings

ljust = 25

if settings.MFSK:
    print('mode:'.ljust(ljust), 'multiple bits, FFT')
    rate = settings.TONE_BITS * settings.TONES_PER_SECOND
    print('data rate:'.ljust(ljust), str(rate), 'bits/s', str(rate//8), 'bytes/s')
    overhead = (settings.NOISE_SAMPLES*2 + settings.SYNC_SWEEP_SAMPLES) / settings.SAMPLE_RATE
    print('record buffer size:'.ljust(ljust), settings.RECORD_BUFFER_SIZE, 'samples')
    print('record buffer time:'.ljust(ljust), f'{settings.RECORD_BUFFER_SIZE / settings.SAMPLE_RATE:.1f} seconds')
    print('max process time:'.ljust(ljust), int(settings.RECORD_PROCESS_SIZE / settings.SAMPLE_RATE * 1000), 'ms')
else:
    print('mode:'.ljust(ljust), 'single bit, comb filter')
    rate = settings.TONES_PER_SECOND
    print('data rate:'.ljust(ljust), str(rate), 'bits/s', str(rate//8), 'bytes/s')
    overhead = (settings.NOISE_SAMPLES*2 + len(settings.START_MARKER)*8*settings.SAMPLES_PER_TONE) / settings.SAMPLE_RATE

print('max packet size:'.ljust(ljust), settings.MAX_PACKET_SIZE, '+', settings.PACKET_HEADER_SIZE, 'bytes')
encoded_samples = (settings.MAX_PACKET_SIZE+settings.PACKET_HEADER_SIZE)*8*settings.SAMPLES_PER_TONE
print('max size, encoded:'.ljust(ljust), f'{encoded_samples} samples, {encoded_samples*2/1024/1024:.1f} MiB')
# buf_size = round(math.log2(encoded_samples) + 1)
# print('recommended buffer size:'.ljust(ljust), f'2**{buf_size} = {2**buf_size}')
print('samples per tone:'.ljust(ljust), settings.SAMPLES_PER_TONE)
print('transmission overhead:'.ljust(ljust), f'{overhead:.1f} seconds')
print()
print('----- TRANSFER DURATION -----')
print('text message (raw):'.ljust(ljust), f'{150*8/rate + overhead:.1f} seconds')
print('text message (HTTP):'.ljust(ljust), f'{2048*8/rate + overhead:.1f} seconds')
print('small pdf:'.ljust(ljust), int(128*1024*8/rate/60 + overhead), 'minutes')
print('low quality song:'.ljust(ljust), int(1.5*1024*1024*8/rate/60 + overhead), 'minutes')
