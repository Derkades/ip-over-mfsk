import sys
from typing import Iterable, Union
import wave
import struct

import numpy as np

import crc16
import tone_conversion
import settings
import smallgzip


def reduce_click(samples: np.ndarray):
    if settings.ANTICLICK_STOP_AT_FULL_PERIOD:
        # Ensure sine wave ends at approx zero, at the end of a period
        prev_sample = samples[-1]
        for i in range(2, len(samples) + 1):
            sample = samples[-i]
            if sample < 0 and prev_sample > 0:
                # Reached zero crossing point
                for j in range(-i+1, 0):
                    samples[j] = 0
                break
            prev_sample = sample

    if settings.ANTICLICK_FADE:
        # Add fade-in and fade-out
        fade_count = settings.SAMPLES_PER_TONE // settings.ANTICLICK_FADE_AMOUNT
        for i in range(0, fade_count):
            vol_ratio = i / fade_count
            samples[i] = int(samples[i] * vol_ratio)  # fade-in
            samples[-i-1] = int(samples[-i-1] * vol_ratio)  # fade-out


def tones_to_sine(tones: Iterable[int]) -> np.ndarray:
    x = np.arange(settings.SAMPLES_PER_TONE)
    data = []
    for tone in tones:
        freq = settings.FREQ_BASE + settings.FREQ_SPACE * tone
        wave = settings.OUTPUT_MAX * np.sin(2 * np.pi * freq * x / settings.SAMPLE_RATE)
        reduce_click(wave)
        data.extend(wave)
    return np.array(data, dtype='i2') # signed 16-bit integers


def gauss_kernel() -> np.ndarray:
    # Convolution with cosine kernel, centered with peak at x=0
    # Not exactly guassian, but close enough?
    kernel_x = np.linspace(-np.pi, np.pi, settings.GUASSIAN_KERNEL_SIZE)
    kernel_y = np.cos(kernel_x) + 1  # cosine in range to [0, 2] (adjusted from [-1, 1])
    return kernel_y / np.sum(kernel_y)  # normalize, for consistent amplitude after convolution


def tone_frequencies(tones: Union[int, np.ndarray]) -> np.ndarray:
    return np.repeat(tones * settings.FREQ_SPACE + settings.FREQ_BASE, settings.SAMPLES_PER_TONE)


def tones_to_sine_gauss(tones: np.ndarray) -> np.ndarray:
    freqs = np.repeat(tones * settings.FREQ_SPACE + settings.FREQ_BASE,
                      settings.SAMPLES_PER_TONE)
    if settings.SYNC_SWEEP:
        sync = np.append(np.logspace(np.log2(settings.SYNC_SWEEP_MAX), np.log2(settings.SYNC_SWEEP_MIN), settings.SAMPLES_PER_TONE, base=2),
                         np.logspace(np.log2(settings.SYNC_SWEEP_MIN), np.log2(settings.SYNC_SWEEP_MAX), settings.SAMPLES_PER_TONE, base=2))
    else:
        sync = tone_frequencies(settings.SYNC_START_TONE)
    end = tone_frequencies(settings.SYNC_END_TONE)
    freqs_all = np.concatenate((sync, freqs, end))
    freqs_smooth = np.convolve(freqs_all, gauss_kernel(), mode='same')
    sine = np.sin(np.cumsum(2 * np.pi * freqs_smooth) / settings.SAMPLE_RATE)
    return (sine * settings.OUTPUT_MAX).astype(dtype='i2')


def data_to_audio(data: bytes) -> np.ndarray:
    if settings.DO_COMPRESS:
        print('original size:', len(data))
        print('original message:', data)
        data = smallgzip.compress(data)

    # TODO no need to send CRC16 when compression is enabled, saves 2 bytes

    checksum = crc16.crc16(data)
    header_bytes = struct.pack('>H', checksum)
    send_data = header_bytes + data
    print('size:', len(data))
    print('message:', data)
    print('checksum:', hex(checksum))
    print('header_bytes', header_bytes)
    tones = tone_conversion.bytes_to_tones(send_data)
    print('tones:', tones)
    if settings.GUASSIAN:
        return tones_to_sine_gauss(np.array(tones))
    else:
        return tones_to_sine(tones)


def write_test_wav(samples: np.ndarray) -> None:
    with wave.open(settings.TEST_WAV, 'wb') as wave_writer:
        wave_writer.setnchannels(1) # mono
        wave_writer.setsampwidth(2) # 16 bits per sample
        wave_writer.setframerate(settings.SAMPLE_RATE)
        wave_writer.writeframes(samples)
        print(f'Written {len(samples)} samples to {settings.TEST_WAV}')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Please provide write/plot/play and message as command line argument')
        sys.exit(1)

    data = ' '.join(sys.argv[2:]).encode()
    noise = np.random.uniform(low=-settings.PRE_NOISE_LEVEL,
                              high=settings.PRE_NOISE_LEVEL,
                              size=settings.PRE_NOISE_SAMPLES).astype('i2')
    samples = np.append(noise, data_to_audio(data))

    print(len(samples))

    if sys.argv[1] == 'write':
        write_test_wav(samples)
    elif sys.argv[1] == 'plot':
        from matplotlib import pyplot as plt
        samples_x = np.linspace(0, len(samples) / settings.SAMPLE_RATE, num=len(samples))
        ax1 = plt.subplot(1, 2, 1)
        ax1.specgram(samples, Fs=settings.SAMPLE_RATE, scale='dB')
        ax1.set_ylim(top=10000)
        ax2 = plt.subplot(1, 2, 2, sharex=ax1)
        ax2.plot(samples_x, samples / settings.OUTPUT_MAX)
        plt.show()
    elif sys.argv[1] == 'play':
        import sounddevice as sd

        while True:
            print('play')
            sd.play(samples, latency='high', samplerate=settings.SAMPLE_RATE, blocking=True)
            print('done')
            sd.sleep(2000)
    else:
        print('Error: expecting first argument "play" or "write"')
        sys.exit(1)
