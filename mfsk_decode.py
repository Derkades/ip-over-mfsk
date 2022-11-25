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


class ChecksumError(Exception):
    def __init__(self, checksum_header: int, checksum_message: int):
        super().__init__(f'Expected checksum {checksum_header} but message has checksum {checksum_message}')


@dataclass
class ReceivedMessage:
    checksum: int
    content: bytes

    def __init__(self, data_bytes):
        # Extract checksum (first 2 bytes)
        self.checksum, = struct.unpack('>H', data_bytes[:2])

        # Message after header
        self.content = data_bytes[2:]
        message_checksum = crc16.crc16(self.content)

        if self.checksum != message_checksum:
            raise ChecksumError(self.checksum, message_checksum)

        if settings.DO_COMPRESS:
            self.content = smallgzip.decompress(self.content)


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


def primary_freq(samples):
    s_fft = fft(samples)
    f_loc = np.argmax(s_fft[0])
    return s_fft[1][f_loc]


def audio_to_tone(samples: np.ndarray) -> list[int]:
    f = primary_freq(samples)
    # print(f_val, (f_val - settings.FREQ_BASE) / settings.FREQ_SPACE + settings.TONE_CALIBRATION_OFFSET)
    tone = round((f - settings.FREQ_BASE) / settings.FREQ_SPACE + settings.TONE_CALIBRATION_OFFSET)
    return tone


def audio_to_tones(samples: np.ndarray, start: int) -> list[int]:
    tones = []
    for sample in range(start, len(samples), settings.SAMPLES_PER_TONE):
        tone_samples = samples[sample-settings.INPUT_READ_SIZE:sample+settings.INPUT_READ_SIZE]
        tone = audio_to_tone(tone_samples)
        if tone == settings.SYNC_END_TONE:
            break
        tones.append(tone)
    return tones


def find_first_tone_midpoint_sweep(samples: np.ndarray) -> Optional[int]:
    prev_freq = None
    down_count = 0
    fft_size = settings.SAMPLES_PER_TONE // settings.SYNC_FFT_SPLIT
    for i in range(0, len(samples) - fft_size, fft_size):
        f = primary_freq(samples[i:i+fft_size])
        # print('sync', f, down_count)

        if prev_freq is None:
            pass
        elif f < prev_freq:
            down_count += 1
            if down_count > 3:
                print('sync', f, down_count)
        elif f > prev_freq:
            if down_count >= settings.SYNC_SWEEP_MIN_DOWN:
                return int(i - fft_size / 2 + settings.SAMPLES_PER_TONE * 1.5)
            else:
                if down_count > 3:
                    print('reset up')
                down_count = 0
        prev_freq = f
    return None


def find_first_tone_midpoint(samples: np.ndarray) -> Optional[int]:
    if settings.SYNC_SWEEP:
        return find_first_tone_midpoint_sweep(samples)

    group_by = settings.SAMPLES_PER_TONE // settings.SYNC_FFT_SPLIT
    min_count = int(settings.SYNC_TONES * settings.SAMPLE_RATE * 0.7 / settings.TONES_PER_SECOND / group_by)
    start_sample = None
    count = 0
    not_count = 0
    for i in range(0, len(samples) - group_by, group_by):
        tone = audio_to_tone(samples[i:i+group_by])
        if settings.DEBUG_SYNC_TONES:
            print('tone', tone, 'count', count)

        if tone == -1:
            count += 1
            if count == 1:
                start_sample = i
            elif count > min_count:
                tone_start_sample = start_sample + settings.SYNC_TONES / settings.TONES_PER_SECOND * settings.SAMPLE_RATE
                first_tone_midpoint = int(tone_start_sample + settings.SAMPLES_PER_TONE / 2)
                return first_tone_midpoint
        else:
            not_count += 1

        if not_count > 1:
            start_sample = None
            count = 0
            not_count = 0

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

    # Convert bytes to 4 bit integer list
    data_bytes = tone_conversion.tones_to_bytes(tones)
    print('data_bytes:'.ljust(LJUST), data_bytes)
    print('message size:'.ljust(LJUST), len(data_bytes) - 2)

    try:
        message = ReceivedMessage(data_bytes)
        print('checksum:'.ljust(LJUST), hex(message.checksum))
        print('message:'.ljust(LJUST), message.content.decode())
    except ChecksumError as ex:
        print('(!)'.ljust(LJUST), ex)

    if len(sys.argv) > 1 and sys.argv[1] == 'plot':
        from matplotlib import pyplot as plt
        plt.specgram(samples, Fs=settings.SAMPLE_RATE, scale='dB')
        plt.show()
