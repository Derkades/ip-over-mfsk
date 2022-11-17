import sys
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


def tones_to_sine(tones: list[int]) -> np.ndarray:
    x = np.arange(settings.SAMPLES_PER_TONE)
    data = []
    for tone in tones:
        # freq = settings.FREQ_BASE + settings.FREQ_SPACE * tone
        freq = settings.FREQ_BASE + tone ** 1.5 * settings.FREQ_SPACE
        wave = settings.OUTPUT_MAX * np.sin(2 * np.pi * freq * x / settings.SAMPLE_RATE)
        reduce_click(wave)
        data.extend(wave)
    return np.array(data, dtype='i2') # signed 16-bit integers


def data_to_audio(data: bytes) -> np.ndarray:
    if settings.DO_COMPRESS:
        print('original size:', len(data))
        print('original message:', data)
        data = smallgzip.compress(data)

    # TODO no need to send CRC16 when compression is enabled, saves 2 bytes

    checksum = crc16.crc16(data)
    header_bytes = struct.pack('>HH', len(data), checksum)
    send_data = settings.START_MARKER + header_bytes + data
    print('size:', len(data))
    print('message:', data)
    print('checksum:', hex(checksum))
    print('header_bytes', header_bytes)
    tones = tone_conversion.bytes_to_tones(send_data)
    print('tones:', tones)
    return tones_to_sine(tones)


def write_test_wav(samples: np.ndarray) -> None:
    with wave.open(settings.TEST_WAV, 'wb') as wave_writer:
        wave_writer.setnchannels(1) # mono
        wave_writer.setsampwidth(2) # 16 bits per sample
        wave_writer.setframerate(settings.SAMPLE_RATE)
        wave_writer.writeframes(signal)
        print(f'Written {len(signal)} samples to {settings.TEST_WAV}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please provide message as command line argument')
        sys.exit(1)

    data = ' '.join(sys.argv[1:]).encode()
    sine = data_to_audio(data)
    noise = np.random.normal(0,
                             settings.OUTPUT_PRE_NOISE_LEVEL,
                             int(settings.OUTPUT_PRE_NOISE_SECONDS * settings.SAMPLE_RATE)).astype('i2')
    signal = np.concatenate((noise, sine))
    write_test_wav(signal)
