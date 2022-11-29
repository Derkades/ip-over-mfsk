from typing import Optional
import sys

import numpy as np
from scipy.signal import firwin, lfiltic, lfilter

import settings
import test_wav
import tone_conversion
from digital_pll import DigitalPLL
from packet import NoStartMarkerError, PacketChecksumError
import packet


START_MARKER_BITS = tone_conversion.bytes_to_tones(settings.START_MARKER)


def find_start(bits: np.ndarray) -> Optional[int]:
    marker_pos = 0
    for i, bit in enumerate(bits):
        if bit == START_MARKER_BITS[marker_pos]:
            marker_pos += 1
            print(marker_pos)
            if marker_pos == len(START_MARKER_BITS):
                return i + 1
        else:
            marker_pos = 0
    return None


def low_pass(samples: np.ndarray) -> np.ndarray:
    lpf_coeffs = np.array(firwin(101, [760.0/(settings.SAMPLE_RATE/2)],
                                 width=None,
                                 pass_zero=True,
                                 scale=True,
                                 window='hann') * settings.OUTPUT_MAX,
                          dtype='i2')
    zl = lfiltic(lpf_coeffs, settings.OUTPUT_MAX, [], [])
    result1, zl = lfilter(lpf_coeffs, settings.OUTPUT_MAX, samples, -1, zl)
    result2, zl = lfilter(lpf_coeffs, settings.OUTPUT_MAX, np.zeros(len(lpf_coeffs)), -1, zl)
    return np.append(result1, result2[len(lpf_coeffs)//2:])


def decode(samples: np.ndarray, plot_option: Optional[list[str]] = None) -> bytes:
    assert not settings.MFSK

    if plot_option:
        from matplotlib import pyplot as plt

    if 'audio' in plot_option:
        plt.plot(samples / 32768)

    # Array of booleans, true where audio sample was positive
    audio_is_positive = samples > 0
    if 'audio_positive' in plot_option:
        plt.plot(audio_is_positive)

    # Delay for comb filter should be half the sample rate
    delay = settings.SAMPLES_PER_TONE // 2

    xored = np.logical_xor(audio_is_positive[:-delay],
                           audio_is_positive[delay:])
    if 'xored' in plot_option:
        plt.plot(xored)

    # Low pass filter
    normalized = (xored - 0.5) * 2.0
    filtered = low_pass(normalized)
    if 'filtered' in plot_option:
        plt.plot(filtered)

    # Convert to booleans again
    bits_signal = filtered > 0

    if 'bits' in plot_option:
        plt.plot(bits_signal)

    pll = DigitalPLL(settings.SAMPLE_RATE, settings.TONES_PER_SECOND)
    clock = np.zeros(len(bits_signal), dtype=int)

    bits = []
    for i in range(len(bits_signal)):
        is_sample = pll(bits_signal[i])
        clock[i] = is_sample
        if is_sample:
            bits.append(int(bits_signal[i]))

    if 'clock' in plot_option:
        plt.plot(clock)

    if plot_option:
        plt.show()

    print(bits)

    start = find_start(bits)
    if start is None:
        raise NoStartMarkerError()

    message_bytes = tone_conversion.tones_to_bytes(bits[start:])

    return packet.unpack(message_bytes)


if __name__ == '__main__':
    audio_data = test_wav.read()
    plot_option = [] if len(sys.argv) < 2 else sys.argv[1].split(',')
    message = decode(audio_data, plot_option)

    print('mesage', message)


# some parts copied from https://github.com/mobilinkd/afsk-demodulator/

# MIT License

# Copyright (c) 2019 Mobilinkd LLC

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
