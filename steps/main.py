#!/usr/bin/env python3
from seamless_selector_audio import Player
from gpio import Control
import threading
import time

if __name__ == '__main__':
    p = Player()
    t1 = threading.Thread(target=p.start)
    t1.daemon = True
    t1.start()

    time.sleep(1)

    c = Control(p.toggle)
    t2 = threading.Thread(target=c.start)
    t2.daemon = True
    t2.start()

    t1.join()
    c.stop()
    t2.join()
    print("end control")
