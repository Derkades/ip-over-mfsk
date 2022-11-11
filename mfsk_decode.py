import wave
import struct
from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt
from sympy import print_maple_code

import crc16
import settings
import smallgzip
import tone_conversion


START_MARKER_TONES = tone_conversion.bytes_to_tones(settings.START_MARKER)


class ChecksumError(Exception):
    def __init__(self, checksum_header: int, checksum_message: int):
        super().__init__(f'Expected checksum {checksum_header} but message has checksum {checksum_message}')


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

        if settings.DO_COMPRESS:
            self.content = smallgzip.decompress(self.content)


def find_start(tones):
    marker_pos = 0
    for i, data in enumerate(tones):
        if data == START_MARKER_TONES[marker_pos]:
            marker_pos += 1
            if marker_pos == len(START_MARKER_TONES):
                return i + 1


def generate_frequencies():
    f_list = []
    for i in range(2**settings.TONE_BITS):
        f_list.append(settings.FREQ_BASE + settings.FREQ_SPACE * i)
    return f_list


def fft(x):
    y_fft = np.fft.rfft(x)
    y_fft = y_fft[:round(len(x)/2)]
    y_fft = np.abs(y_fft)
    y_fft = y_fft/max(y_fft)
    freq_x_axis = np.linspace(0, settings.SAMPLE_RATE / 2, len(y_fft))
    return [y_fft, freq_x_axis]


def audio_to_tones(samples: np.ndarray) -> list[int]:
    previous_sample = 0
    mfsk_freqs = generate_frequencies()
    tones = []
    for sample in range(0, len(samples) + 1, settings.SAMPLE_RATE // settings.TONES_PER_SECOND):
        if sample > 0:
            sinusoid = samples[previous_sample:sample]
            s_fft = fft(sinusoid)
            f_loc = np.argmax(s_fft[0])
            f_val = s_fft[1][f_loc]

            def abs_difference(list_value):
                return abs(list_value - f_val)

            closest_freq = min(mfsk_freqs, key=abs_difference)
            tones.append(mfsk_freqs.index(closest_freq))
            previous_sample = sample
    return tones


def read_test_wav():
    with wave.open(settings.TEST_WAV, 'rb') as wave_reader:
        max_frames = 16*1024*1024 # max 32 MiB memory usage
        frame_bytes = wave_reader.readframes(max_frames)
        return np.frombuffer(frame_bytes, dtype='i2')


if __name__ == '__main__':
    samples = read_test_wav()

    tones = audio_to_tones(samples)

    # Start after start marker
    tones = tones[find_start(tones):]

    # Convert bytes to 4 bit integer list
    data_bytes = tone_conversion.tones_to_bytes(tones)

    try:
        message = ReceivedMessage(data_bytes)
        print('size:', message.size)
        print('checksum:', hex(message.checksum))
        print('message:', message.content.decode())
    except ChecksumError as ex:
        print('(!)', ex)
        print('tones:', tones)
        print('data_bytes:', data_bytes)

    plt.specgram(samples, Fs=settings.SAMPLE_RATE)
    plt.show()
