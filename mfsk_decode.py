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
print('START_MARKER_TONES', START_MARKER_TONES)


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


def audio_to_tones(samples: np.ndarray, start: int) -> list[int]:
    read_size = settings.SAMPLE_RATE // settings.TONES_PER_SECOND // 3
    mfsk_freqs = generate_frequencies()
    tones = []
    for sample in range(start, len(samples), settings.SAMPLE_RATE // settings.TONES_PER_SECOND):
        if sample > 0:
            sinusoid = samples[sample-read_size:sample+read_size]
            s_fft = fft(sinusoid)
            f_loc = np.argmax(s_fft[0])
            f_val = s_fft[1][f_loc]

            def abs_difference(list_value):
                return abs(list_value - f_val)

            closest_freq = min(mfsk_freqs, key=abs_difference)
            tones.append(mfsk_freqs.index(closest_freq))
    return tones


def find_first_tone_midpoint(samples: np.ndarray) -> int:
    group_by = settings.SAMPLE_RATE // settings.TONES_PER_SECOND // 8
    min_count = (settings.OUTPUT_SURROUNDING_NOISE_SECONDS * 0.9 * settings.SAMPLE_RATE) // group_by
    start_sample = None
    count = 0
    for i in range(0, len(samples) - group_by, group_by):
        level = np.sum(np.abs(samples[i:i+group_by]))

        if level > settings.INPUT_PRE_NOISE_LEVEL*group_by:
            count += 1
            if count == 1:
                start_sample = i
                # print('noise start seconds:', i / settings.SAMPLE_RATE)
                # print('noise start level:', level // group_by)
            elif count > min_count:
                tone_start = start_sample + settings.OUTPUT_SURROUNDING_NOISE_SECONDS * settings.SAMPLE_RATE
                tone_length = settings.SAMPLE_RATE // settings.TONES_PER_SECOND
                first_tone_mindpoint = tone_start + (tone_length // 2)
                print(f'first tone midpoint: {first_tone_mindpoint / settings.SAMPLE_RATE:.2f} seconds')
                return first_tone_mindpoint
        else:
            start_sample = None
            count = 0

    raise ValueError('could not identify start')


def read_test_wav():
    with wave.open(settings.TEST_WAV, 'rb') as wave_reader:
        max_frames = 16*1024*1024 # max 32 MiB memory usage
        frame_bytes = wave_reader.readframes(max_frames)
        return np.frombuffer(frame_bytes, dtype='i2')


if __name__ == '__main__':
    samples = read_test_wav()

    print(f'audio duration {len(samples) / settings.SAMPLE_RATE:.1f} seconds')

    first_tone_midpoint = find_first_tone_midpoint(samples)

    tones = audio_to_tones(samples, first_tone_midpoint)

    print('tones:', tones)
    # Start after start marker
    tones = tones[find_start(tones):]

    # Convert bytes to 4 bit integer list
    data_bytes = tone_conversion.tones_to_bytes(tones)
    print('data_bytes:', data_bytes)

    try:
        message = ReceivedMessage(data_bytes)
        print('size:', message.size)
        print('checksum:', hex(message.checksum))
        print('message:', message.content.decode())
    except ChecksumError as ex:
        print('(!)', ex)

    plt.specgram(samples, Fs=settings.SAMPLE_RATE, scale='dB')
    plt.show()
