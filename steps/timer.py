import time


class Timer:
    running = False

    def __init__(self, interval, callback, arg=None):
        self.interval = max(interval, 5)
        assert callable(callback)
        self.callback = callback
        self.arg = arg

    def start(self):
        self.running = True
        while self.running:
            time.sleep(self.interval)
            if self.arg is not None:
                if callable(self.arg):
                    self.callback(self.arg())
                else:
                    self.callback(self.arg)
            else:
                self.callback()

    def stop(self):
        self.running = False


if __name__ == '__main__':
    t = Timer(5, print)
    t.start()
