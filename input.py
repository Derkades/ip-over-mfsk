import time
from enum import Enum

import sounddevice as sd
import numpy as np

import settings
import mfsk_decode


class InputState(Enum):
    WAITING = 1
    RECEIVING = 2


input_state = InputState.WAITING
sample_buffer = np.zeros(settings.RECORD_BUFFER_SIZE, dtype='i2')
buffer_pos = 0
samples_since_process = settings.RECORD_PROCESS_INTERVAL * settings.SAMPLE_RATE
next_tone_pos = None
tones = []


def get_buffer_as_array_starting_from_zero():
    copy = np.zeros(settings.RECORD_BUFFER_SIZE, dtype='i2')
    for i in range(0, settings.RECORD_BUFFER_SIZE):
        copy[i] = sample_buffer[(buffer_pos + i) % settings.settings.RECORD_BUFFER_SIZE]
    return copy


def callback(indata: np.ndarray, frames: int,
             time, status: sd.CallbackFlags) -> None:
    global buffer_pos, samples_since_process

    for i in range(frames):
        sample_buffer[buffer_pos % settings.RECORD_BUFFER_SIZE] = indata[i]
        buffer_pos += 1

    samples_since_process += frames
    if samples_since_process > (settings.RECORD_PROCESS_INTERVAL * settings.SAMPLE_RATE):
        process_recording()
        samples_since_process = 0


def process_recording():
    global buffer_pos, input_state, next_tone_pos
    print('buffer_pos:', buffer_pos, buffer_pos % settings.RECORD_BUFFER_SIZE)

    if input_state == InputState.WAITING:
        first_midpoint = mfsk_decode.find_first_tone_midpoint(sample_buffer)
        if first_midpoint is not None:
            next_tone_pos = (first_midpoint + buffer_pos) % settings.RECORD_BUFFER_SIZE
            print('> found first midpoint at', first_midpoint, next_tone_pos)
        else:
            print('> waiting for noise')
    elif input_state == InputState.RECEIVING:
        print('receiving')
        # Check if we have received a full tone (half tone length past midpoint)
        # We may have even received multiple tones since the last time process_recording() was called
        while buffer_pos > next_tone_pos + settings.SAMPLES_PER_TONE // 2:
            start = (next_tone_pos - settings.SAMPLES_PER_TONE // 2) % settings.RECORD_BUFFER_SIZE
            end = (next_tone_pos + settings.SAMPLES_PER_TONE // 2) % settings.RECORD_BUFFER_SIZE
            tone = mfsk_decode.audio_to_tone(sample_buffer[start:end])
            print('> received tone', tone)
            tones.append(tone)
            next_tone_pos += settings.SAMPLES_PER_TONE
    else:
        raise ValueError(input_state)


if __name__ == '__main__':
    # stop_time = 0
    while True:
        # if stop_time != 0:
        #     print('stopped for', int((time.time_ns() - stop_time) / 1_000_000 * settings.SAMPLE_RATE), 'samples')
        # recording = sd.rec(settings.RECORD_SIZE * settings.SAMPLE_RATE, samplerate=settings.SAMPLE_RATE, channels=1)
        # sd.wait()
        # stop_time = time.time_ns()
        # recordings.append(recording)

        with sd.InputStream(samplerate=settings.SAMPLE_RATE, latency='high', channels=1, callback=callback):
            sd.sleep(settings.RECORD_CHUNK_SIZE * 1000)
