# -*- coding: utf-8 -*-
'''
    Torrenter plugin for XBMC
    Copyright (C) 2012 Vadim Skorba
    vadim.skorba@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import re

import Content


class RiperAM(Content.Content):
    category_dict = {
        'hot': ('Most Recent', '/', {'page': '/portal.php?tp=%d', 'increase': 30, 'second_page': 30}),
    }

    baseurl = "http://riperam.org/"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', baseurl+'/'), ('Accept-Encoding', 'gzip,deflate,sdch'),
               ('Accept-Language', 'ru,en;q=0.8')]
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 1

    def isTracker(self):
        return True

    def isSearcher(self):
        return True

    def isScrappable(self):
        return False

    def isInfoLink(self):
        return True

    def isPages(self):
        return True

    def isSearchOption(self):
        return False

    def get_contentList(self, category, subcategory=None, apps_property=None):
        #self.debug=self.log
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            response=response.decode('utf-8')
            #self.debug(str(response))
            if category in ['hot']:
                contentList = self.popmode(response)
        self.debug('[get_contentList] contentList '+str(contentList))
        return contentList

    def popmode(self, response):
        contentList = []
        num = 31
        bad_forum = [u'Безопасность', u'Книги и журналы', u'Action & Shooter', u'RPG/MMORPG', u'Книги', u'Журналы']

        regex = u'<table class="postbody postbody_portal"(.+?)</table>'
        regex_tr = u'''<img height="200" src="(.+?)".+?></a>.+?<h4 class="first"><a href="(.+?)" title=".+?"><strong>(.+?)</strong></a></h4></div>.+?<div style="height:20px;overflow:hidden;">.+?<a href=".+?">(.+?)</a>'''
        for tr in re.compile(regex, re.DOTALL).findall(response):

            result=re.compile(regex_tr, re.DOTALL).findall(tr)
            self.debug(tr+' -> '+str(result))
            if result:
                (img, link, label, forum)=result[0]
                info = {}
                if forum and forum in bad_forum:
                    continue
                num = num - 1
                original_title = None
                year = 0
                title = self.unescape(label)
                if img:
                    img = img.replace('.webp', '.jpg')

                #info

                info['label'] = label
                info['link'] = link
                info['title'] = title
                info['year'] = int(year)

                contentList.append((
                    int(int(self.sourceWeight) * (int(num))),
                    original_title, title, int(year), img, info,
                ))
        return contentList
