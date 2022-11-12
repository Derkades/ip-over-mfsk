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
