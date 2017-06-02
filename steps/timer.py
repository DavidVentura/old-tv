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
            # Wait up to 1 second to be interrupted
            for _ in range(self.interval):
                if not self.running:
                    return
                time.sleep(1)
            print("I'm about to call my callback", flush=True)
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
