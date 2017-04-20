#!/usr/bin/env python3
import os

cwd = os.path.dirname(os.path.realpath(__file__))
BASEPATH = os.path.join(cwd, "channels/")
ADS_PATH = os.path.join(cwd, "ads/")
BLANK_PATH = os.path.join(cwd, 'noise/noise.mp4')


def get_directories(path):
    ret = []
    for f in os.listdir(path):
        fullpath = os.path.join(path, f)
        if os.path.isdir(fullpath):
            ret.append(f)

    return ret


def valid_ext(path):
    return (path.endswith("mp4") or path.endswith("mkv"))


def get_files(path):
    ret = []
    for f in os.listdir(path):
        fullpath = os.path.join(path, f)
        if os.path.isfile(fullpath) and valid_ext(fullpath):
            ret.append(f)

    # Sorting the output is very important
    # As the playback will be ordered.
    return sorted(ret)


def index():
    channels = get_directories(BASEPATH)
    data = {}
    for c in channels:
        data[int(c)] = {}
        channel_path = os.path.join(BASEPATH, c)
        for p in get_directories(channel_path):
            program_path = os.path.join(channel_path, p)
            data[int(c)][int(p)] = get_files(program_path)

    ads = get_files(ADS_PATH)
    return {'ads': ads, 'channels': data}


if __name__ == '__main__':
    print(index())
