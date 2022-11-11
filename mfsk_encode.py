import sys

import numpy as np
from scipy.io.wavfile import write

import gray
import crc16


START_MARKER = b'RAPHBIN'
frequency_spacing = 512
base_frequency = 1000
sample_rate = 44100  # samples per second
bit_rate = 16  # bits per second
sendLength = 0
samplesPerBit = sample_rate / bit_rate
amplitude = np.iinfo(np.int16).max
fname = "mfsk.wav"
x = np.arange(samplesPerBit)


def bytes_to_4bit(data_8bit: bytes):
    data_4bit = []
    for byte in data_8bit:
        data_4bit.append(byte >> 4)
        data_4bit.append(byte & 0xF)
    return data_4bit


def uint4_to_sine(data_4bit):
    data = []
    tones = [gray.to_gray(uint4) for uint4 in data_4bit]
    tones.extend([0] * 8)
    for tone in tones:
        freq = base_frequency + frequency_spacing * tone
        # print(f'{tone=}\t{freq=}')
        wave = amplitude * np.sin(2 * np.pi * freq * x / sample_rate)
        data.extend(wave)
    return data


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please provide message as command line argument')
        sys.exit(1)

    input_text = ' '.join(sys.argv[1:])

    # Encode text to bytes
    data = input_text.encode()

    # Convert bytes to list of 4-bit integers
    data_4bit = bytes_to_4bit(START_MARKER + data)

    # Append checksum to data
    # Split up 16 bit checksum into 4 4-bit ints
    checksum = crc16.crc16(data)
    for shift in (12, 8, 4, 0):
        data_4bit.append((checksum >> shift) & 0xF)

    print('Sending:', data)
    print('As 4 bit ints:', data_4bit)

    sine = uint4_to_sine(data_4bit)
    sine = np.append(np.random.normal(0, 1e5, 56000), sine)
    # print(sine[50:])
    write(fname, sample_rate, sine.astype(np.dtype('i2')))
