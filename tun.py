from cgi import print_directory
import fcntl
import struct
import os


def tun_open(tun_name: str):
    # ifreq struct (see /usr/include/linux/if.h)

    # 16 byte char[]
    ifrn_name = tun_name.encode()
    # 2 byte short set to IFF_TUN | IFF_NO_PI, defined in /usr/include/linux/if_tun.h
    ifru_flags = 0x0001 | 0x1000

    ioctl_arg = struct.pack('16sh', ifrn_name, ifru_flags)

    tun_dev = os.open('/dev/net/tun', os.O_RDWR)

    # TUNSETIFF is _IOW('T', 202, int), see /usr/include/linux/if_tun.h
    # The magic number was found by writing a C program that prints TUNSETIFF
    fcntl.ioctl(tun_dev, 0x400454ca, ioctl_arg)

    return tun_dev


if __name__ == '__main__':
    tun_dev = tun_open('tun0')
    print(os.read(tun_dev, 2048))
    os.close(tun_dev)
