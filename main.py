#!/usr/bin/python3
from player import Player
import os
import threading
import random
import channel_indexer as ci
import gpio
from pprint import pprint


def sanitize_status(s, guide):
    status = s
    channels = guide['channels']
    ads = guide['ads']
    for channel in status.keys():
        if 'curType' not in status[channel]:
            status[channel]['curType'] = 'program'

        if 'curFileIndex' not in status[channel]:
            status[channel]['curFileIndex'] = 0

        if 'curFileTime' not in status[channel]:
            status[channel]['curFileTime'] = 0

        if 'curProgram' not in status[channel]:
            status[channel]['curProgram'] = 0

        if status[channel]['curType'] == 'ad':
            status[channel]['curFileIndex'] = status[channel]['curFileIndex']\
                % len(ads)
        else:
            print(channel, status[channel])
            status[channel]['curProgram'] = status[channel]['curProgram']\
                % len(channels[channel])
            status[channel]['curFileIndex'] = status[channel]['curFileIndex']\
                % len(channels[channel][status[channel]['curProgram']])

        if 'lastChapter' not in status[channel]:
            status[channel]['lastChapter'] = {}

        for program in channels[channel]:
            if program not in status[channel]['lastChapter']:
                status[channel]['lastChapter'][program] = -1

    return status


def load_status():
    # TODO: Load this from a file
    return {
            2: {
                'curType': 'ad',
                'curFileIndex': 5,
                'curFileTime': 10,
                'curFileDuration': 40,
                'lastProgramIndex': 0,
               },
            4: {
                'curType': 'program',
                'curProgram': 0,
                'curFileTime': 10,
                'curFileDuration': 40,
                'lastProgramIndex': 0,
               },
            5: {
                'curType': 'program',
                'curProgram': 0,
                'curFileTime': 10,
                'curFileDuration': 40,
                'lastProgramIndex': 0,
               },
            8: {}
            }


class TrackProgram():
    BASEPATH = ci.BASEPATH
    ADS_PATH = ci.ADS_PATH
    BLANK_PATH = ci.BLANK_PATH
    guide = {}
    channel = 0
    program = 0
    status = {}

    def get_cur_file(self):
        s = self.get_current_status()
        ret = ''
        if s['curType'] == 'ad':
            ret = os.path.join(self.ADS_PATH,
                               self.guide['ads'][s['curFileIndex']])
        else:
            curfidx = s['lastChapter'][self.program]
            if curfidx == -1:
                curfidx = 0
                # FIXME: What do I do about this?
                # Setting -1 as having not played a single file
                # Destroys this part.

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
            if data == "s":
                pprint(self.status)
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

    def update_duration(self, duration):
        self.set_current_status('curFileDuration', duration)

    def finished_playing(self):
        if self.channel in self.valid_channels:
            idx = 0
            cs = self.get_current_status()
            # Just finished an ad. Go to the next program
            if cs['curType'] == 'ad':
                self.set_current_status('curType', 'program')
                if 'lastChapter' in cs:
                    next_program = (cs['lastProgramIndex'] + 1) %\
                        len(self.guide['channels'][self.channel])

                    idx = cs['lastChapter'][next_program] + 1 % \
                        len(self.guide['channels'][self.channel][self.program])
                    # Taking index from lastProgramIndex..
                    # should take from the next program

                    self.program = (self.program + 1) % \
                        len(self.guide['channels'][self.channel])
                    self.set_current_status('curProgram', self.program)

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

        self.set_current_status('curFileTime', 0)
        # self.set_current_status('curFileDuration', 10) # FIXME
        self.player.change_uri()

    def set_channel(self, channel):
        print("Asked to set", channel)
        channel = min(max(channel, 1), 12)
        if self.channel == channel:
            print("Aborting, asked to switch to current channel")
            return

        self.set_current_status('curFileTime', self.player.get_cur_time())
        self.channel = channel
        print("New channel:", self.channel)
        if self.channel not in self.valid_channels:
            self.player.snow()
            return

        cs = self.get_current_status()
        self.program = cs['curProgram']
        self.player.set_next_file(self.get_cur_file())
        if 'curFileDuration' not in cs or cs['curFileTime'] == 0:
            print('curFileDuration' not in cs)
            self.player.change_uri()
        else:
            self.player.change_uri(start_time=cs['curFileTime'],
                                   duration=cs['curFileDuration'])

    def __init__(self):
        self.guide = ci.index()
        # FIXME: Sorts... poorly
        self.valid_channels = self.guide['channels'].keys()

        self.status = sanitize_status(load_status(), self.guide)

        self.player = Player(blank_uri="file://" + self.BLANK_PATH,
                             on_finished=self.finished_playing,
                             on_duration=self.update_duration)

        g = gpio.Control(self.set_channel)
        t1 = threading.Thread(target=self.control)
        t1.start()
        self.player.run()
        g.stop()
        t1.join()


if __name__ == "__main__":
    t = TrackProgram()
