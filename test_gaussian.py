import numpy as np
from matplotlib import pyplot as plt

import settings
import encode

assert settings.MFSK
assert settings.TONE_BITS == 4

tones = np.array([2, 5, 6, 3, 5, 2, 3])
freqs_repeated = encode.tone_frequencies(tones)

# Convolution with cosine kernel, centered with peak at x=0
kernel_x = np.linspace(-np.pi, np.pi, settings.SAMPLES_PER_TONE // 2)
kernel_y = np.cos(kernel_x) + 1  # cosine in range to [0, 2] (adjusted from [-1, 1])
kernel_y /= np.sum(kernel_y)  # normalize, for consistent amplitude after convolution
freqs_smooth = np.convolve(freqs_repeated, kernel_y)

# Convert frequency array to sine wave with those frequencies
audio_x = np.arange(len(freqs_smooth))
audio_samples_smooth = np.sin(np.cumsum(2*np.pi * freqs_smooth) / settings.SAMPLE_RATE)

# Do the same for raw frequencies, for plots
# Convolution with single one value. This does nothing except produce an
# array equal in length to the array produced by the gaussian convolution.
noop_kernel = np.zeros(len(kernel_y))
noop_kernel[len(kernel_y) // 2] = 1
freqs_raw = np.convolve(freqs_repeated, noop_kernel)
audio_samples_raw = np.sin(np.cumsum(2*np.pi * freqs_raw) / settings.SAMPLE_RATE)

# Human readable x-axis for plots, seconds instead of sample index
audio_x_seconds = np.linspace(0, len(audio_x) / settings.SAMPLE_RATE, len(audio_x))

for i, name, freqs_arr, audio_arr in ((0, 'raw', freqs_raw, audio_samples_raw),
                                      (1, 'smooth', freqs_smooth, audio_samples_smooth)):
    ax1 = plt.subplot(2, 3, i*3+1)
    ax1.set_title('frequencies, ' + name)
    ax1.plot(audio_x_seconds, freqs_arr)
    ax2 = plt.subplot(2, 3, i*3+2, sharex=ax1)
    ax2.set_title('audio waveform')
    ax2.plot(audio_x_seconds, audio_arr)
    ax3 = plt.subplot(2, 3, i*3+3, sharex=ax1, sharey=ax1)
    ax3.set_title('audio spectogram (w/ orig freq overlay)')
    ax3.specgram(audio_arr, Fs=settings.SAMPLE_RATE)
    ax3.plot(audio_x_seconds, freqs_arr, color='red')
    ax3.set_ylim(top=max(freqs_smooth) * 1.2)

plt.show()
