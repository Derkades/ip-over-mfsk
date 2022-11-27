import sys

import sounddevice as sd

import settings
import test_wav


if __name__ == '__main__':
    duration = float(sys.argv[1])
    print(f'Recording for {duration} seconds at {settings.SAMPLE_RATE/1000:.1f} kHz')

    samples = sd.rec(int(duration * settings.SAMPLE_RATE), samplerate=settings.SAMPLE_RATE, latency='high', channels=1, blocking=True, dtype='i2')
    # sd.wait()
    print(samples)
    test_wav.write(samples)
