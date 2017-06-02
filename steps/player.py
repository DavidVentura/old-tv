#!/usr/bin/env python3
from seamless_selector_audio import Player
from gpio import Control
from config import Config
from timer import Timer
import threading
import time


if __name__ == '__main__':
    cfg = Config()
    p = Player(cfg.status, cfg.sources)
    t1 = threading.Thread(target=p.start)
    t1.daemon = True
    t1.start()

    time.sleep(1)

    c = Control(p.toggle)
    t2 = threading.Thread(target=c.start)
    t2.daemon = True
    t2.start()

    t = Timer(60, cfg.save_status, p.update_timings)
    t3 = threading.Thread(target=t.start)
    t3.daemon = True
    t3.start()

    t1.join()

    c.stop()
    t2.join()

    t.stop()
    t3.join()
    print("end control")
