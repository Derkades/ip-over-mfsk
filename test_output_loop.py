import os
import select
import time
import numpy as np

import sounddevice as sd

import encode
import tun
import settings


# TODO fix ALSA lib pcm.c:8568:(snd_pcm_recover) underrun occurred


if __name__ == '__main__':
    i = 0
    tun_fd = tun.tun_open('tun0')
    poll = select.poll()
    poll.register(tun_fd, select.POLLIN)
    sd.default.latency = 'high'
    sd.default.samplerate = settings.SAMPLE_RATE
    silence = np.zeros(settings.SAMPLE_RATE // 2, dtype='i2')
    while True:
        print('...')
        sd.play(silence, blocking=True)

        if not poll.poll():
            # sd.wait()
            continue

        start_time = time.time()
        network_data = os.read(tun_fd, 4096)
        samples = encode.data_to_audio(network_data)
        sd.play(samples, blocking=True)
        print(f'transmitted {len(network_data)} bytes in {time.time()-start_time:.1f} seconds')
