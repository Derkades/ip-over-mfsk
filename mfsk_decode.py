import wave

import numpy as np
from numpy.fft import rfft
from matplotlib import pyplot as plt

import gray
import int4list
import crc16
import settings


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


def FFT(x):
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
            s_fft = FFT(sinusoid)
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
    print(data_4bit)
    # Start after start marker
    data_4bit = data_4bit[find_start(data_4bit):]
    # Convert bytes to 4 bit integer list
    data_bytes = int4list.int4list_to_bytes(data_4bit)
    # Stop at first zero byte
    # TODO this will break when message/checksum contains null bytes, find a better way (like a start header that contains packet length and checksum)
    data_bytes = data_bytes[:data_bytes.index(0)]

    message_checksum = crc16.crc16(data_bytes[:-2])

    if message_checksum >> 8 == data_bytes[-2] and message_checksum & 0xFF == data_bytes[-1]:
        print('checksum valid')
    else:
        print('checksum incorrect')
        print(message_checksum >> 8, message_checksum & 0xFF)
        print(data_bytes[-2], data_bytes[-1])

    print('message:', data_bytes[:-2].decode())

    plt.specgram(samples, Fs=settings.SAMPLE_RATE)
    plt.show()

# def DetectStart():
#     """
#     startdetectie:
#         detecteer een lengte van [samplesPerBit] met de frequentie [base_frequency]
#     """
#     X = FFT(wav_data[56000:61100])
#     f_loc = np.argmax(X[0])
#     f_val = X[1][f_loc]