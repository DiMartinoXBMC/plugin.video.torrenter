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


class EZTV(Content.Content):
    category_dict = {
        'hot': ('Most Recent', '/', {'page': '/page_%d', 'increase': 1, 'second_page': 1}),
    }

    baseurl = "https://eztv.ag"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', 'https://eztv.ch/'), ('Accept-Encoding', 'gzip')]
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 1

    def isTracker(self):
        return True

    def isSearcher(self):
        return False

    def isScrappable(self):
        return False

    def isInfoLink(self):
        return True

    def isPages(self):
        return True

    def isSearchOption(self):
        return False

    def get_contentList(self, category, subcategory=None, apps_property=None):
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            # print response
            if category in ['hot']:
                contentList = self.mode(response)
        # print str(contentList)
        return contentList

    def mode(self, response):
        contentList = []
        # print str(result)
        num = 51
        result = re.compile(
            r'''class="epinfo">(.+?)</a>.+?<a href="(magnet.+?)".+?<td align="center" class="forum_thread_post">(.+?) </td>''',
            re.DOTALL).findall(response)
        for title, link, date in result:
            # main
            info = {}
            num = num - 1
            original_title = None
            year = 0
            img = ''
            # info

            info['label'] = info['title'] = title
            info['link'] = link
            info['plot'] = info['title'] + '\r\nAge: %s' % (date)

            contentList.append((
                int(int(self.sourceWeight) * (int(num))),
                original_title, title, int(year), img, info,
            ))
        return contentList
