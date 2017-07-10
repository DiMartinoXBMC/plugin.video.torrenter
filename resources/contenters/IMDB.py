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
import HTMLParser

import Content
from BeautifulSoup import BeautifulSoup
from datetime import date


class IMDB(Content.Content):
    category_dict = {
        'movies': ('Movies', '/search/title?languages=en|1&title_type=feature&sort=moviemeter,asc'),
        'rus_movies': ('Russian Movies', '/search/title?languages=ru|1&title_type=feature&sort=moviemeter,asc'),
	'heb_movies': ('סרטים ישראלים', '/search/title?languages=he|1&title_type=feature&sort=moviemeter,asc'),
        'tvshows': ('TV Shows', '/search/title?count=100&title_type=tv_series,mini_series&ref_=gnr_tv_mp'),
        'cartoons': ('Cartoons', '/search/title?genres=animation&title_type=feature&sort=moviemeter,asc'),
        'anime': ('Anime',
                  '/search/title?count=100&genres=animation&keywords=anime&num_votes=1000,&explore=title_type&ref_=gnr_kw_an'),
        'hot': ('Most Recent', '/search/title?count=100&title_type=feature%2Ctv_series%2Ctv_movie&ref_=nv_ch_mm_1'),
        'top': ('Top 250 Movies', '/chart/top/'),
        'search': ('[B]Search[/B]', '/find?q=%s&s=tt&ttype=ft'),
        'year': {'year': 'by Year', },
        'genre': {'genre': 'by Genre',
                  'action': ('Action', '/genre/action'),
                  'adventure': ('Adventure', '/genre/adventure'),
                  'animation': ('Animation', '/genre/animation'),
                  'biography': ('Biography', '/genre/biography'),
                  'comedy': ('Comedy', '/genre/comedy'),
                  'crime': ('Crime', '/genre/crime'),
                  'documentary': ('Documentary', '/genre/documentary'),
                  'drama': ('Drama', '/genre/drama'),
                  'family': ('Family', '/genre/family'),
                  'fantasy': ('Fantasy', '/genre/fantasy'),
                  'film_noir': ('Film-Noir', '/genre/film_noir'),
                  'history': ('History', '/genre/history'),
                  'horror': ('Horror', '/genre/horror'),
                  'music': ('Music', '/genre/music'),
                  'musical': ('Musical', '/genre/musical'),
                  'mystery': ('Mystery', '/genre/mystery'),
                  'romance': ('Romance', '/genre/romance'),
                  'sci_fi': ('Sci-Fi', '/genre/sci_fi'),
                  'short': ('Short', '/genre/short'),
                  'sport': ('Sport', '/genre/sport'),
                  'thriller': ('Thriller', '/genre/thriller'),
                  'war': ('War', '/genre/war'),
                  'western': ('Western', '/genre/western'),
        }
    }

    for y in range(date.today().year, 1970, -1):
        category_dict['year'][str(y)] = (str(y), '/year/%s/' % str(y))

    regex_list = []

    baseurl = "http://imdb.com"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', baseurl), ('Accept-Encoding', 'gzip'), ('Accept-Language', 'he,en,ru;q=0.8')]
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

    def isPages(self):
        return False

    def isSearchOption(self):
        return True

    def isScrappable(self):
        return True

    def get_contentList(self, category, subcategory=None, apps_property=None):
        self.debug = self.log
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            self.debug(response)
            if category in ['top']:
                contentList = self.topmode(response)
            elif category == 'search':
                contentList = self.searchmode(response)
            else:  #if category in ['genre']:
                contentList = self.genremode(response)
        self.debug(str(contentList))
        return contentList

    def searchmode(self, response):
        contentList = []
        pars = HTMLParser.HTMLParser()
        Soup = BeautifulSoup(response)
        result = Soup.findAll('tr', {'class': 'lister-item mode-advanced'})
        num = 250
        for tr in result:
            #main
            info = {}
            year = 0
            num = num - 1

            title = pars.unescape(tr.findAll('a')[1].text)
            tdtitle = tr.find('td', 'result_text')
            #print str(tdtitle.text.encode('utf-8'))
            originaltitle = tr.find('i')
            if originaltitle:
                originaltitle = originaltitle.text
            try:
                year = re.compile('\((\d\d\d\d)\)').findall(tdtitle.text)[0]
            except:
                try:
                    year = re.compile('(\d\d\d\d)').findall(tdtitle.text)[0]
                except:
                    pass
                info['tvshowtitle'] = title
            img = self.biggerImg(tr.find('img').get('src'))

            contentList.append((
                int(int(self.sourceWeight) * (251 - int(num))),
                originaltitle, title, int(year), img, info,
            ))
        self.debug(str(result))
        return contentList

    def genremode(self, response):
        contentList = []
        pars = HTMLParser.HTMLParser()
        Soup = BeautifulSoup(response)
        result = Soup.findAll('tr', {'class': ['odd detailed', 'even detailed']})
        for tr in result:
            #main
            info = {}
            year = 0
            tdtitle = tr.find('td', 'title')
            num = tr.find('td', 'number').text.rstrip('.')
            originaltitle = None
            title = pars.unescape(tdtitle.find('a').text)
            try:
                year = re.compile('\((\d\d\d\d)\)').findall(tdtitle.find('span', 'year_type').text)[0]
            except:
                try:
                    year = re.compile('(\d\d\d\d)').findall(tdtitle.find('span', 'year_type').text)[0]
                except:
                    pass
                info['tvshowtitle'] = title
            img = self.biggerImg(tr.find('td', 'image').find('img').get('src'))

            #info

            info['code'] = tr.find('span', 'wlb_wrapper').get('data-tconst')

            contentList.append((
                int(int(self.sourceWeight) * (251 - int(num))),
                originaltitle, title, int(year), img, info,
            ))
        self.debug(str(result))
        return contentList

    def biggerImg(self, img):
        if img and '._' in img:
            img = img.split('._')[0] + '._V1_SY_CR1,0,,_AL_.jpg'
            return img

    def topmode(self, response):
        contentList = []
        Soup = BeautifulSoup(response)
        result = Soup.findAll('tr')[1:251]
        for tr in result:
            #main
            tdtitle = tr.find('td', 'titleColumn')
            num = tr.find('span', {'name': 'rk'}).get('data-value').rstrip('.')
            originaltitle = None
            title = tdtitle.find('a').text
            year = tdtitle.find('span', {'class': 'secondaryInfo'}).text.rstrip(')').lstrip('(')
            tdposter = tr.find('td', 'posterColumn')
            img = self.biggerImg(tdposter.find('img').get('src'))

            #info
            info = {}
            info['title'] = title
            info['year'] = int(year)
            info['code'] = tr.find('div', 'wlb_ribbon').get('data-tconst')

            contentList.append((
                int(int(self.sourceWeight) * (251 - int(num))),
                originaltitle, title, int(year), img, info,
            ))
        #print result
        return contentList


