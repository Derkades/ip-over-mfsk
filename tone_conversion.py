import settings
import gray


def bytes_to_tones(data: bytes) -> list[int]:
    tones = []

    if not settings.MFSK or settings.TONE_BITS == 1:
        for byte in data:
            tones.append(byte >> 7 & 1)
            tones.append(byte >> 6 & 1)
            tones.append(byte >> 5 & 1)
            tones.append(byte >> 4 & 1)
            tones.append(byte >> 3 & 1)
            tones.append(byte >> 2 & 1)
            tones.append(byte >> 1 & 1)
            tones.append(byte >> 0 & 1)
    elif settings.TONE_BITS == 2:
        for byte in data:
            tones.append(byte >> 6 & 0b11)
            tones.append(byte >> 4 & 0b11)
            tones.append(byte >> 2 & 0b11)
            tones.append(byte >> 0 & 0b11)
    elif settings.TONE_BITS == 4:
        for byte in data:
            tones.append(byte >> 4)
            tones.append(byte & 0xF)
    elif settings.TONE_BITS == 8:
        tones = list(data)
    else:
        raise ValueError()

    if settings.MFSK and settings.USE_GRAY_ENCODING:
        for i, tone in enumerate(tones):
            tones[i] = gray.to_gray(tone)

    return tones


def tones_to_bytes(tones: list[int]):
    if settings.MFSK:
        # TODO Gray encode/decode bytes, not tones (and not only for MFSK)
        if settings.USE_GRAY_ENCODING:
            for i, gray_tone in enumerate(tones):
                tones[i] = gray.from_gray(gray_tone)

        if settings.TONE_BITS not in {1, 2, 4, 8}:
            raise ValueError()

        tone_bits = settings.TONE_BITS
    else:
        tone_bits = 1

    byte_list = []
    tones_per_byte = 8 // tone_bits
    for i in range(0, len(tones) // tones_per_byte * tones_per_byte, tones_per_byte):
        b = 0
        for j in range(tones_per_byte):
            b |= tones[i + j] << (8 - (j+1)*tone_bits)
        byte_list.append(b)

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
