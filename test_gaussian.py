import numpy as np
from matplotlib import pyplot as plt

import settings

tones = np.array([1, 3, 2, 4])
freqs = tones * settings.FREQ_SPACE + settings.FREQ_BASE
freqs_repeated = np.repeat(freqs, settings.SAMPLES_PER_TONE)

# Convolution with cosine kernel, centered with peak at x=0
kernel_x = np.linspace(-np.pi, np.pi, settings.SAMPLES_PER_TONE // 2)
kernel_y = np.cos(kernel_x) + 1
kernel_sum = np.sum(kernel_y)
kernel_y /= kernel_sum
freqs_smooth = np.convolve(freqs_repeated, kernel_y)

# Does nothing but ensure same length
noop_kernel = np.zeros(len(kernel_y))
noop_kernel[len(kernel_y) // 2] = 1
freqs_raw = np.convolve(freqs_repeated, noop_kernel)

# Convert frequency array to sine wave with those frequencies
audio_x = np.arange(len(freqs_smooth))
audio_samples_smooth = np.sin(np.cumsum(2*np.pi * freqs_smooth) / settings.SAMPLE_RATE)
audio_samples_raw = np.sin(np.cumsum(2*np.pi * freqs_raw) / settings.SAMPLE_RATE)

audio_x_seconds = np.linspace(0, len(audio_x) / settings.SAMPLE_RATE, len(audio_x))

ax1 = plt.subplot(2, 3, 1)
ax1.set_title('frequencies, smoothed')
ax1.plot(audio_x_seconds, freqs_smooth)
ax2 = plt.subplot(2, 3, 2, sharex=ax1)
ax2.set_title('audio waveform')
ax2.plot(audio_x_seconds, audio_samples_smooth)
ax3 = plt.subplot(2, 3, 3, sharex=ax1, sharey=ax1)
ax3.set_title('audio spectogram')
ax3.specgram(audio_samples_smooth, Fs=settings.SAMPLE_RATE)
ax3.set_ylim(top=max(freqs_smooth) * 1.2)

ax1 = plt.subplot(2, 3, 4)
ax1.set_title('frequencies, no smoothing')
ax1.plot(audio_x_seconds, freqs_raw)
ax2 = plt.subplot(2, 3, 5, sharex=ax1)
ax2.set_title('audio waveform')
ax2.plot(audio_x_seconds, audio_samples_raw)
ax3 = plt.subplot(2, 3, 6, sharex=ax1, sharey=ax1)
ax3.set_title('audio spectogram')
ax3.specgram(audio_samples_raw, Fs=settings.SAMPLE_RATE)
ax3.set_ylim(top=max(freqs_smooth) * 1.2)

plt.show()