'''
                    - Video Values:
                - genre : string (Comedy)
                - year : integer (2009)
                - episode : integer (4)
                - season : integer (1)
                - top250 : integer (192)
                - rating : float (6.4) - range is 0..10
                - cast : list (Michal C. Hall)
                - castandrole : list (Michael C. Hall|Dexter)
                - director : string (Dagur Kari)
                - mpaa : string (PG-13)
                - plot : string (Long Description)
                - plotoutline : string (Short Description)
                - title : string (Big Fan)
                - originaltitle : string (Big Fan)
                - sorttitle : string (Big Fan)
                - duration : string (3:18)
                - studio : string (Warner Bros.)
                - tagline : string (An awesome movie) - short description of movie
                - writer : string (Robert D. Siegel)
                - tvshowtitle : string (Heroes)
                - premiered : string (2005-03-04)
                - status : string (Continuing) - status of a TVshow
                - code : string (tt0110293) - IMDb code
                - aired : string (2008-12-07)
                - credits : string (Andy Kaufman) - writing credits
                - lastplayed : string (Y-m-d h:m:s = 2009-04-05 23:16:04)
                - album : string (The Joshua Tree)
                - artist : list (['U2'])
                - votes : string (12345 votes)
                - trailer : string (/home/user/trailer.avi)
                - dateadded : string (Y-m-d h:m:s = 2009-04-05 23:16:04)
                '''
