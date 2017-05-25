#!/usr/bin/env python3
import os
import random
from itertools import cycle, islice

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


def create_playlist(data):
    channels = data['channels']
    ads = data['ads']

    out = {}
    for c in channels:
        out[c] = []
        tupled = tuple(channels[c][v] for v in channels[c])
        interleaved = roundrobin(*tupled)
        for program in interleaved:
            out[c].append(program)
            out[c].append(random.choice(ads))

    return out


def roundrobin(*iterables):
    "roundrobin('ABC', 'D', 'EF') --> A D E B F C"
    # Recipe credited to George Sakkis
    pending = len(iterables)
    nexts = cycle(iter(it).__next__ for it in iterables)
    while pending:
        try:
            for next in nexts:
                yield next()
        except StopIteration:
            pending -= 1
            nexts = cycle(islice(nexts, pending))


if __name__ == '__main__':
    from pprint import pprint
    d = create_playlist(index())
    print(d)
    # pprint(index())
