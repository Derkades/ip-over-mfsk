import time

import sounddevice as sd

import settings
import mfsk_decode

sd.default.latency = 'high'
sd.default.samplerate = settings.SAMPLE_RATE


if __name__ == '__main__':
    while True:
        print('play')
        samples = mfsk_decode.read_test_wav()
        sd.play(samples)
        sd.wait()

        time.sleep(2)
