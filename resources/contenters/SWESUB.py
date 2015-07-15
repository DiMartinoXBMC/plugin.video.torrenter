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


class SWESUB(Content.Content):
    category_dict = {
        'tvshows': ('TV Shows', '/senaste-tv-serier/', {'page': '/senaste-tv-serier/?page=%d',
                                                        'increase': 1, 'second_page': 2, }),
        'movies': ('Movies', '/senaste-filmer/'),
        # , {'page': '/senaste-filmer/?page=%d', 'increase': 1, 'second_page': 2,}),
        'genre': {'genre': 'by Genre',
                  'action': ('Action', '/action/', {'page': '/action/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'adventure': (
                  'Adventure', '/aventyr/', {'page': '/aventyr/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'animation': (
                  'Animation', '/animerat/', {'page': '/animerat/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'comedy': ('Comedy', '/komedi/', {'page': '/komedi/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'crime': ('Crime', '/kriminal/', {'page': '/kriminal/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'documentary': (
                  'Documentary', '/dokumentar/', {'page': '/dokumentar/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'drama': ('Drama', '/drama/', {'page': '/drama/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'family': ('Family', '/familj/', {'page': '/familj/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'fantasy': ('Fantasy', '/fantasy/', {'page': '/fantasy/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'horror': ('Horror', '/skrack/', {'page': '/skrack/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'music': ('Music', '/dans/', {'page': '/dans/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'musical': ('Musical', '/musikal/', {'page': '/musikal/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'romance': (
                  'Romance', '/romantik/', {'page': '/romantik/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'sci_fi': ('Sci-Fi', '/sci-fi/', {'page': '/sci-fi/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'sport': ('Sport', '/sport/', {'page': '/sport/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'thriller': (
                  'Thriller', '/thriller/', {'page': '/thriller/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'war': ('War', '/krig/', {'page': '/krig/?page=%d', 'increase': 1, 'second_page': 2, }),
                  'western': ('Western', '/western/', {'page': '/western/?page=%d', 'increase': 1, 'second_page': 2, }),
                  }
    }

    baseurl = "http://swesub.tv"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', 'http://swesub.tv/'), ('Accept-Encoding', 'gzip')]
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

    def isSort(self):
        return False

    def isSearchOption(self):
        return False

    def get_contentList(self, category, subcategory=None, apps_property=None):
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)
        response = response.decode('iso-8859-1')

        if None != response and 0 < len(response):
            if category:
                contentList = self.mode(response)
        # print str(contentList)
        return contentList

    def mode(self, response):
        contentList = []
        num = 51
        Soup = BeautifulSoup(response)
        result = Soup.findAll('article', {'class': 'box'})
        # print str(result)
        for article in result:
            # main
            info = {}
            num = num - 1
            original_title = None
            year = 0

            div = article.find('div', {'class': 'box-img'})
            title = div.find('img').get('alt')
            img = div.find('img').get('src')
            link = div.find('a').get('href').replace(self.baseurl, '').replace('.html', '')

            # info

            info['label'] = info['title'] = self.unescape(title)
            info['link'] = self.baseurl + '/downloads' + link + '/'
            info['infolink'] = self.baseurl + link + '.html'

            info['plot'] = article.find('div', {'class': 'item-content'}).text

            contentList.append((
                int(int(self.sourceWeight) * (int(num))),
                original_title, title, int(year), img, info,
            ))
        return contentList
