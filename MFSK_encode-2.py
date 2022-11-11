from time import sleep
import struct
import numpy as np
from scipy.io.wavfile import write
st = "test 123 test"


frequency_spacing = 64
base_frequency = 1000
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
samplerate = 44100 #samples per second
bitrate = 15        #bits per second
sendLength = 0
samplesPerBit = samplerate/bitrate
amplitude = np.iinfo(np.int16).max
print(samplesPerBit)
fname = "mfsk.wav"

x = np.arange(samplesPerBit)
"""
wave1 = amplitude * np.sin(2 * np.pi * freq1 * x / samplerate)
wave2 = amplitude * np.sin(2 * np.pi * freq2 * x / samplerate)
"""

def BinaryEncode(st):
    byte_array = st.encode("utf-8")
    binary_int = int.from_bytes(byte_array, "big")

    binary_string = bin(binary_int)
    binary_string = "0" + binary_string[2:]
    print(binary_string)
    sendLength = len(binary_string)
    return binary_string
def SplitPerFourBits(s):
    return [s[i:i+4] for i in range(0, len(s), 4)]



binary = BinaryEncode(st)
def GenerateSineWave(bytelist):
    data = []
    tonelist = [0,0,0,0,0,0,0,0]
    for byte in bytelist:
        tonelist.append(ByteLookup.get(byte))
    tonelist.extend([0,0,0,0,0,0,0,0])
    for greycode in tonelist:
        freq = base_frequency + frequency_spacing*greycode
        print(freq)
        wave = amplitude * np.sin(2 * np.pi * freq * x / samplerate)
        data.extend(wave)
    return data

binary = BinaryEncode(st)
sine = np.array(GenerateSineWave(SplitPerFourBits(binary)))
sine = np.append(np.random.normal(0,1e5,56000),sine)
print(sine[50:])
write(fname, samplerate, sine.astype(np.dtype('i2')))
