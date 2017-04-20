#!/usr/bin/env python3
import platform
import threading
import time
if platform.machine() != 'x86_64':
    import RPi.GPIO as GPIO


class Control:
    def __init__(self, cb):
        if platform.machine() == 'x86_64':
            return
        GPIO.setmode(GPIO.BCM)
        self.running = True
        self.cb = cb
        self.gpios = [4, 17, 27, 22]

        self.gpio_to_channel = {
            -1: -1,
            17: 2,
            4: 4,
            27: 5,
            22: 8
        }

        for gpio in self.gpios:
            GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        self.t1 = threading.Thread(target=self.control)
        self.t1.daemon = True
        self.t1.start()

    def control(self):
        print("starting to sleep")
        time.sleep(0.1)
        print("slept")
        last = -2
        while self.running:
            value = -1
            for g in self.gpios:
                v = GPIO.input(g)
                if v:
                    value = g
            if value != last:
                self.cb(self.gpio_to_channel[value])
                last = value
            time.sleep(0.05)

    def stop(self):
        if platform.machine() == 'x86_64':
            return
        self.running = False
        print("waiting to join")
        self.t1.join()


if __name__ == '__main__':
    c = Control(print)
