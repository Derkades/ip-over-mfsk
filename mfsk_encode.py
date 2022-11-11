import sys
import wave

import numpy as np

import gray
import crc16
import int4list
import settings


x = np.arange(settings.SAMPLE_RATE // settings.BIT_RATE)


def uint4_to_sine(data_4bit: list[int]) -> np.ndarray:
    data = []
    tones = [gray.to_gray(uint4) for uint4 in data_4bit]
    tones.extend([0] * 8)
    for tone in tones:
        freq = settings.FREQ_BASE + settings.FREQ_SPACE * tone
        # print(f'{tone=}\t{freq=}')
        wave = settings.OUTPUT_MAX * np.sin(2 * np.pi * freq * x / settings.SAMPLE_RATE)
        data.extend(wave)
    return np.array(data, dtype='i2') # signed 16-bit integers


def data_to_sine(data: bytes) -> np.ndarray:
    # Convert bytes to list of 4-bit integers
    data_4bit = int4list.bytes_to_int4list(settings.START_MARKER + data)
    # Append checksum, split up 16 bit checksum into 4-bit ints
    checksum = crc16.crc16(data)
    for shift in (12, 8, 4, 0):
        data_4bit.append((checksum >> shift) & 0xF)
    print('Sending:', data)
    print('Checksum: ', hex(checksum))
    print('As 4 bit ints:', data_4bit)
    return uint4_to_sine(data_4bit)


def write_test_wav(samples: np.ndarray) -> None:
    with wave.open(settings.TEST_WAV, 'wb') as wave_writer:
        wave_writer.setnchannels(1) # mono
        wave_writer.setsampwidth(2) # 16 bits per sample
        wave_writer.setframerate(settings.SAMPLE_RATE)
        wave_writer.writeframes(signal)
        print(f'Written {len(signal)} samples to {settings.TEST_WAV}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please provide message as command line argument')
        sys.exit(1)

    data = ' '.join(sys.argv[1:]).encode()
    sine = data_to_sine(data)
    noise = np.random.normal(0, 1e4, 56000).astype('i2')
    signal = np.concatenate((noise, sine, noise))
    write_test_wav(signal)
