import settings
import gray


def bytes_to_tones(data: bytes) -> list[int]:
    byte_list = list(data)

    if settings.USE_GRAY_ENCODING:
        for i, byte in enumerate(byte_list):
            byte_list[i] = gray.to_gray(byte)

    tones = []

    if not settings.MFSK or settings.TONE_BITS == 1:
        for byte in byte_list:
            tones.append(byte >> 7 & 1)
            tones.append(byte >> 6 & 1)
            tones.append(byte >> 5 & 1)
            tones.append(byte >> 4 & 1)
            tones.append(byte >> 3 & 1)
            tones.append(byte >> 2 & 1)
            tones.append(byte >> 1 & 1)
            tones.append(byte >> 0 & 1)
    elif settings.TONE_BITS == 2:
        for byte in byte_list:
            tones.append(byte >> 6 & 0b11)
            tones.append(byte >> 4 & 0b11)
            tones.append(byte >> 2 & 0b11)
            tones.append(byte >> 0 & 0b11)
    elif settings.TONE_BITS == 4:
        for byte in byte_list:
            tones.append(byte >> 4)
            tones.append(byte & 0xF)
    elif settings.TONE_BITS == 8:
        tones = byte_list
    else:
        raise ValueError()

    return tones


def tones_to_bytes(tones: list[int]):
    if settings.MFSK:
        assert settings.TONE_BITS in {1, 2, 4, 8}
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

    if settings.USE_GRAY_ENCODING:
        for i, byte in enumerate(byte_list):
            byte_list[i] = gray.from_gray(byte)

    return bytes(byte_list)


if __name__ == '__main__':
    test_message = b'testing testing 123'
    settings.MFSK = True
    for use_gray in [True, False]:
        settings.USE_GRAY_ENCODING = use_gray
        print('gray:', use_gray)
        for tone_bits in [1, 2, 4, 8]:
            print('tone_bits:', tone_bits)
            settings.TONE_BITS = tone_bits
            tones = bytes_to_tones(test_message)
            print('tones:', tones)
            restored = tones_to_bytes(tones)
            print('restored:', restored)
            assert restored == test_message
