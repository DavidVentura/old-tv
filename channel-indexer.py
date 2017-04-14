#!/usr/bin/env python3
import os

BASEPATH = "/home/david/git/old-tv/channels/"
ADS_PATH = "/home/david/git/old-tv/ads/"


def get_directories(path):
    ret = []
    for f in os.listdir(path):
        fullpath = os.path.join(path, f)
        if os.path.isdir(fullpath):
            ret.append(f)

    return ret


def get_files(path):
    ret = []
    for f in os.listdir(path):
        fullpath = os.path.join(path, f)
        if os.path.isfile(fullpath):
            ret.append(f)

    return sorted(ret)


channels = get_directories(BASEPATH)
data = {}
for c in channels:
    data[c] = {}
    channel_path = os.path.join(BASEPATH, c)
    for p in get_directories(channel_path):
        program_path = os.path.join(channel_path, p)
        data[c][p] = get_files(program_path)

ads = get_files(ADS_PATH)
print(data)
print(ads)
