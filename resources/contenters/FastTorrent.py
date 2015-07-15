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
from BeautifulSoup import BeautifulSoup


class FastTorrent(Content.Content):
    category_dict = {
        #'movies':('Movies', '/popular/'),
        'tvshows': (
        'TV Shows', '/last-tv-torrent/', {'page': '/last-tv-torrent/%d.html', 'increase': 1, 'second_page': 2}),
        'cartoons': ('Cartoons', '/last-multfilm-torrent/',
                     {'page': '/last-multfilm-torrent/%d.html', 'increase': 1, 'second_page': 2}),
        'anime': ('Anime', '/anime/multfilm/', {'page': '/anime/multfilm/%d.html', 'increase': 1, 'second_page': 2}),
        'hot': ('Most Recent', '/new-films/', {'page': '/new-films/%d.html', 'increase': 1, 'second_page': 2}),
        'genre': {'genre': 'by Genre',
                  'amime_series': ('Anime Series', '/anime-serialy/multfilm/',
                                   {'page': '/anime-serialy/multfilm/%d.html', 'increase': 1, 'second_page': 2}),
        }
        #'top':('Top 250 Movies', '/top/'),
    }
    baseurl = "http://www.fast-torrent.ru"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', baseurl), ('Accept-Encoding', 'gzip'), ('Accept-Language', 'ru,en;q=0.8')]
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 1

    def isTracker(self):
        return False

    def isSearcher(self):
        return False

    def isScrappable(self):
        return True

    def isSearchOption(self):
        return True

    def isInfoLink(self):
        return False

    def isPages(self):
        return True

    def get_contentList(self, category, subcategory=None, apps_property=None):
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            #print response
            if category:  # in ['hot']:
                contentList = self.popmode(response)
        #print str(contentList)
        return contentList

    def popmode(self, response):
        contentList = []
        Soup = BeautifulSoup(response.decode('utf-8'))
        result = Soup.findAll('div', {'class': 'film-wrap'})
        num = 16
        for tr in result:
            #main
            info = {}
            num = num - 1
            original_title = None
            year = 0
            h2 = tr.find('h2')
            #print str(h2)
            label = h2.find('span', {'itemprop': 'name'})
            if label:
                title = label.text
                year = re.compile('\((\d\d\d\d)\)').findall(h2.text)
                if year:
                    year = year[0]
                original_title = h2.find('span', {'itemprop': 'alternativeHeadline'})
                if original_title:
                    original_title = original_title.text
            else:
                try:
                    title, year, original_title = \
                    re.compile(u'<h2>(.+?) \((\d\d\d\d)\) <br.*?>\((.+?)\)<', re.DOTALL | re.I).findall(unicode(h2))[0]
                except:
                    try:
                        title, year = re.compile(u'<h2>(.+?) \((\d\d\d\d)\)<', re.DOTALL | re.I).findall(unicode(h2))[0]
                    except:
                        pass
            a = tr.find('div', 'film-image').find('a')
            link = a.get('href')
            img = a.get('style')
            if img:
                img = img.replace('background: url(', '').rstrip(')')

            #info

            info['label'] = title
            info['link'] = link
            info['title'] = title
            genre = tr.find('div', 'film-genre').text
            tv = [u'Зарубежный сериал', u'Русский сериал', u'Аниме сериалы', u'Мультсериалы']
            for i in tv:
                if re.search(i, genre):
                    info['tvshowtitle'] = title
            info['year'] = int(year)

            contentList.append((
                int(int(self.sourceWeight) * (int(num))),
                original_title, title, int(year), img, info,
            ))
        return contentList
