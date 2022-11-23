import time

import sounddevice as sd

import settings
import mfsk_decode

sd.default.latency = ('hight', 'high')
sd.default.samplerate = settings.SAMPLE_RATE


if __name__ == '__main__':
    samples = mfsk_decode.read_test_wav()
    while True:
        print('play')
        sd.play(samples)
        sd.wait()

        time.sleep(3)
