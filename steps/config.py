#!/usr/bin/python3
import os
import json
import time
from pprint import pprint


class Config:
    path = ''
    sources = []
    status = {}
    initial_values = {
        '0': 0,
        '1': 0,
        '2': 0,
        '3': 0,
        '4': 0,
    }

    def list_saves(self):
        ret = []
        for f in os.listdir(self.path):
            if f.endswith('json') and os.path.getsize(f) > 5:
                # Consider the possibility of a file writing '{}'
                ret.append(f)
        return ret

    def newest_file(self, xs):
        ltime = None
        ret = None
        for f in xs:
            t = os.path.getmtime(f)
            if ltime is None or t > ltime:
                # print("%s is newer than %s" % (f, ret))
                ltime = t
                ret = f
        return ret

    def load_status(self, fname):
        data = self.initial_values
        try:
            with open(fname, 'r') as f:
                data = json.loads(f.read())
        except Exception as e:
            # print(e)
            pass
        return data

    def save_status(self, status):
        seconds = str(int(round(time.time())))
        path = os.path.join(self.path, seconds + ".json")
        print("Saving status to ", path)
        with open(path, "w") as f:
            f.write(json.dumps(status, sort_keys=False, indent=4))

    def __init__(self):
        if not os.path.isdir(self.path):
            self.path = os.getcwd()
        sourcesfile = os.path.join(self.path, "sources.json")

        statusfile = os.path.join(self.path, "1492733314.json")
        statusfile = self.newest_file(self.list_saves())
        statusfile = ''
        self.status = self.load_status(statusfile)
        self.sources = self.load_status(sourcesfile)


if __name__ == "__main__":
    c = Config()
    pprint(c.status)
