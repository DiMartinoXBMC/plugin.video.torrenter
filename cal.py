# -*- coding: utf-8 -*-
import sys
import os, json

ROOT = os.path.dirname(sys.modules["__main__"].sys.argv[0])
searcherObject = {}
searcher = 'IMDB'
if ROOT + os.sep + 'resources' + os.sep + 'contenters' not in sys.path:
    sys.path.insert(0, ROOT + os.sep + 'resources' + os.sep + 'contenters')
searcherObject[searcher] = getattr(__import__(searcher), searcher)()

#print str(searcherObject[searcher].get_contentList(category='search', subcategory='Hobbit'))

title='No Game No Life\\Subs.[GMC]\\No Game No Life - 06.ass'
path='D:\\torrents\\Torrenter\\No Game No Life\\No Game No Life - 06.mkv'
#path='/sdasda/asdasd/asdasd/No Game No Life - 06.mkv'

folder=title.split('\\')[0]
print folder
temp=os.path.basename(title)
print temp
addition=os.path.dirname(title).lstrip(folder+'\\').replace('\\','.').replace(' ','_').strip()
print addition
ext=temp.split('.')[-1]
temp = temp[:len(temp) - len(ext) - 1]+'.'+addition+'.'+ext
print temp
newFileName=os.path.join(os.path.dirname(path),temp.replace('\\',os.sep))
print str((os.path.join(os.path.dirname(os.path.dirname(path)),title.replace('\\',os.sep)),newFileName))