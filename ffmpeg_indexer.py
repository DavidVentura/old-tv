#!/usr/bin/env python3
import os
import random
import os, fnmatch
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


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result[0]


if __name__ == '__main__':
    import sys
    from pprint import pprint
    d = create_playlist(index())
    if len(sys.argv) != 2:
        print("arg: channel id in %s" % d.keys())
        sys.exit(1)

    channel = int(sys.argv[1])
    files = d[channel]
    out = []
    command = "ffmpeg -hide_banner -loglevel error -stats"
    l = len(files)
    for f in files:
        newpath = find(f, "./")
        newpath = newpath.replace("'", "'\\''")
        command = command + (" -i '%s'" % newpath)

    #-filter_complex '[0:v] setsar=sar=1/1[sarfix0]; [1:v] setsar=sar=1/1[sarfix1]; [sarfix0] [0:a] [sarfix1] [1:a] concat=n=2:v=1:a=1 [v] [a]' -map '[v]' -map '[a]' -c:v libx264 -c:a libmp3lame -ac 1 -preset:v veryfast -y channel5.mp4
    l = min(l, 184) #FIXME ??
    fc = " -filter_complex '"
    concat = ''
    for i in range(0, l):
        # command = command + '[%d:0] [%d:1] ' % (i, i)
        fc += '[%d:v] setsar=sar=1/1[sarfix%d]; ' % (i, i)
        concat += '[sarfix%d] [%d:a] ' % (i, i)

    fc = fc + concat + 'concat=n=%d:v=1:a=1 [v] [a]\'' % l
    command = command + fc + " -map '[v]' -map '[a]' -c:v libx264 -c:a libmp3lame -ac 1 -preset:v veryfast -profile:v baseline -movflags +faststart -g 12 -r 24 -y channel%d.mp4" % channel
    print(command)
    # pprint(index())
