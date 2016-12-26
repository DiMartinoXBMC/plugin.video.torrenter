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
import socket
from datetime import date

import Content
from BeautifulSoup import BeautifulSoup


class KinoPoisk(Content.Content):
    category_dict = {
        'tvshows': ('TV Shows', '/top/serial/list/'),
        'cartoons': ('Cartoons', '/top/id_genre/14/'),
        'search': ('[B]Search[/B]', '/s/type/film/list/1/find/%s/'),
        'movies': ('Movies', '/s/type/film/list/1/m_act[country]/1/m_act[type]/film/'),
        'rus_movies': ('Russian Movies', '/s/type/film/list/1/m_act[country]/2/m_act[type]/film/'),
        'anime': ('Anime', '/s/type/film/list/1/order/rating/m_act[genre][0]/1750/',),
        'hot': ('Most Recent', '/popular/'),
        'top': ('Top 250 Movies', '/top/'),
        'genre': {'genre': 'by Genre',
                  'russia': ('Russia & USSR', '/top/rus/list/'),
                  'biography': ('Biography', '/s/type/film/list/1/m_act[genre][0]/22/'),
                  'action': ('Action', '/top/id_genre/3/'),
                  'thriller': ('Thriller', '/top/id_genre/4/'),
                  'comedy': ('Comedy', '/top/id_genre/6/'),
                  'drama': ('Drama', '/top/id_genre/8/'),
                  'romance': ('Romance', '/top/id_genre/7/'),
                  'horror': ('Horror', '/top/id_genre/1/'),
                  'sci_fi': ('Sci-Fi', '/top/id_genre/2/'),
                  'documentary': ('Documentary', '/top/id_genre/12/'),
                  'cartoonseries': ('Cartoons Series', '/top/mult_serial/list/'),
                  'cartoonshort': ('Cartoons Short', '/top/short_mult/list/'),
                  'short': ('Short', '/top/short/list/'),
                  'male': ('Male', '/top/sex/male/'),
                  'female': ('Female', '/top/sex/female/'),
        }
    }

    for category in category_dict.keys():
        if isinstance(category_dict.get(category), dict):
            for subcategory in category_dict.get(category).keys():
                if subcategory != category:
                    x = category_dict[category][subcategory]
                    if x[1].startswith('/s/type/film/list/'):
                        category_dict[category][subcategory] = (x[0], x[1] + 'perpage/25/',
                                                                {'page': x[1] + 'perpage/25/page/%d/', 'increase': 1,
                                                                 'second_page': 2})
        if not isinstance(category_dict.get(category), dict):
            x = category_dict[category]
            if x[1].startswith('/s/type/film/list/'):
                category_dict[category] = (
                x[0], x[1] + 'perpage/25/', {'page': x[1] + 'perpage/25/page/%d/', 'increase': 1, 'second_page': 2})

    category_dict['year'] = {'year': 'by Year', }
    for y in range(date.today().year, 1970, -1):
        category_dict['year'][str(y)] = (str(y), '/s/type/film/list/1/m_act[year]/%s/' % str(y) + 'perpage/25/',
                                         {'page': '/s/type/film/list/1/m_act[year]/%s/' % str(y) + 'perpage/25/page/%d/',
                                          'increase': 1, 'second_page': 2})

    baseurl = "http://www.kinopoisk.ru"
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

    def isPages(self):
        return True

    def isSearchOption(self):
        return True

    def isScrappable(self):
        return True

    def get_contentList(self, category, subcategory=None, apps_property=None):
        #self.debug=self.log
        socket.setdefaulttimeout(15)
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        self.debug('get_contentList: url = '+url)
        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            self.debug(str(response))
            if category in ['hot']:
                contentList = self.popmode(response)
            elif url.startswith(self.baseurl + '/s/type/film/list/'):
                contentList = self.infomode(response)
            else:
                contentList = self.topmode(response)
        self.debug('get_contentList: contentList = '+str(contentList))
        return contentList

    def stripTtl(self, title):
        bad_end = [u'\(ТВ\)', u'\(сериал\)', u'\(видео\)']
        for code in bad_end:
            title = re.sub(u' ' + code + '$', '', title)
        return title

    def popmode(self, response):
        contentList = []
        Soup = BeautifulSoup(response)
        result = Soup.find('div', 'stat').findAll('div', 'el')
        self.debug('popmode: '+str(result))
        for tr in result:
            #main
            a = tr.findAll('a')
            num = a[0].text

            info = {}
            year = 0
            img = ''
            originaltitle = tr.find('i')
            if originaltitle:
                originaltitle = self.stripHtml(self.unescape(originaltitle.text))
            title = a[1].text
            link = a[1].get('href')
            if link:
                id = re.compile('/film/(\d+)/').findall(link)
                if id:
                    img = self.id2img(id[0])
            try:
                title, year = re.compile('(.+?) \((\d\d\d\d)\)', re.DOTALL).findall(a[1].text)[0]
                #self.log('popmode 1'+str((title, year)))
            except:
                pass
            if not year:
                try:
                    title, year = re.compile('(.+?) \(.*(\d\d\d\d)').findall(a[1].text)[0]
                    info['tvshowtitle'] = title
                    #self.log('popmode 2' + str((title, year)))
                except:
                    pass
            title = self.stripHtml(self.stripTtl(title))

            #info
            info['title'] = title
            info['year'] = int(year)

            contentList.append((
                int(int(self.sourceWeight) * (201 - int(num))),
                originaltitle, title, int(year), img, info,
            ))
        return contentList

    def topmode(self, response):
        contentList = []
        Soup = BeautifulSoup(response)
        result = Soup.find('table', {'cellpadding': '3'}).findAll('tr')[2:]
        self.debug('topmode: ' + str(result))
        for tr in result:
            #main
            td = tr.findAll('td')
            year = 0
            info = {}
            img = ''
            title, originaltitle = None, None
            num = td[0].text.rstrip('.')
            originaltitle = tr.find('span', 'text-grey')
            if originaltitle:
                originaltitle = self.stripHtml(self.unescape(originaltitle.text))
            a_all = tr.find('a', {'class': 'all'})
            if a_all:
                link = a_all.get('href')
                if link:
                    id = re.compile('/film/(\d+)/').findall(link)
                    if id:
                        img = self.id2img(id[0])
                year = re.compile('(.+) \((\d\d\d\d)\)').findall(a_all.text)
                if not year:
                    try:
                        match = re.search(r"(.+) \((\d\d\d\d) &ndash;|(.+) \(.*(\d\d\d\d)", a_all.text,
                                          re.IGNORECASE | re.MULTILINE)
                        if match:
                            title = match.group(1)
                            year = match.group(2)
                            info['tvshowtitle'] = title
                    except:
                        title = a_all.text
                else:
                    title, year = year[0]
                title = self.stripHtml(self.stripTtl(title))

            #info
            if originaltitle and not title:
                title = originaltitle
                originaltitle = None

            if title:
                info['title'] = title
                info['year'] = int(year)

                contentList.append((
                    int(int(self.sourceWeight) * (251 - int(num))),
                    originaltitle, title, int(year), img, info,
                ))
        return contentList

    def infomode(self, response):
        contentList = []
        Soup = BeautifulSoup(response)
        result = Soup.findAll('div', 'info')
        #print str(result)
        num = 0
        for div in result:
            #main
            info = {}
            img = ''
            name = div.find('p', 'name')
            title = name.find('a').text
            link = name.find('a').get('href')
            if link:
                id = re.compile('/film/(\d+)/').findall(link)
                if id:
                    img = self.id2img(id[0])
            year = name.find('span', 'year') if name.find('span', 'year') else 0
            if year:
                year=year.text
                ysplit = year.split(' ')
                if len(ysplit) > 1: year = ysplit[0]
            title = self.stripHtml(self.unescape(title))
            tvshowtitle = re.compile(u'(.+?) \((.+?)\)$').findall(title)
            if tvshowtitle and tvshowtitle[0][1] in [u'сериал']:
                title = tvshowtitle[0][0]
                info['tvshowtitle'] = title
            num = num + 1
            originaltitle = div.find('span', 'gray')
            if originaltitle:
                originaltitle = re.match('(.+?), \d', originaltitle.text)
                if originaltitle:
                    originaltitle = self.stripHtml(self.unescape(originaltitle.group(1)))
            title = self.stripTtl(title)

            #info
            info['title'] = title
            info['year'] = int(year)

            contentList.append((
                int(int(self.sourceWeight) * (100 - int(num))),
                originaltitle, title, int(year), img, info,
            ))
        return contentList


    def id2img(self, id):
        if id:
            return "http://st.kp.yandex.net/images/film_iphone/iphone360_%s.jpg" % (str(id))
        else:
            return ''


'''
                    - Video Values:
                - genre : string (Comedy)
                - year : integer (2009)
                - episode : integer (4)
                - season : integer (1)
                - top250 : integer (192)
                - tracknumber : integer (3)
                - rating : float (6.4) - range is 0..10
                - watched : depreciated - use playcount instead
                - playcount : integer (2) - number of times this item has been played
                - overlay : integer (2) - range is 0..8. See GUIListItem.h for values
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