#include <stdio.h>
#include <sys/ioctl.h>
#include <linux/if_tun.h>

int main() {
    printf("%x\n", TUNSETIFF);
}
