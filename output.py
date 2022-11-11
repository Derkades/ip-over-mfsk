import sounddevice as sd

import mfsk_encode

if __name__ == '__main__':
    i = 0
    while True:
        message = b'test' + str(i).encode()
        samples = mfsk_encode.data_to_audio(message)
        sd.play(samples)
        sd.wait()
        i += 1
