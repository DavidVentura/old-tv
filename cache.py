#!/usr/bin/env python3
import threading
import os


class Cache:
    MB = 1024*1024
    CACHE_SIZE = 2*MB
    cached_paths = []

    def __init__(self):
        return

    def _cache(self, path):
        if path in self.cached_paths:
            print('%s already in cache')
            return

        self.cached_paths.append(path)
        print('reading %s' % path)
        f = open(path, 'rb')
        f.read(self.CACHE_SIZE)
        f.close()
        print('finished reading')

    def add(self, path):
        if not os.path.isfile(path):
            print("Invalid file %s" % path)
            return
        t1 = threading.Thread(target=self._cache, args=(path,))
        t1.daemon = True
        t1.start()
