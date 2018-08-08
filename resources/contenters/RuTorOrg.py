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
import re, sys

import Content
from BeautifulSoup import BeautifulSoup

#http://anti-tor.org/browse/0/1/0/0 date movie
#http://anti-tor.org/browse/1/1/0/0 page 2
#http://anti-tor.org/browse/0/1/0/2 seed movie
#                          page/cat/?/sort


class RuTorOrg(Content.Content):
    category_dict = {
        'movies': ('Movies', '/browse/0/1/0',
                   {'page': '/browse/%d/1/0', 'increase': 1, 'second_page': 1,
                                                'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                                                         {'name': 'by Date', 'url_after': '/0'}]}),
        'rus_movies': ('Russian Movies', '/browse/0/5/0',
                   {'page': '/browse/%d/5/0', 'increase': 1, 'second_page': 1,
                    'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                             {'name': 'by Date', 'url_after': '/0'}]}),
        'tvshows': ('TV Shows', '/browse/0/4/0',
                   {'page': '/browse/%d/4/0', 'increase': 1, 'second_page': 1,
                    'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                             {'name': 'by Date', 'url_after': '/0'}]}),
        'science': ('Научно - популярные фильмы', '/browse/0/12/0',
                   {'page': '/browse/%d/12/0', 'increase': 1, 'second_page': 1,
                    'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                             {'name': 'by Date', 'url_after': '/0'}]}),
        'cartoons': ('Cartoons', '/browse/0/7/0',
                   {'page': '/browse/%d/7/0', 'increase': 1, 'second_page': 1,
                    'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                             {'name': 'by Date', 'url_after': '/0'}]}),
        'anime': ('Anime', '/browse/0/10/0',
                   {'page': '/browse/%d/10/0', 'increase': 1, 'second_page': 1,
                    'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                             {'name': 'by Date', 'url_after': '/0'}]}),
        'sport': ('Спорт и Здоровье', '/browse/0/13/0',
                   {'page': '/browse/%d/13/0', 'increase': 1, 'second_page': 1,
                    'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                             {'name': 'by Date', 'url_after': '/0'}]}),
        'tele': ('Телевизор', '/browse/0/6/0',
                  {'page': '/browse/%d/6/0', 'increase': 1, 'second_page': 1,
                   'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                            {'name': 'by Date', 'url_after': '/0'}]}),
        'humor': ('Юмор', '/browse/0/15/0',
                 {'page': '/browse/%d/15/0', 'increase': 1, 'second_page': 1,
                  'sort': [{'name': 'by Seeders', 'url_after': '/2'},
                           {'name': 'by Date', 'url_after': '/0'}]}),
    }


    #'hot': ('Most Recent',),


    baseurl = "anti-tor.org"

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

    def isSort(self):
        return True

    def isSearchOption(self):
        return False

    def get_contentList(self, category, subcategory=None, apps_property=None):
        #self.debug = self.log
        contentList = []
        url = 'http://%s' % self.get_url(category, subcategory, apps_property)
        self.debug(url)

        self.headers = [('User-Agent',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
           ('Referer', 'http://%s' % self.baseurl), ('Accept-encoding', 'gzip'),
           ('Cookie', str(sys.modules["__main__"].__settings__.getSetting("rutor-auth")))]

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            #self.debug(response)
            cookie = re.compile("document.cookie='(.+?)';").findall(response)
            if cookie and str(cookie[0]) != str(sys.modules["__main__"].__settings__.getSetting("rutor-auth")):
                cookie = cookie[0]
                self.log('ok found new cookie: ' + str(cookie))
                sys.modules["__main__"].__settings__.setSetting("rutor-auth", cookie)
                headers = [('User-Agent',
                            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                           ('Referer', 'http://%s' % self.baseurl), ('Accept-encoding', 'gzip'),
                           ('Cookie', str(sys.modules["__main__"].__settings__.getSetting("rutor-auth")))]
                response = self.makeRequest(url, headers=headers)
                self.debug(response)

            if category:
                contentList = self.mode(response.decode('utf-8'))
        self.debug(str(contentList))
        return contentList

    def mode(self, response):
        contentList = []
        num = 101


        regex = '''<tr class="[tg].+?</tr>'''
        regex_tr = '<td>(.+?)</td><td ><a.+?href="(.+?download/\d+)">.+?<a href=".+?">.+?<a href="(.+?)">(.+?)</a></td>.+?<td align="right">(\d*?\..+?&nbsp;.+?)</td>.+?<img .+?alt="S".+?>&nbsp;(\d+)</span>.+?alt="L".+?>&nbsp;(\d+)'
        for tr in re.compile(regex, re.DOTALL).findall(response):
            result=re.compile(regex_tr, re.DOTALL).findall(tr)
            if result:
                self.debug(tr + ' -> ' + str(result[0]))
                (date, link, infolink, title, size, seeds, leechers)=result[0]
                # main
                info = {}
                num = num - 1
                original_title = None
                year = 0
                img = ''

                # info
                title = self.unescape(self.stripHtml(title.strip()))
                info['label'] = info['title'] = title

                if link[0] == '/': link = 'http://%s%s' % (self.baseurl, link)
                info['link'] = link

                #if infolink[0] == '/': infolink = 'http://%s%s' % (self.baseurl, infolink)
                #info['infolink'] = infolink

                size = size.replace('&nbsp;', ' ')
                date = date.replace('&nbsp;', ' ')

                info['plot'] = info['title'] + '\r\n[I](%s) [S/L: %s/%s] [/I]\r\n%s: %s' % (
                size, seeds, leechers, self.localize('Date'), date)

                #regex_title = '(.+?) / (.+?) \((\d\d\d\d)\)'
                #regex_result = re.compile(regex_title, re.DOTALL).findall(title)
                #if regex_result:
                #    title, original_title, year = regex_result[0]
                #    info['title'] = title

                contentList.append((
                    int(int(self.sourceWeight) * (int(num))),
                    original_title, title, int(year), img, info,
                ))

        return contentList

    def get_info(self, url):
        self.debug = self.log
        movieInfo = {}
        color = '[COLOR blue]%s:[/COLOR] %s\r\n'
        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            Soup = BeautifulSoup(response)
            result = Soup.find('div', 'torrentMediaInfo')
            if not result:
                return None
            li = result.findAll('li')
            info, movieInfo = {'Cast': ''}, {'desc': '', 'poster': '', 'title': '', 'views': '0', 'rating': '50',
                                             'kinopoisk': ''}
            try:
                img = result.find('a', {'class': 'movieCover'}).find('img').get('src')
                movieInfo['poster'] = img if img.startswith('http:') else 'http:' + img
            except:
                pass
            try:
                movie = re.compile('View all <strong>(.+?)</strong> episodes</a>').match(str(result))
                if movie:
                    info['Movie'] = movie.group(1)
            except:
                pass
            for i in li:
                name = i.find('strong').text
                if name:
                    info[name.rstrip(':')] = i.text.replace(name, '', 1)
            plot = result.find('div', {'id': 'summary'})
            if plot:
                cut = plot.find('strong').text
                info['plot'] = plot.text.replace(cut, '', 1).replace('report summary', '')
            # print str(result)
            cast = re.compile('<a href="/movies/actor/.+?">(.+?)</a>').findall(str(result))
            if cast:
                for actor in cast:
                    info['Cast'] += actor + ", "
            if 'Genres' in info:
                info['Genres'] = info['Genres'].replace(', ', ',').replace(',', ', ')
            for key in info.keys():
                if not 'Movie' in info and info[key] == 'addto bookmarks':
                    movieInfo['title'] = self.unescape(key)
                    info['TV Show'] = self.unescape(key)
                if not 'plot' in info and 'Summary' in key:
                    info['plot'] = info[key]

            for i in ['Movie', 'TV Show', 'Release date', 'Original run', 'Episode', 'Air date', 'Genres', 'Language',
                      'Director', 'Writers', 'Cast', 'Original run', 'IMDb rating', 'AniDB rating']:
                if info.get(i) and info.get(i) not in ['']:
                    movieInfo['desc'] += color % (i, info.get(i))
                    if i == 'Movie':
                        movieInfo['title'] = info.get(i)

            for i in ['plot', 'IMDb link', 'RottenTomatoes']:
                if info.get(i) and info.get(i) not in ['']:
                    if i == 'plot':
                        movieInfo['desc'] += '\r\n[COLOR blue]Plot:[/COLOR]\r\n' + self.unescape(info.get(i))
                    if i == 'RottenTomatoes':
                        movieInfo['rating'] = str(info.get(i).split('%')[0])
                    if i == 'IMDb link':
                        movieInfo['kinopoisk'] = 'http://imdb.snick.ru/ratefor/02/tt%s.png' % info.get(i)

        self.debug(str(movieInfo))
        return movieInfo
