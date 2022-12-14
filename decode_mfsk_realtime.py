from enum import Enum
from threading import Thread
import time

import sounddevice as sd
import numpy as np

import settings
import decode_mfsk
from decode_mfsk import ReceivedMessage, ChecksumError
import tone_conversion


class InputState(Enum):
    WAITING = 1
    RECEIVING = 2


class AudioProcessor(Thread):
    need_process: bool
    buffer: np.ndarray
    buffer_pos: int
    input_state: InputState
    next_tone_mid_pos: int
    tones: list[int]

    def __init__(self):
        super().__init__(daemon=True)
        self.need_process = False
        self.input_state = InputState.WAITING
        self.tones = []

    def run(self):
        while True:
            if self.need_process:
                self.process()
            time.sleep(0.01)

    def update_buffer(self, buffer: np.ndarray, buffer_pos: int):
        self.buffer = buffer
        self.buffer_pos = buffer_pos
        self.need_process = True

    def get_buffer_as_array(self, start, count):
        copy = np.zeros(count, dtype='i2')
        for i in range(0, count):
            copy[i] = self.buffer[(start + i) % settings.RECORD_BUFFER_SIZE]
        return copy

    def process(self):
        # start_time = time.time_ns()
        self.need_process = False

        if self.buffer_pos < settings.RECORD_BUFFER_SIZE:
            print('waiting to fill buffer', self.buffer_pos / settings.RECORD_BUFFER_SIZE)
            return

        # print('buffer_pos:', self.buffer_pos, self.buffer_pos % settings.RECORD_BUFFER_SIZE)

        if self.input_state == InputState.WAITING:
            samples = self.get_buffer_as_array(self.buffer_pos, settings.RECORD_BUFFER_SIZE)
            first_midpoint = decode_mfsk.find_first_tone_midpoint(samples)
            if first_midpoint is not None:
                self.next_tone_mid_pos = self.buffer_pos - settings.RECORD_BUFFER_SIZE + first_midpoint
                print('> found first midpoint at', '0-indexed', first_midpoint, 'midpoint pos in buffer', self.next_tone_mid_pos)
                self.input_state = InputState.RECEIVING
            else:
                print('> waiting for sync')
        elif self.input_state == InputState.RECEIVING:
            print('receiving', 'buf_pos', self.buffer_pos, 'tone_pos', self.next_tone_mid_pos)
            # Check if we have received a full tone (half tone length past midpoint)
            # We may have even received multiple tones since the last time process_recording() was called
            while self.buffer_pos > self.next_tone_mid_pos + settings.INPUT_READ_SIZE:
                tone_start = self.next_tone_mid_pos - settings.INPUT_READ_SIZE
                samples = self.get_buffer_as_array(tone_start, settings.INPUT_READ_SIZE * 2)
                tone = decode_mfsk.audio_to_tone(samples)
                print('tones', self.tones)
                if tone == settings.SYNC_END_TONE:
                    print('...end tone!')
                    self.input_state = InputState.WAITING
                    self.decode_message()
                    print('bytes', )
                    self.tones = []
                    break
                elif tone < 0 or tone > 2**settings.TONE_BITS:
                    print('illegal tone! RESET', tone)
                    self.input_state = InputState.WAITING
                    self.tones = []
                    break
                self.tones.append(tone)
                self.next_tone_mid_pos += settings.SAMPLES_PER_TONE
        else:
            raise ValueError(self.input_state)

        # print('took', (time.time_ns() - start_time) // 1000000, 'ms')

    def decode_message(self):
        data_bytes = tone_conversion.tones_to_bytes(self.tones)
        print('received', len(data_bytes), 'bytes', '-', data_bytes)
        if len(data_bytes) < 3:
            print('too short')
        else:
            try:
                message = ReceivedMessage(data_bytes)
                print('VALID MESSAGE:', message.content.decode())
            except ChecksumError as ex:
                print('corrupt message:', ex)


class AudioReceiver:
    buffer: np.ndarray
    buffer_pos: int
    samples_since_process: int

    def __init__(self):
        self.buffer = np.zeros(settings.RECORD_BUFFER_SIZE, dtype='i2')
        self.buffer_pos = 0
        self.samples_since_process = settings.RECORD_PROCESS_SIZE * settings.SAMPLE_RATE

    def process(self, samples: np.ndarray) -> None:
        for i in range(len(samples)):
            self.buffer[self.buffer_pos % settings.RECORD_BUFFER_SIZE] = samples[i] * settings.OUTPUT_MAX
            self.buffer_pos += 1

        self.samples_since_process += len(samples)
        if self.samples_since_process > settings.RECORD_PROCESS_SIZE:
            audio_processor.update_buffer(np.copy(self.buffer), self.buffer_pos)
            self.samples_since_process = 0

    def run(self):
        def callback(indata, frames, time, status):
            self.process(indata)

        with sd.InputStream(samplerate=settings.SAMPLE_RATE, latency='high', channels=1, callback=callback):
            while True:
                sd.sleep(1000)


if __name__ == '__main__':
    audio_processor = AudioProcessor()
    audio_processor.start()
    audio_receiver = AudioReceiver()
    audio_receiver.run()
