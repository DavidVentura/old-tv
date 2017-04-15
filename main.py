#!/usr/bin/python3
from player import Player
import os
import threading
import random
import channel_indexer as ci
from pprint import pprint

BASEPATH = "/home/david/git/old-tv/channels/"
ADS_PATH = "/home/david/git/old-tv/ads/"


def get_next_file(guide, channel, program):
    files = guide[channel][program]
    ret = os.path.join(BASEPATH,
                       str(channel),
                       str(program),
                       random.choice(files))
    return "file://" + ret


def get_random_ad(ads):
    return "file://" + os.path.join(ADS_PATH, random.choice(ads))


def control(target, ads):
    data = ""
    while data != "q":
        data = input()
        if data == "next" or data == "n":
            target.change_uri(target.get_next_file())
        elif data == "snow" or data == "s":
            target.snow()
        elif data == "channel" or data == "c":
            target.channel()
        elif data.startswith("uri") or data == "u":
            target.set_next_file(get_random_ad(ads))
        else:
            try:
                target.seek(float(data))
            except Exception:
                print("Exiting control")
                break


def main():
    data = ci.index()
    ads = data["ads"]
    channels = data["channels"]
    # pprint(channels)
    p = Player()
    p.set_next_file(get_next_file(channels, 3, 1))
    p.change_uri()

    t1 = threading.Thread(target=control, args=(p, ads))
    t1.start()
    p.run()
    t1.join()


if __name__ == "__main__":
    main()
