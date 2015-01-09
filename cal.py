# -*- coding: utf-8 -*-
import sys
import os

ROOT = os.path.dirname(sys.modules["__main__"].sys.argv[0])
searcherObject = {}
searcher = 'IMDB'
if ROOT + os.sep + 'resources' + os.sep + 'contenters' not in sys.path:
    sys.path.insert(0, ROOT + os.sep + 'resources' + os.sep + 'contenters')
searcherObject[searcher] = getattr(__import__(searcher), searcher)()

#print str(searcherObject[searcher].get_contentList(category='search', subcategory='Hobbit'))
