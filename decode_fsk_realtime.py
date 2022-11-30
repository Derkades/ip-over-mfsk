from enum import Enum
from threading import Thread
import time

import sounddevice as sd
import numpy as np

import settings
from packet import NoStartMarkerError, PacketIncompleteError, PacketCorruptError
import decode_fsk


START_MARKER_SAMPLES = int(len(settings.START_MARKER) * 8 / settings.TONES_PER_SECOND * settings.SAMPLE_RATE)


class AudioProcessor(Thread):
    buffer: np.ndarray
    buffer_pos: int
    processed_to_pos: int

    def __init__(self):
        super().__init__(daemon=True)
        self.buffer = np.zeros(settings.REALTIME_PROCESS_BUFFER_SIZE, dtype='i2')
        self.buffer_pos = 0
        self.processed_to_pos = 0

    def run(self):
        while True:
            self.process()
            time.sleep(settings.REALTIME_PROCESS_SLEEP)

    def update_buffer(self, buffer: np.ndarray, buffer_pos: int):
        self.buffer = buffer
        self.buffer_pos = buffer_pos

    def add_samples(self, samples: np.ndarray):
        for i in range(len(samples)):
            self.buffer[self.buffer_pos % settings.REALTIME_PROCESS_BUFFER_SIZE] = samples[i] * settings.OUTPUT_MAX
            self.buffer_pos += 1

    def get_buffer_as_array(self, start, count):
        copy = np.zeros(count, dtype='i2')
        for i in range(0, count):
            copy[i] = self.buffer[(start + i) % settings.REALTIME_PROCESS_BUFFER_SIZE]
        return copy

    def process(self):
        start_time = time.time_ns()
        print('start processing')

        # New data samples may be added while this function is running, remember current pos
        buffer_pos = self.buffer_pos
        samples = self.get_buffer_as_array(self.processed_to_pos, buffer_pos - self.processed_to_pos)

        if len(samples) < settings.REALTIME_PROCESS_MINIMUM:
            print('waiting for more samples')
            return

        print(f'processing {len(samples)} samples, from pos', self.processed_to_pos)

        try:
            message = decode_fsk.decode(samples)
            print('=> RECEIVED MESSAGE', message)
        except NoStartMarkerError:
            # No start marker was found. End of our buffer may contain start marker.
            # Keep end of buffer, the size of a start marker, and discard everything else.
            self.processed_to_pos = max(0, buffer_pos - START_MARKER_SAMPLES)
            print('=> no start marker')
        except PacketIncompleteError:
            # Packet is incomplete, wait for more data
            print('=> incomplete')
            pass
        except PacketCorruptError:
            # Packet is corrupt, discard received data by marking all as processed
            print('=> corrupt')
            self.processed_to_pos = buffer_pos

        print('done processing, took', (time.time_ns() - start_time) // 1000000, 'ms')
        self.need_process = False


class AudioReceiver:
    processor: AudioProcessor

    def __init__(self, processor: AudioProcessor):
        self.processor = processor

    def process(self, samples: np.ndarray) -> None:
        self.processor.add_samples(samples)

    def run(self):
        def callback(indata, frames, time, status):
            self.process(indata)

        with sd.InputStream(samplerate=settings.SAMPLE_RATE, latency='high', channels=1, callback=callback):
            while True:
                sd.sleep(1000)


if __name__ == '__main__':
    audio_processor = AudioProcessor()
    audio_processor.start()
    audio_receiver = AudioReceiver(audio_processor)
    audio_receiver.run()
