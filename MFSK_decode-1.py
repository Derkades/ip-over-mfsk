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

frequency_spacing = 64
base_frequency = 1000

bitrate = 15        #bits per second
sendLength = 0

fname = "mfsk.wav"
wavfile = read(fname, mmap=False)
samplerate = wavfile[0]
data = wavfile[1]
ts = 1/samplerate
samplesPerBit = samplerate/bitrate
amplitude = np.iinfo(np.int16).max

freq_bins = np.arange(len(data//2)*samplerate/len(data))

ByteLookup = { #lookup table for getting the tone number of a byte
    "0000":0,
    "0001":1,
    "0011":2,
    "0010":3,
    "0110":4,
    "0111":5,
    "0101":6,
    "0100":7,
    "1100":8,
    "1101":9,
    "1111":10,
    "1110":11,
    "1010":12,
    "1011":13,
    "1001":14,
    "1000":15
}

def GenerateFrequencies(spacing,base):
    f_list = []
    for i in range(16):
        f_list.append(base+spacing*i)
    return f_list

def BinaryDecode(bytelist): #under construction
    binary_int = int(bytelist, 2)
    byte_number = binary_int.bit_length() + 7 // 8
    binary_array = binary_int.to_bytes(byte_number, "big")
    ascii_text = binary_array.decode()
    return ascii_text

def FFT(x):
    y_fft = rfft(x)
    y_fft = y_fft[:round(len(x)/2)]
    y_fft = np.abs(y_fft)
    y_fft = y_fft/max(y_fft)
    freq_x_axis = np.linspace(0, samplerate/2, len(y_fft))
    return [y_fft,freq_x_axis]

def AudioToBits():
    previous_sample = 0
    bit_list = ""
    mfsk_freqs = GenerateFrequencies(frequency_spacing,base_frequency)
    gray_list = []
    bit_list = ""
    for sample in range(0,len(data)+1,int(samplesPerBit)):
        if sample > 0:
            sinusoid = data[previous_sample:sample]
            s_fft = FFT(sinusoid)
            f_loc = np.argmax(s_fft[0])
            f_val = s_fft[1][f_loc]
            absDifference = lambda list_value : abs(list_value - f_val)
            closest_freq = min(mfsk_freqs, key=absDifference)
            #print(f_val,closest_freq)
            gray_list.append(mfsk_freqs.index(closest_freq))
            previous_sample = sample
    for value in gray_list:
        bit_list += (list(ByteLookup.keys())[list(ByteLookup.values()).index(value)])
    return bit_list

def DetectStart():
    X = FFT(data[56000:61100])
    f_loc = np.argmax(X[0])
    f_val = X[1][f_loc]

DetectStart()
"""
startdetectie:
    detecteer een lengte van [samplesPerBit] met de frequentie [base_frequency]

"""
print(BinaryDecode(AudioToBits()))

powerSpectrum, frequenciesFound, time, imageAxis = plt.specgram(data, Fs=samplerate)
print(list(zip(frequenciesFound,time)))
plt.show()
