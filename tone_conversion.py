import settings
import gray

def bytes_to_tones(data: bytes) -> list[int]:
    tones = []
    if settings.TONE_BITS == 4:
        for byte in data:
            tones.append(byte >> 4)
            tones.append(byte & 0xF)
    elif settings.TONE_BITS == 8:
        tones = list(data)
    else:
        raise ValueError

    for i, tone in enumerate(tones):
        tones[i] = gray.to_gray(tone)

    return tones

def tones_to_bytes(tones: list[int]):
    for i, gray_tone in enumerate(tones):
        tones[i] = gray.from_gray(gray_tone)

    byte_list = []
    if settings.TONE_BITS == 4:
        for i in range(0, len(tones) // 2 * 2, 2):
            byte_list.append((tones[i] << 4) ^ tones[i + 1])
    elif settings.TONE_BITS == 8:
        byte_list = tones
    else:
        raise ValueError

    return bytes(byte_list)


if __name__ == '__main__':
    test_message = b'testing testing 123'

    for tone_bits in [4, 8]:
        print('tone_bits:', tone_bits)
        settings.TONE_BITS = tone_bits
        tones = bytes_to_tones(test_message)
        print('tones:', tones)
        restored = tones_to_bytes(tones)
        print('restored:', restored)
        assert restored == test_message
        print()
