#!/usr/bin/python3
from player import Player
import os
import threading
import random
import channel_indexer as ci
from pprint import pprint


class TrackProgram():
    BASEPATH = "/home/david/git/old-tv/channels/"
    ADS_PATH = "/home/david/git/old-tv/ads/"
    guide = {}
    channel = 3
    program = 0
    status = {}
    # status[channel] = {
    #   type: 'ad', file: '...',
    #   chapterIndex: 0, programIndex: 0,
    #   time: 100s
    # }

    def get_cur_file(self):
        s = self.get_current_status()
        ret = ''
        if s['curType'] == 'ad':
            s['curFileIndex'] = s['curFileIndex'] % len(self.guide['ads'])

            ret = os.path.join(self.ADS_PATH,
                               self.guide['ads'][s['curFileIndex']])
        else:
            self.program = self.program % len(self.guide['channels'][self.channel])
            if 'lastChapter' not in s:
                curfidx = 0
            else:
                curfidx = s['lastChapter'][self.program]

            ret = os.path.join(self.BASEPATH,
                               str(self.channel),
                               str(self.program),
                               self.guide['channels'][self.channel][self.program][curfidx])

        return "file://" + ret

    def get_next_file(self):
        if self.get_current_status()['curType'] == 'ad':
            return self.get_random_ad()
        else:
            return self.get_next_chapter()

    def get_next_chapter(self):
        files = self.guide['channels'][self.channel][self.program]
        ret = os.path.join(self.BASEPATH,
                           str(self.channel),
                           str(self.program),
                           files[self.get_current_status()['curFileIndex']])
        return "file://" + ret

    def get_random_ad(self):
        cfi = self.get_current_status()['curFileIndex']
        return "file://" + os.path.join(self.ADS_PATH,
                                        self.guide['ads'][cfi])

    def control(self):
        data = ""
        while data != "q":
            data = input()
            if data == "next" or data == "n":
                self.player.change_uri(self.player.get_next_file())
            elif data == "snow" or data == "s":
                self.player.snow()
            elif data == "channel" or data == "c":
                self.player.channel()
            elif data.startswith("uri") or data == "u":
                self.player.set_next_file(self.get_random_ad())
            elif data == "+":
                self.set_channel(self.channel + 1)
            elif data == "-":
                self.set_channel(self.channel - 1)
            else:
                try:
                    self.player.seek(float(data))
                except Exception:
                    print("Exiting control")
                    break

    def get_current_status(self):
        # TODO: Return valid data on incomplete input
        return self.status[self.channel]

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

    def finished_playing(self):
        idx = 0
        cs = self.get_current_status()

        # Just finished an ad. Go to the next program
        if cs['curType'] == 'ad':
            self.set_current_status('curType', 'program')
            pprint(cs['lastChapter'])
            pprint(cs['lastChapter'][cs['lastProgramIndex']])
            idx = cs['lastChapter'][cs['lastProgramIndex']] + 1

        else:  # Just finished a chapter. Go to an ad
            self.set_current_status('lastProgramIndex', self.program)
            self.set_current_status('lastChapter',
                                    {self.program: cs['curFileIndex']})

            self.set_current_status('curType', 'ad')
            idx = random.randint(0, len(self.guide['ads']) - 1)

        self.set_current_status('curFileIndex', idx)
        # curFileIndex is used for get_next_file()
        new_file = self.get_next_file()
        self.player.set_next_file(new_file)
        bname = os.path.basename(new_file)

        self.set_current_status('curFileTime', 0)
        # self.set_current_status('curFileDuration', 10) # FIXME
        self.player.change_uri()

    def load_status(self):
        # TODO: Load this from a file
        return {
                2: {
                    'curType': 'ad',
                    'curFileIndex': 5,
                    'curFileTime': 10,
                    'curFileDuration': 40,
                    'lastProgramIndex': 0,
                   },
                3: {
                    'curType': 'program',
                    'curFileIndex': 5,
                    'curFileTime': 10,
                    'curFileDuration': 40,
                    'lastProgramIndex': 0,
                   },
                5: {
                    'curType': 'program',
                    'curFileIndex': 5,
                    'curFileTime': 10,
                    'curFileDuration': 40,
                    'lastProgramIndex': 0,
                   },
                }

    def set_channel(self, channel):
        self.set_current_status('curFileTime', self.player.get_cur_time())
        self.channel = min(max(channel, 1), 12)
        print("New channel:", self.channel)
        if self.channel not in self.valid_channels:
            self.player.snow()
            return

        self.player.set_next_file(self.get_cur_file())
        cs = self.get_current_status()
        self.player.change_uri(start_time=cs['curFileTime'],
                               duration=cs['curFileDuration'])

    def __init__(self):
        self.guide = ci.index()
        self.valid_channels = self.guide['channels'].keys()

        self.status = self.load_status()
        self.player = Player(on_finished=self.finished_playing)
        self.set_channel(4)
        self.set_channel(3)  # FIXME: Must call a valid channel so pads link

        t1 = threading.Thread(target=self.control)
        t1.start()
        self.player.run()
        t1.join()


if __name__ == "__main__":
    t = TrackProgram()
