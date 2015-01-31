# -*- coding: utf-8 -*-
import sys
import os, json

ROOT = os.path.dirname(sys.modules["__main__"].sys.argv[0])
searcherObject = {}
searcher = 'KickAssSo'
if ROOT + os.sep + 'resources' + os.sep + 'contenters' not in sys.path:
    sys.path.insert(0, ROOT + os.sep + 'resources' + os.sep + 'contenters')
searcherObject[searcher] = getattr(__import__(searcher), searcher)()

print str(searcherObject[searcher].get_info('http://kickass.so/greys-anatomy-s11e09-hdtv-x264-lol-ettv-t10144556.html'))

