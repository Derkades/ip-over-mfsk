import gzip

# https://www.rfc-editor.org/rfc/rfc1952

# We can safely remove some bytes from the compressed gzip data to save space.
# Header:
#   2 bytes for magic: 0x1f8b
#   1 byte for compression method: 0x08 for deflate
#   1 byte for header flags: always seems to be 0x00
#   4 bytes timestamp: doesn't matter anyway, just set to 0
#   1 byte for compression flags: python sets to 0x02, meaning slow compression algorithm
#   1 byte for OS id (python uses 0xff for unknown)
# Trailer:
#   4 bytes for CRC32, must be left as-is (however we don't need our own checksum anymore)
#   4 bytes for size, can be reduced to 2 bytes since our payloads will never exceed 65535 bytes


def compress(data: bytes) -> bytes:
    compressed = gzip.compress(data)
    return compressed[10:-2]


def decompress(data: bytes) -> bytes:
    magic = b'\x1f\x8b'
    comp_method = b'\x08'
    header_flags = b'\0'
    timestamp = b'\0\0\0\0'
    comp_flags = b'\x02'
    os_id = b'\xff'
    header = magic + comp_method + header_flags + timestamp + comp_flags + os_id
    return gzip.decompress(header + data + b'\0\0')


if __name__ == '__main__':
    test_message = b'hello world'
    standard_compressed = gzip.compress(test_message)
    compressed = compress(test_message)
    print('standard compressed', len(standard_compressed), standard_compressed)
    print('compressed', len(compressed), compressed)
    decompressed = decompress(compressed)
    assert decompressed == test_message
    print(decompressed)
