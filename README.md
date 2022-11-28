## Usage

1. MFSK - Transfer multiple bits in a single tone using multiple frequencies (4, 16 or 256 frequencies for 2, 4 or 8 bits respectively). Uses Fourier transform to find frequency for audio signal in small windows. Write or play audio for a message using `encode.py`. Decode from file using `decode_mfsk.py`. Decode from live audio input using `decode_mfsk_realtime.py`. Set `MFSK = True` in `settings.py`.
2. FSK - Transfer data using only two frequencies (single bit), but at much higher rate. Write or play audio for a message using `encode.py`. Decode from file using `decode_fsk.py`. Decoding from live audio is not possible, yet. Set `MFSK = False` in `settings.py`.

## Creating network interface

```
sudo ip tuntap add dev tun0 mode tun user $(id -u) group $(id -g)
sudo ip link set dev tun0 up
```

On machine 1:
```
sudo ip addr replace dev tun0 local 172.30.0.1 peer 172.30.0.2
```

On machine 2:
```
sudo ip addr replace dev tun0 local 172.30.0.2 peer 172.30.0.1
```

Removing the adapter:
```
sudo ip tuntap del dev tun0 mode tun
```

## Credits

Original MFSK code (commit e7d2e7d) by [Juulpy](https://github.com/Juulpy)
Networking code inspired by [dsptunnel](https://github.com/50m30n3/dsptunnel) by 50m30n3 (C) 2011, licensed under GPL
