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
        freq = settings.FREQ_BASE + settings.FREQ_SPACE * tone
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
    header_bytes = struct.pack('>H', checksum)
    send_data = header_bytes + data
    print('size:', len(data))
    print('message:', data)
    print('checksum:', hex(checksum))
    print('header_bytes', header_bytes)
    tones = tone_conversion.bytes_to_tones(send_data)
    start_sync = np.repeat(-1, settings.SYNC_TONES)
    end_sync = np.repeat(2**settings.TONE_BITS, settings.SYNC_TONES)
    tones = np.concatenate((start_sync, tones, end_sync))
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
    if len(sys.argv) < 3:
        print('Please provide play/write and message as command line argument')
        sys.exit(1)

    data = ' '.join(sys.argv[2:]).encode()
    signal = data_to_audio(data)
    if sys.argv[1] == 'write':
        write_test_wav(signal)
    elif sys.argv[1] == 'play':
        import sounddevice as sd
        sd.play(signal, latency='high', samplerate=settings.SAMPLE_RATE, blocking=True)
    else:
        print('Error: expecting first argument "play" or "write"')
        sys.exit(1)
