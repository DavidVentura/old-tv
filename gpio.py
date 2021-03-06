#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

class Control:
    gpios = [4, 17, 27, 22]
    def __init__(self, cb):
        self.cb = cb
        GPIO.setmode(GPIO.BCM)

        for gpio in self.gpios:
            GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def start(self):
        last = -2
        gpio_to_channel = {
        	-1: -1,
        	17: 2,
        	4:  4,
        	27: 5,
        	22: 8
        }
        gpio_to_isv = {
        	-1: 0,
        	17: 1,
        	4:  2,
        	27: 3,
        	22: 4
        }
        while True:
            valid = False
            value = -1
            for g in self.gpios:
                v = GPIO.input(g)
                if v:
                    value = g
            if value != last:
                self.cb(gpio_to_isv[value])
                last = value
            time.sleep(0.05)

if __name__ == '__main__':
    c = Control(print)
    c.start()
