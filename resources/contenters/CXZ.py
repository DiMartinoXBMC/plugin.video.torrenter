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
from datetime import date

def make_category_dict():
    category_dict = {
        'movies': ('Movies', '/films/fl_foreign_hight/?'),
        'rus_movies': ('Russian Movies', '/films/fl_our_hight/?'),
        'tvshows': ('TV Shows', '/serials/fl_hight/?'),
        'cartoons': ('Cartoons', '/cartoons/fl_hight/?'),
        'anime': ('Anime', '/cartoons/cartoon_genre/anime/?'),
        'hot': ('Most Recent', '/films/fl_hight/?'),
        'top': ('Top 250 Movies', '/films/fl_hight/?sort=popularity&'),
        'genre': {'genre': 'by Genre',
                  'action': ('Action', '/films/film_genre/bojevik/?'),
                  'adventure': ('Adventure', '/films/film_genre/priklucheniya/?'),
                  'biography': ('Biography', '/films/film_genre/biografiya/?'),
                  'comedy': ('Comedy', '/films/film_genre/komediya/?'),
                  'crime': ('Crime', '/films/film_genre/detektiv/?'),
                  'documentary': ('Documentary', '/films/film_genre/dokumentalnyj/?'),
                  'drama': ('Drama', '/films/film_genre/drama/?'),
                  'erotika': ('Adult', '/films/film_genre/erotika/?'),
                  'family': ('Family', '/films/film_genre/semejnyj/?'),
                  'fantasy': ('Fantasy', '/films/film_genre/fentezi/?'),
                  'film_noir': ('Film-Noir', '/films/film_genre/nuar/?'),
                  'history': ('History', '/films/film_genre/istoriya/?'),
                  'horror': ('Horror', '/films/film_genre/uzhasy/?'),
                  'kids': ('For Kids', '/films/film_genre/detskij/?'),
                  'musical': ('Musical', '/films/film_genre/muzikl/?'),
                  'mystery': ('Mystery', '/films/film_genre/mistika/?'),
                  'romance': ('Romance', '/films/film_genre/melodrama/?'),
                  'sci_fi': ('Sci-Fi', '/films/film_genre/fantastika/?'),
                  'short': ('Short', '/films/film_genre/korotkometrazhka/?'),
                  'thriller': ('Thriller', '/films/film_genre/triller/?'),
                  'war': ('War', '/films/film_genre/vojennyj/?'),
                  'western': ('Western', '/films/film_genre/vestern/?'),
        }
    }

    for category in category_dict.keys():
        if isinstance(category_dict.get(category), dict):
            for subcategory in category_dict.get(category).keys():
                if subcategory != category:
                    x = category_dict[category][subcategory]
                    category_dict[category][subcategory] = (
                    x[0], x[1] + 'view=list', {'page': x[1] + 'view=list&page=%d', 'increase': 1, 'second_page': 1})
        if not isinstance(category_dict.get(category), dict):
            x = category_dict[category]
            category_dict[category] = (
            x[0], x[1] + 'view=list', {'page': x[1] + 'view=list&page=%d', 'increase': 1, 'second_page': 1})

    category_dict['year'] = {'year': 'by Year', }
    for y in range(date.today().year, 1970, -1):
        category_dict['year'][str(y)] = (str(y), '/films/year/%s/' % str(y),
                                         {'page': '/films/year/%s/' % str(y) + '?view=list&page=%d', 'increase': 1,
                                          'second_page': 1})

    return category_dict


class CXZ(Content.Content):
    category_dict = make_category_dict()

    regex_list = []

    baseurl = "http://cxz.to"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', baseurl), ('Accept-Encoding', 'gzip'), ('Accept-Language', 'ru,en;q=0.8')]
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 2


    def isTracker(self):
        return False

    def isSearcher(self):
        return False

    def isInfoLink(self):
        return False

    def isPages(self):
        return True

    def isSearchOption(self):
        return True

    def isScrappable(self):
        return True

    def get_contentList(self, category, subcategory=None, apps_property=None):
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            #print response
            if category:
                contentList = self.mode(response)
        #print str(contentList)
        return contentList

    def mode(self, response):
        contentList = []
        Soup = BeautifulSoup(response)
        result = Soup.findAll('div', {'class': 'b-poster-tile   '})
        num = 0
        for tr in result:
            #main
            info = {}
            year = 0
            num = num + 1
            title = tr.find('span', 'b-poster-tile__title-full').text.strip()
            originaltitle = None
            year = re.compile('(\d\d\d\d)').findall(tr.find('span', 'b-poster-tile__title-info-items').text)[0]
            link = tr.find('a', 'b-poster-tile__link').get('href')
            for i in ['/serials/', '/cartoonserials/', '/tvshow/']:
                if i in link:
                    info['tvshowtitle'] = title
                    break

            img = tr.find('img').get('src')
            img = img if img else ''

            #info

            contentList.append((
                int(int(self.sourceWeight) * (251 - int(num))),
                originaltitle, title, int(year), img, info,
            ))
        #print result
        return contentList