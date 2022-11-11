from time import sleep
import struct
import numpy as np
from scipy.io.wavfile import write
from scipy.io.wavfile import read
from numpy.fft import fft, ifft, fftfreq, rfft, rfftfreq
from matplotlib import pyplot as plt
from scipy import signal
import wave
import pylab
import gray

import mfsk_encode
import crc16


START_MARKER = b'RAPHBIN'

frequency_spacing = 512
base_frequency = 1000

bitrate = 16        #bits per second
sendLength = 0

fname = "mfsk.wav"
wavfile = read(fname, mmap=False)
samplerate = wavfile[0]
wav_data = wavfile[1]
ts = 1/samplerate
samplesPerBit = samplerate/bitrate
amplitude = np.iinfo(np.int16).max

freq_bins = np.arange(len(wav_data//2)*samplerate/len(wav_data))


def GenerateFrequencies(spacing, base):
    f_list = []
    for i in range(16):
        f_list.append(base+spacing*i)
    return f_list


# def BinaryDecode(bytelist): #under construction
#     binary_int = int(bytelist, 2)
#     byte_number = binary_int.bit_length() + 7 // 8
#     binary_array = binary_int.to_bytes(byte_number, "big")
#     ascii_text = binary_array.decode()
#     return ascii_text


def find_start(data_4bit):
    marker_ints = mfsk_encode.bytes_to_4bit(START_MARKER)
    marker_pos = 0
    for i, data in enumerate(data_4bit):
        if data == marker_ints[marker_pos]:
            marker_pos += 1
            if marker_pos == len(marker_ints):
                return i + 1

def int4_to_bytes(data_4bit):
    byte_list = []
    for i in range(0, len(data_4bit), 2):
        byte_list.append((data_4bit[i] << 4) ^ data_4bit[i + 1])
    return bytes(byte_list)


def FFT(x):
    y_fft = rfft(x)
    y_fft = y_fft[:round(len(x)/2)]
    y_fft = np.abs(y_fft)
    y_fft = y_fft/max(y_fft)
    freq_x_axis = np.linspace(0, samplerate/2, len(y_fft))
    return [y_fft,freq_x_axis]


def AudioToBits():
    previous_sample = 0
    mfsk_freqs = GenerateFrequencies(frequency_spacing,base_frequency)
    gray_list = []
    for sample in range(0, len(wav_data)+1,int(samplesPerBit)):
        if sample > 0:
            sinusoid = wav_data[previous_sample:sample]
            s_fft = FFT(sinusoid)
            f_loc = np.argmax(s_fft[0])
            f_val = s_fft[1][f_loc]
            absDifference = lambda list_value : abs(list_value - f_val)
            closest_freq = min(mfsk_freqs, key=absDifference)
            #print(f_val,closest_freq)
            gray_list.append(mfsk_freqs.index(closest_freq))
            previous_sample = sample
    bit_list = [gray.from_gray(int4) for int4 in gray_list]
    # for value in gray_list:
        # bit_listgray.from_gray(value)
        # bit_list += (list(ByteLookup.keys())[list(ByteLookup.values()).index(value)])
    return bit_list


def DetectStart():
    """
    startdetectie:
        detecteer een lengte van [samplesPerBit] met de frequentie [base_frequency]
    """
    X = FFT(wav_data[56000:61100])
    f_loc = np.argmax(X[0])
    f_val = X[1][f_loc]


DetectStart()

data_4bit = AudioToBits()
print(data_4bit)
start = find_start(data_4bit)
print(data_4bit[start:])
data = int4_to_bytes(data_4bit[start:]).rstrip(b'\0')
message_checksum = crc16.crc16(data[:-2])

if message_checksum >> 8 == data[-2] and message_checksum & 0xFF == data[-1]:
    print('checksum valid')
else:
    print('checksum incorrect')
    print(message_checksum >> 8, message_checksum & 0xFF)
    print(data[-2], data[-1])

print('message:', data[:-2].decode())

powerSpectrum, frequenciesFound, time, imageAxis = plt.specgram(wav_data, Fs=samplerate)
print(list(zip(frequenciesFound, time)))
plt.show()
