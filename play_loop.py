import time

import sounddevice as sd

import settings
import mfsk_decode
import numpy as np

sd.default.latency = ('hight', 'high')
sd.default.samplerate = settings.SAMPLE_RATE


if __name__ == '__main__':
    noise = np.random.uniform(low=-settings.PRE_NOISE_LEVEL,
                              high=settings.PRE_NOISE_LEVEL,
                              size=settings.PRE_NOISE_SAMPLES).astype('i2')
    samples = mfsk_decode.read_test_wav()
    while True:
        print('play')
        sd.play(np.concatenate((noise, samples)), blocking=True)
        time.sleep(3)
