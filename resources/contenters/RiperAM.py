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

import Content
from BeautifulSoup import BeautifulSoup


class RiperAM(Content.Content):
    category_dict = {
        #'movies':('Movies', '/popular/'),
        #'tvshows':('TV Shows', '/top/serial/list/'),
        #'cartoons':('Cartoons', '/top/id_genre/14/'),
        #'anime':('Anime', '/search/title?count=100&genres=animation&keywords=anime&num_votes=1000,&explore=title_type&ref_=gnr_kw_an'),
        'hot': ('Most Recent', '/', {'page': '/portal.php?tp=%d', 'increase': 30, 'second_page': 30}),
        #'top':('Top 250 Movies', '/top/'),
    }

    baseurl = "http://www.riper.am"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', 'http://www.riper.am/'), ('Accept-Encoding', 'gzip,deflate,sdch'),
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
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            #print response
            if category in ['hot']:
                contentList = self.popmode(response)
        #print str(contentList)
        return contentList

    def popmode(self, response):
        contentList = []
        Soup = BeautifulSoup(response)
        result = Soup.findAll('table', 'postbody postbody_portal')
        #print str(result)
        num = 31
        bad_forum = [u'Безопасность', u'Книги и журналы', u'Action & Shooter', u'RPG/MMORPG']
        for tr in result:
            #main
            info = {}
            forum = tr.find('div', {'style': 'height:20px;overflow:hidden;'}).find('a').text
            if forum and forum in bad_forum:
                continue
            link = tr.find('div', {'style': 'width:200px;overflow:hidden;'}).find('a').get('href')
            num = num - 1
            label = tr.find('strong').text
            original_title = None
            year = 0
            title = self.unescape(label)
            img = tr.findAll('a')[0].find('img').get('src')
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
