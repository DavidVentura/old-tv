#!/usr/bin/python3
from player import Player
import os
import threading
import random

BASEPATH = "/home/david/git/old-tv/channels/3/0/"
exiting = False


def get_next_file(files):
    ret = "file://" + os.path.join(BASEPATH, random.choice(files))
    return ret


def control(target):
    global exiting
    data = ""
    while data != "q":
        data = input()
        if data == "next" or data == "n":
            target.change_uri(target.get_next_file())
        elif data == "snow" or data == "s":
            target.snow()
        elif data == "channel" or data == "c":
            target.channel()
        else:
            try:
                target.seek(float(data))
            except Exception:
                print("Exiting control")
                break
    exiting = True


def main():
    files = [f for f in os.listdir(BASEPATH)
             if os.path.isfile(os.path.join(BASEPATH, f)) and
             (f.endswith("mp4") or f.endswith("mkv"))]

    p = Player()
    p.set_next_file(get_next_file(files))
    p.change_uri()

    t1 = threading.Thread(target=control, args=(p,))
    t1.start()
    p.run()
    t1.join()


if __name__ == "__main__":
    main()
