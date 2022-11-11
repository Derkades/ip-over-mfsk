import wave
import struct
from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt

import gray
import int4list
import crc16
import settings


class ChecksumError(Exception):
    def __init__(self, checksum_header: int, checksum_message: int):
        super(f'Expected checksum {checksum_header} but message has checksum {checksum_message}')


@dataclass
class ReceivedMessage:
    size: int
    checksum: int
    content: bytes

    def __init__(self, data_bytes):
        # Extract length and checksum from header (first 4 bytes)
        self.size, self.checksum = struct.unpack('>HH', data_bytes[:4])

        # Message after header
        self.content = data_bytes[4:4+self.size]
        message_checksum = crc16.crc16(self.content)

        if self.checksum != message_checksum:
            raise ChecksumError(self.checksum, message_checksum)


def find_start(data_4bit):
    marker_ints = int4list.bytes_to_int4list(settings.START_MARKER)
    marker_pos = 0
    for i, data in enumerate(data_4bit):
        if data == marker_ints[marker_pos]:
            marker_pos += 1
            if marker_pos == len(marker_ints):
                return i + 1


def generate_frequencies():
    f_list = []
    for i in range(16):
        f_list.append(settings.FREQ_BASE + settings.FREQ_SPACE * i)
    return f_list


def fft(x):
    y_fft = np.fft.rfft(x)
    y_fft = y_fft[:round(len(x)/2)]
    y_fft = np.abs(y_fft)
    y_fft = y_fft/max(y_fft)
    freq_x_axis = np.linspace(0, settings.SAMPLE_RATE / 2, len(y_fft))
    return [y_fft, freq_x_axis]


def audio_to_int4list(samples: np.ndarray) -> list[int]:
    previous_sample = 0
    mfsk_freqs = generate_frequencies()
    gray_list = []
    for sample in range(0, len(samples) + 1, settings.SAMPLE_RATE // settings.BIT_RATE):
        if sample > 0:
            sinusoid = samples[previous_sample:sample]
            s_fft = fft(sinusoid)
            f_loc = np.argmax(s_fft[0])
            f_val = s_fft[1][f_loc]

            def abs_difference(list_value):
                return abs(list_value - f_val)

            closest_freq = min(mfsk_freqs, key=abs_difference)
            gray_list.append(mfsk_freqs.index(closest_freq))
            previous_sample = sample
    return [gray.from_gray(int4) for int4 in gray_list]


def read_test_wav():
    with wave.open(settings.TEST_WAV, 'rb') as wave_reader:
        max_frames = 16*1024*1024 # max 32 MiB memory usage
        frame_bytes = wave_reader.readframes(max_frames)
        return np.frombuffer(frame_bytes, dtype='i2')


if __name__ == '__main__':
    samples = read_test_wav()

    data_4bit = audio_to_int4list(samples)

    # Start after start marker
    data_4bit = data_4bit[find_start(data_4bit):]

    # Convert bytes to 4 bit integer list
    data_bytes = int4list.int4list_to_bytes(data_4bit)

    message = ReceivedMessage(data_bytes)

    print('size:', message.size)
    print('checksum:', hex(message.checksum))
    print('message:', message.content.decode())

    plt.specgram(samples, Fs=settings.SAMPLE_RATE)
    plt.show()
