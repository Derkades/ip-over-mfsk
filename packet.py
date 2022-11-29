import struct

import crc16
import settings
import smallgzip


class BasePacketDecodeError(Exception):
    pass


class NoStartMarkerError(BasePacketDecodeError):
    """
    No start marker was found. Most of the buffer can be discarded, except for
    the last part which may contain a partial start marker
    """
    pass


class PacketIncompleteError(BasePacketDecodeError):
    """
    Packet is not fully received yet, either because the buffer is too small
    to contain header bytes, or the buffer is smaller than the expected
    packet size. Wait for the buffer to fill more, and try to unpack again.
    """
    pass


class PacketCorruptError(BasePacketDecodeError):
    """
    Packet is corrupt. Buffer should be discarded. There is no point in trying
    to unpack again.
    """
    pass


class PacketChecksumError(PacketCorruptError):
    def __init__(self, checksum_header: int, checksum_message: int, message: bytes):
        super().__init__(f'Expected checksum {checksum_header} but message has checksum {checksum_message}. Message: {message}')


def pack(data: bytes) -> bytes:
    if settings.DO_COMPRESS:
        print('original size:', len(data))
        original_size = len(data)
        data = smallgzip.compress(data)
        print(f'compressed from {original_size} to {len(data)}')

    if len(data) > settings.MAX_PACKET_SIZE:
        raise ValueError('message too long')

    checksum = crc16.crc16(data)
    header_bytes = struct.pack('>HH', len(data), checksum)

    assert len(header_bytes) == settings.PACKET_HEADER_SIZE

    return header_bytes + data


def get_size(data: bytes) -> int:
    if len(data) < settings.PACKET_HEADER_SIZE:
        raise PacketIncompleteError('Data smaller than header size')

    size = struct.unpack('>H', data[:2])

    if size > settings.MAX_PACKET_SIZE:
        raise PacketCorruptError('Size greater than maximum packet size')

    return size


def unpack(data: bytes) -> bytes:
    assert len(data) > settings.PACKET_HEADER_SIZE
    header_bytes = data[:settings.PACKET_HEADER_SIZE]
    message_bytes = data[settings.PACKET_HEADER_SIZE:]

    size, checksum = struct.unpack('>HH', header_bytes)

    if size > settings.MAX_PACKET_SIZE:
        raise PacketCorruptError('Packet too large')

    if size > len(message_bytes):
        raise PacketIncompleteError('Packet header claims size ' + str(size) + ' but we have only received ' + str(len(message_bytes) - 4))

    message_bytes = message_bytes[:size]

    message_checksum = crc16.crc16(message_bytes)

    if checksum != message_checksum:
        raise PacketChecksumError(checksum, message_checksum, message_bytes)

    if settings.DO_COMPRESS:
        message_bytes = smallgzip.decompress(message_bytes)

    return message_bytes
