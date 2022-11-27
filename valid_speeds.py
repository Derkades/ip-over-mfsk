import settings

if __name__ == '__main__':
    for i in range(1, 2000):
        if settings.SAMPLE_RATE / i == settings.SAMPLE_RATE // i:
            print(i)
