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

class KickAssSo(Content.Content):
    category_dict = {
        'hot': ('Hot & New', '/new/', {'page': '/new/%d/', 'increase': 1, 'second_page': 2}),
        'anime': ('Anime', '/anime/', {'page': '/anime/%d/', 'increase': 1, 'second_page': 2}),
        'tvshows': ('TV Shows', '/tv/', {'page': '/tv/%d/', 'increase': 1, 'second_page': 2}),
        'movies': ('Forieng Movies', '/movies/', {'page': '/movies/%d/', 'increase': 1, 'second_page': 2}),
    }

    baseurl = "http://kickass.so"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', 'http://kickass.so/'), ('Accept-Encoding', 'gzip')]
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 1

    def isLabel(self):
        return True

    def isScrappable(self):
        return False

    def isInfoLink(self):
        return True

    def isPages(self):
        return True

    def isSearchOption(self):
        return False

    def get_contentList(self, category, subcategory=None, page=None):
        contentList = []
        url = self.get_url(category, subcategory, page, self.baseurl)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            #print response
            if category:
                contentList = self.mode(response)
        #print str(contentList)
        return contentList

    def mode(self, response):
        contentList = []
        #print str(result)
        num = 51
        good_forums=['TV','Anime','Movies']
        result = re.compile(
                r'''<a title="Download torrent file" href="(.+?)\?.+?" class=".+?"><i.+?<a.+?<a.+?<a href=".+?html" class=".+?">(.+?)</a>.+? in <span.+?"><strong>.+?">(.+?)</a>''',
                re.DOTALL).findall(response)
        for link,title,forum in result:
            #main
            if forum in good_forums:
                info = {}
                num = num - 1
                original_title = None
                year = 0
                img = ''
                #info

                info['label'] = info['title'] = self.unescape(title)
                info['link'] = link

                contentList.append((
                    int(int(self.sourceWeight) * (int(num))),
                    original_title, title, int(year), img, info,
                ))
        return contentList
