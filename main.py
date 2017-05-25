#!/usr/bin/python3
from player import Player
import cache
import os
import threading
import channel_indexer as ci
import gpio
import json
import time
from pprint import pprint


def list_saves():
    ret = []
    for f in os.listdir(ci.cwd):
        if f.endswith('json') and os.path.getsize(f) > 5:
            # Consider the possibility of a file writing '{}'
            ret.append(f)
    return ret


def newest_file(xs):
    ltime = None
    ret = None
    for f in xs:
        t = os.path.getmtime(f)
        if ltime is None or t > ltime:
            # print("%s is newer than %s" % (f, ret))
            ltime = t
            ret = f
    return ret


def sanitize_status(s, guide):
    status = s
    for channel in guide.keys():
        if channel not in status:
            status[channel] = {}

        if 'curFileIndex' not in status[channel]:
            status[channel]['curFileIndex'] = 0

        if 'curFileTime' not in status[channel]:
            status[channel]['curFileTime'] = 0

    return status


def keys_to_int(obj):
    keys = obj.keys()
    for k in keys:
        if type(k) == str:
            obj[int(k)] = obj[k]
            del obj[k]
    return obj


def load_status(fname):
    data = {}
    try:
        with open(fname, 'r') as f:
            data = json.loads(f.read())
            data = keys_to_int(data)
    except Exception as e:
        print(e)

    return data


def save_status(status):
    seconds = str(int(round(time.time())))
    path = os.path.join(ci.cwd, seconds + ".json")
    print("Saving status to ", path)
    pprint(status)
    with open(path, "w") as f:
        f.write(json.dumps(status, sort_keys=False, indent=4))


class TrackProgram():
    BASEPATH = ci.BASEPATH
    ADS_PATH = ci.ADS_PATH
    BLANK_PATH = ci.BLANK_PATH
    guide = {}
    channel = 0
    status = {}

    def get_cur_file(self, channel):
        s = self.get_current_status(channel)
        ret = os.path.join(self.BASEPATH,
                           str(channel),
                           self.guide[channel][s['curFileIndex']])

        return "file://" + ret

    def get_next_file(self, channel):
        files = self.guide[channel]
        ret = os.path.join(self.BASEPATH,
                           str(channel),
                           files[self.get_current_status(channel)['curFileIndex']])
        return "file://" + ret

    def chaos(self):
        last = 0
        t = sorted([k for k in self.guide.keys()])
        print(t)
        self.player.set_next_file('file://'+'/home/david/git/old-tv/channels/2/0/mtn-pp101.avi.mp4',0)
        while True:
            time.sleep(5)
            self.player.change_channel(last)
            last = (last + 1) % len(t)

    def control(self):
        data = ""
        while True:
            data = input()
            if data == "s":
                pprint(self.status)
            elif data == "+":
                self.set_channel(self.channel + 1)
            elif data == "-":
                self.set_channel(self.channel - 1)
            elif data == "q":
                self.set_current_status('curFileTime', self.player.get_cur_time())
                save_status(self.status)
            else:
                try:
                    self.player.seek(float(data))
                except Exception:
                    print("Invalid")

    def get_current_status(self, channel):
        # TODO: Return valid data on incomplete input
        return self.status[channel]

    def set_current_status(self, k, v):
        if self.channel not in self.valid_channels:
            print("This is not a valid channel to set status!")
            return
        if type(v) is dict:
            for key in v.keys():
                if k not in self.status[self.channel]:
                    print('creating channel obj key')
                    self.status[self.channel][k] = {}
                self.status[self.channel][k][key] = v[key]
                print("Setting channel %d.%s.%s to %s" %
                      (self.channel, k, key, v[key]))
        else:
            print("Setting channel %d.%s to %s" % (self.channel, k, v))
            self.status[self.channel][k] = v

    def update_duration(self, duration):
        self.set_current_status('curFileDuration', duration)

    def finished_playing(self, channel):
        print("finished playing!!")
        if self.channel in self.valid_channels:
            print("valid channel")
            idx = 0
            cs = self.get_current_status(channel)
            idx = cs['curFileIndex']
            self.set_current_status('curFileIndex', idx + 1)
            # curFileIndex is used for get_next_file()
            new_file = self.get_next_file(channel)
            self.player.set_next_file(new_file, self.valid_channels.index(channel))

        self.set_current_status('curFileTime', 0)
        self.player.change_uri()

    def set_channel(self, channel):
        print("Asked to set", channel)
        channel = min(max(channel, 1), 12)
        if self.channel == channel:
            print("Aborting, asked to switch to current channel")
            return
        if self.player.BUSY:
            print("Player is BUSY!!")
            return

        self.set_current_status('curFileTime', self.player.get_cur_time())
        self.channel = channel
        print("New channel:", self.channel)
        if self.channel not in self.valid_channels:
            print("Snow")
            self.player.snow()
            return

        cs = self.get_current_status(channel)
        self.player.set_next_file(self.get_cur_file(channel), self.valid_channels.index(self.channel))
        if 'curFileDuration' not in cs or cs['curFileTime'] == 0:
            print('curFileDuration' not in cs)
            self.player.change_uri()
        else:
            self.player.change_uri(start_time=cs['curFileTime'],
                                   duration=cs['curFileDuration'])

    def __init__(self):
        self.guide = ci.create_playlist(ci.index())
        self.guide = { 2: self.guide[2] }
        self.valid_channels = sorted(list(self.guide.keys()))

        statusfile = ''
        statusfile = os.path.join(ci.cwd, "1492733314.json")
        statusfile = newest_file(list_saves())
        loaded = load_status(statusfile)
        self.status = sanitize_status(loaded, self.guide)

        self.player = Player(blank_uri="file://" + self.BLANK_PATH,
                             on_finished=self.finished_playing,
                             on_duration=self.update_duration,
                             channels=len(self.valid_channels))

        g = gpio.Control(self.set_channel)
        t1 = threading.Thread(target=self.control)
        t1.daemon = True
        t1.start()
        t2 = threading.Thread(target=self.chaos)
        t2.daemon = True
        t2.start()
        self.player.run()
        g.stop()
        t1.join()


if __name__ == "__main__":
    tp = TrackProgram()
