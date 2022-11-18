import wave
import struct
from dataclasses import dataclass
import sys
from typing import Optional

import numpy as np

import crc16
import settings
import smallgzip
import tone_conversion


LJUST = 20
START_MARKER_TONES = tone_conversion.bytes_to_tones(settings.START_MARKER)
print('START_MARKER_TONES'.ljust(LJUST), START_MARKER_TONES)


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


def audio_to_tone(samples: np.ndarray) -> list[int]:
    s_fft = fft(samples)
    f_loc = np.argmax(s_fft[0])
    f_val = s_fft[1][f_loc]
    tone = round((f_val - settings.FREQ_BASE) / settings.FREQ_SPACE)
    # print(f'{f_val:.2f} -> {tone}')
    return tone


def audio_to_tones(samples: np.ndarray, start: int) -> list[int]:
    read_size = settings.SAMPLES_PER_TONE // settings.INPUT_READ_SIZE
    tones = []
    for sample in range(start, len(samples), settings.SAMPLES_PER_TONE):
        tone_samples = samples[sample-read_size:sample+read_size]
        tones.append(audio_to_tone(tone_samples))
    return tones


def find_first_tone_midpoint(samples: np.ndarray) -> Optional[int]:
    group_by = settings.SAMPLES_PER_TONE // 8
    min_count = (settings.OUTPUT_PRE_NOISE_SECONDS * 0.9 * settings.SAMPLE_RATE) // group_by
    start_sample = None
    count = 0
    for i in range(0, len(samples) - group_by, group_by):
        tone = audio_to_tone(samples[i:i+group_by])

        if tone == -1:
            count += 1
            if count == 1:
                start_sample = i
                # print('noise start seconds:', i / settings.SAMPLE_RATE)
                # print('noise start level:', level // group_by)
            elif count > min_count:
                tone_start = start_sample + settings.OUTPUT_PRE_NOISE_SECONDS * settings.SAMPLE_RATE
                first_tone_midpoint = int(tone_start + settings.SAMPLES_PER_TONE / 2)
                return first_tone_midpoint
        else:
            start_sample = None
            count = 0

    return None


def read_test_wav() -> np.ndarray:
    with wave.open(settings.TEST_WAV, 'rb') as wave_reader:
        max_frames = 16*1024*1024 # max 32 MiB memory usage
        frame_bytes = wave_reader.readframes(max_frames)
        return np.frombuffer(frame_bytes, dtype='i2')


if __name__ == '__main__':
    samples = read_test_wav()

    print('audio duration'.ljust(LJUST), f'{len(samples) / settings.SAMPLE_RATE:.1f} seconds')

    first_tone_midpoint = find_first_tone_midpoint(samples)

    if first_tone_midpoint is None:
        raise ValueError('could not identify start')

    print('first tone midpoint'.ljust(LJUST), f'{first_tone_midpoint / settings.SAMPLE_RATE:.2f} seconds')

    tones = audio_to_tones(samples, first_tone_midpoint)

    print('tones:'.ljust(LJUST), tones)
    # Start after start marker
    tones = tones[find_start(tones):]

    # Convert bytes to 4 bit integer list
    data_bytes = tone_conversion.tones_to_bytes(tones)
    print('data_bytes:'.ljust(LJUST), data_bytes)

    try:
        message = ReceivedMessage(data_bytes)
        print('size:'.ljust(LJUST), message.size)
        print('checksum:'.ljust(LJUST), hex(message.checksum))
        print('message:'.ljust(LJUST), message.content.decode())
    except ChecksumError as ex:
        print('(!)'.ljust(LJUST), ex)

    if len(sys.argv) > 1 and sys.argv[1] == 'plot':
        from matplotlib import pyplot as plt
        plt.specgram(samples, Fs=settings.SAMPLE_RATE, scale='dB')
        plt.show()
