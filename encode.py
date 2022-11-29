import sys
from typing import Iterable, Union

import numpy as np

import packet
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
    if settings.MFSK:
        freqs = np.repeat(tones * settings.FREQ_SPACE + settings.FREQ_BASE,
                          settings.SAMPLES_PER_TONE)
        sync = np.linspace(settings.SYNC_SWEEP_END, settings.SYNC_SWEEP_BEGIN,
                           settings.SYNC_SWEEP_SAMPLES)
        end = tone_frequencies(settings.SYNC_END_TONE)
        freqs = np.concatenate((sync, freqs, end))
    else:
        freqs = np.zeros_like(tones, dtype='i2')
        freqs[tones == 1] = settings.FREQ_MARK
        freqs[tones == 0] = settings.FREQ_SPACE
        freqs = np.repeat(freqs, settings.SAMPLES_PER_TONE)

    freqs_smooth = np.convolve(freqs, gauss_kernel(), mode='same')
    sine = np.sin(np.cumsum(2 * np.pi * freqs_smooth) / settings.SAMPLE_RATE)
    return (sine * settings.OUTPUT_MAX).astype(dtype='i2')


def data_to_audio(data: bytes) -> np.ndarray:
    send_data = packet.pack(data)
    print('header_bytes', send_data[:settings.PACKET_HEADER_SIZE])

    # MFSK uses sync sweep to find start, but non-M FSK has no such thing.
    # Prepend start marker to bitstream
    if not settings.MFSK:
        send_data = settings.START_MARKER + send_data

    print('size:', len(send_data))
    print('transmission:', send_data)
    tones = tone_conversion.bytes_to_tones(send_data)
    print('tones:', tones)
    if settings.GAUSSIAN:
        return tones_to_sine_gauss(np.array(tones))
    else:
        return tones_to_sine(tones)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Please provide write/plot/play and message as command line argument')
        sys.exit(1)

    data = ' '.join(sys.argv[2:]).encode()
    noise = np.random.uniform(low=-settings.NOISE_LEVEL,
                              high=settings.NOISE_LEVEL,
                              size=settings.NOISE_SAMPLES).astype('i2')
    samples = np.concatenate((noise, data_to_audio(data), noise))

    print('sample count', len(samples))

    if settings.MFSK:
        first_tone_midpoint = len(noise) + settings.SYNC_SWEEP_SAMPLES + settings.SAMPLES_PER_TONE // 2
    else:
        first_tone_midpoint = len(noise) + settings.SAMPLES_PER_TONE // 2
    print(f'first tone midpoint: ', first_tone_midpoint, f'{first_tone_midpoint/settings.SAMPLE_RATE:.4f}')

    if sys.argv[1] == 'write':
        import test_wav
        test_wav.write(samples)
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
            sd.play(samples // 2, latency='high', samplerate=settings.SAMPLE_RATE, blocking=True)
            print('done')
            sd.sleep(2000)
    else:
        print('Error: expecting first argument "play" or "write"')
        sys.exit(1)
