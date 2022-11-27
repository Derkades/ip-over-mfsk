import wave

import numpy as np

import settings


MAX_READ_FRAMES = 16*1024*1024  # max 32 MiB memory usage (2 bytes per frame)


def read() -> np.ndarray:
    with wave.open(settings.TEST_WAV, 'rb') as wave_reader:

        frame_bytes = wave_reader.readframes(MAX_READ_FRAMES)
        samples = np.frombuffer(frame_bytes, dtype='i2')
        if len(samples) > MAX_READ_FRAMES // 2:
            print('WARNING test.wav length is getting close to maximum!')
        return samples


def write(samples: np.ndarray) -> None:
    with wave.open(settings.TEST_WAV, 'wb') as wave_writer:
        wave_writer.setnchannels(1)  # mono
        wave_writer.setsampwidth(2)  # 16 bits per sample
        wave_writer.setframerate(settings.SAMPLE_RATE)
        wave_writer.writeframes(samples)
        print(f'Written {len(samples)} samples to {settings.TEST_WAV}')
