# -*- coding: utf-8 -*-
import sys
import os, json, re
from BeautifulSoup import BeautifulSoup

ROOT = os.path.dirname(sys.modules["__main__"].sys.argv[0])
searcherObject = {}
searcher = 'KickAssSo'
if ROOT + os.sep + 'resources' + os.sep + 'contenters' not in sys.path:
    sys.path.insert(0, ROOT + os.sep + 'resources' + os.sep + 'contenters')
searcherObject[searcher] = getattr(__import__(searcher), searcher)()

#print str(searcherObject[searcher].get_info('http://kickass.so/greys-anatomy-s11e09-hdtv-x264-lol-ettv-t10144556.html'))


x='<a href="http://swesub.tv/action/">Action</a></li><li><a href="http://swesub.tv/animerat/">Animerat</a></li><li><a href="http://swesub.tv/dans/">Dans</a></li><li><a href="http://swesub.tv/dokumentar/">Dokumentär</a></li><li><a href="http://swesub.tv/drama/">Drama</a></li><li><a href="http://swesub.tv/familj/">Familj</a></li><li><a href="http://swesub.tv/fantasy/">Fantasy</a></li><li><a href="http://swesub.tv/komedi/">Komedi</a></li><li><a href="http://swesub.tv/krig/">Krig</a></li><li><a href="http://swesub.tv/kriminal/">Kriminal</a></li><li><a href="http://swesub.tv/musikal/">Musikal</a></li><li><a href="http://swesub.tv/romantik/">Romantik</a></li><li><a href="http://swesub.tv/sci-fi/">Sci-Fi</a></li><li><a href="http://swesub.tv/skrack/">Skräck</a></li><li><a href="http://swesub.tv/sport/">Sport</a></li><li><a href="http://swesub.tv/thriller/">Thriller</a></li><li><a href="http://swesub.tv/western/">Western</a></li><li><a href="http://swesub.tv/aventyr/">Äventyr</a></li>'
y='href="http://swesub.tv/(.+?)/">(.+?)<'
for u,t in re.findall(y,x):
    #print ", '/"+u+"/', {'page': '/"+u+"/?page=%d', 'increase': 1, 'second_page': 2,}),"
    print t