def bytes_to_int4list(data_8bit: bytes) -> list[int]:
    int4list = []
    for byte in data_8bit:
        int4list.append(byte >> 4)
        int4list.append(byte & 0xF)
    return int4list


def int4list_to_bytes(int4list: list[int]) -> bytes:
    byte_list = []
    for i in range(0, len(int4list), 2):
        byte_list.append((int4list[i] << 4) ^ int4list[i + 1])
    return bytes(byte_list)
