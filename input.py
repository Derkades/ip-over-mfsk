from enum import Enum

import sounddevice as sd
import numpy as np

import settings
import mfsk_decode
import tone_conversion


class InputState(Enum):
    WAITING = 1
    RECEIVING = 2
    IGNORE_END_TONES = 3


input_state = InputState.WAITING
sample_buffer = np.zeros(settings.RECORD_BUFFER_SIZE, dtype='i2')
buffer_pos = 0
samples_since_process = settings.RECORD_PROCESS_INTERVAL * settings.SAMPLE_RATE
next_tone_pos = None
tones = []


def get_buffer_as_array(start, count):
    copy = np.zeros(count, dtype='i2')
    for i in range(0, count):
        copy[i] = sample_buffer[(start + i) % settings.RECORD_BUFFER_SIZE]
    return copy


def callback(indata: np.ndarray, frames: int,
             time, status: sd.CallbackFlags) -> None:
    global buffer_pos, samples_since_process

    for i in range(frames):
        sample_buffer[buffer_pos % settings.RECORD_BUFFER_SIZE] = indata[i] * settings.OUTPUT_MAX
        buffer_pos += 1

    samples_since_process += frames
    if samples_since_process > (settings.RECORD_PROCESS_INTERVAL * settings.SAMPLE_RATE):
        process_recording()
        samples_since_process = 0


def process_recording():
    global buffer_pos, input_state, next_tone_pos
    print('buffer_pos:', buffer_pos, buffer_pos % settings.RECORD_BUFFER_SIZE)


    if input_state == InputState.WAITING:
        samples = get_buffer_as_array(buffer_pos, settings.RECORD_BUFFER_SIZE)
        first_midpoint = mfsk_decode.find_first_tone_midpoint(samples)
        if first_midpoint is not None:
            next_tone_pos = (first_midpoint + buffer_pos) % settings.RECORD_BUFFER_SIZE
            print('> found first midpoint at', first_midpoint, next_tone_pos)
            input_state = InputState.RECEIVING
        else:
            print('> waiting for sync')
    elif input_state == InputState.RECEIVING or input_state == InputState.IGNORE_END_TONES:
        print('receiving')
        # Check if we have received a full tone (half tone length past midpoint)
        # We may have even received multiple tones since the last time process_recording() was called
        while buffer_pos > next_tone_pos + settings.SAMPLES_PER_TONE // 2:
            start = next_tone_pos - settings.SAMPLES_PER_TONE // settings.INPUT_READ_SIZE
            count = (settings.SAMPLES_PER_TONE // settings.INPUT_READ_SIZE) * 2
            samples = get_buffer_as_array(start, count)
            tone = mfsk_decode.audio_to_tone(samples)
            if input_state == InputState.IGNORE_END_TONES:
                if tone == settings.SYNC_END_TONE:
                    print('... another end tone')
                else:
                    print('not an end tone', tone)
                    print('transition to WAITING state')
                    input_state = InputState.WAITING
            else:
                print('> received tone', tone)
                if tone == settings.SYNC_END_TONE:
                    print('received end tone!')
                    input_state = InputState.IGNORE_END_TONES
                    print(tone_conversion.tones_to_bytes(tones))
                    break
                elif tone < 0 or tone > 2**settings.TONE_BITS:
                    print('illegal tone! set to 0', tone)
                    tone = 0
                tones.append(tone)
            next_tone_pos += settings.SAMPLES_PER_TONE
    else:
        raise ValueError(input_state)


if __name__ == '__main__':
    while True:
        with sd.InputStream(samplerate=settings.SAMPLE_RATE, latency='high', channels=1, callback=callback):
            sd.sleep(settings.RECORD_CHUNK_SIZE * 1000)
