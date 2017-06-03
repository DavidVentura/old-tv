#!/usr/bin/env python3
from seamless_selector_audio import Player
from gpio import Control
from config import Config
from timer import Timer
import subprocess
import threading
import time


counter = 0
MAX_COUNT = 5


def shutdown(val):
    global counter
    print('shutdown val %s' % val)
    if val == 0 or val == '0':
        counter += 1
    else:
        counter = 0
    print('counter %d' % counter)

    if counter >= MAX_COUNT:
        print('powering off')
        subprocess.Popen(['sudo', 'poweroff'])

if __name__ == '__main__':
    cfg = Config()
    print(cfg.status, flush=True)
    p = Player(cfg.status, cfg.sources)
    t1 = threading.Thread(target=p.start)
    t1.daemon = True
    t1.start()

    time.sleep(1)

    c = Control(p.toggle)
    t2 = threading.Thread(target=c.start)
    t2.daemon = True
    t2.start()

    t = Timer(300, cfg.save_status, p.update_timings)
    t3 = threading.Thread(target=t.start)
    t3.daemon = True
    t3.start()

    ti = Timer(5, shutdown, p.get_current_channel)
    t4 = threading.Thread(target=ti.start)
    t4.daemon = True
    t4.start()

    t1.join()

    c.stop()
    t2.join()

    t.stop()
    t3.join()
    print("end control")
