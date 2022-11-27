import numpy as np
from matplotlib import pyplot as plt
import scipy.signal
from scipy.signal import firwin, lfiltic, lfilter

import settings
import mfsk_decode
import tone_conversion
from DigitalPLL import DigitalPLL


class fir_filter(object):
    def __init__(self, coeffs):
        self.coeffs = coeffs
        self.zl = lfiltic(self.coeffs, 32768.0, [], [])

    def __call__(self, data):
        result, self.zl = lfilter(self.coeffs, 32768.0, data, -1, self.zl)
        return result


if __name__ == '__main__':
    audio_data = mfsk_decode.read_test_wav()
    sample_rate = settings.SAMPLE_RATE

    # plt.plot(audio_data / 32768)

    # DIGITIZE

    # digitized = np.array([int(x > 0) for x in audio_data])
    digitized = audio_data > 0
    # plt.plot(digitized)

    # DIGITALLY CORRELATE

    # 446 microsec is goed voor 1200/2200hz volgens https://github.com/mobilinkd/afsk-demodulator/blob/master/afsk-demodulator.ipynb
    delay = int(0.000446 * settings.SAMPLE_RATE)
    delayed = digitized[delay:]
    xored = np.logical_xor(digitized[:0-delay], delayed)
    # plt.plot(xored)

    # LOW PASS FILTER

    lpf_coeffs = np.array(firwin(101, [760.0/(sample_rate/2)],
                                 width=None,
                                 pass_zero=True,
                                 scale=True,
                                 window='hann') * 32768,
                          dtype=int)

    lpf = fir_filter(lpf_coeffs)
    normalized = (xored - 0.5) * 2.0
    filtered = np.append(lpf(normalized), lpf(np.zeros(len(lpf_coeffs))))[len(lpf_coeffs)//2:]
    # plt.plot(filtered)

    # DIGITIZE AGAIN
    bits_signal = filtered > 0

    # plt.plot(bits_signal)

    pll = DigitalPLL(sample_rate, settings.TONES_PER_SECOND)
    clock = np.zeros(len(bits_signal), dtype=int)

    bits = []
    for i in range(len(bits_signal)):
        is_sample = pll(bits_signal[i])
        clock[i] = is_sample
        if is_sample:
            bits.append(int(bits_signal[i]))

    # plt.plot(clock)

    for i in range(8):
        print(tone_conversion.tones_to_bytes(bits[i:]))

    # plt.show()


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
