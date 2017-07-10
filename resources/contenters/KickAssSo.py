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


class KickAssSo(Content.Content):
    category_dict = {
                'hot': ('Most Recent', '/new/?field=seeders&sorder=desc',
                {'page': '/new/%d/?field=seeders&sorder=desc', 'increase': 1, 'second_page': 2,
                 ' ': [{'name': ' ', 'url_after': '?field=seeders&sorder=desc'}]}),
        'anime': ('Anime', '/anime/', {'page': '/anime/%d/', 'increase': 1, 'second_page': 2,
                                       ' ': [{'name': ' ', 'url_after': '?field=seeders&sorder=desc'}]}),
        'tvshows': ('TV Shows', '/tv/?field=seeders&sorder=desc',
                    {'page': '/tv/%d/?field=seeders&sorder=desc', 'increase': 1, 'second_page': 2,
                     ' ': [{'name': ' ', 'url_after': '?field=seeders&sorder=desc'}]}),
        'movies': ('Movies', '/movies/?field=seeders&sorder=desc',
                   {'page': '/movies/%d/?field=seeders&sorder=desc', 'increase': 1, 'second_page': 2,
                    '': [{'name': '', 'url_after': '?field=seeders&sorder=desc'}]}),
		'3Dmovies': ('3D Movies', '/3d-movies/?field=seeders&sorder=desc',
                   {'page': '/3d-movies/%d/?field=seeders&sorder=desc', 'increase': 1, 'second_page': 2,
                    'sort ': [{'name': 'by Seeders', 'url_after': '?field=seeders&sorder=desc'},
						{'name': 'by Date', 'url_after': '?field=time_add&sorder=desc'}]}),
		'highres movies': ('High Resolution Movies', '/highres-movies/?field=seeders&sorder=desc',
                   {'page': '/highres-movies/%d/?field=seeders&sorder=desc', 'increase': 1, 'second_page': 2,
                    ' ': [{'name': ' ', 'url_after': '?field=seeders&sorder=desc'}]}),			
	    'heb_movies': ('hebdub movies', '/usearch/heb%20dub%20category%3Amovies/?field=seeders&sorder=desc'),
			

    }

    baseurl = "http://kat.am"
    headers = [('User-Agent',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124' + \
                ' YaBrowser/14.10.2062.12061 Safari/537.36'),
               ('Referer', 'http://kickass.so/'), ('Accept-Encoding', 'gzip'), ('Accept-Language', 'he;q=0.8')]
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

    def isSort(self):
        return True

    def isSearchOption(self):
        return False

    def get_contentList(self, category, subcategory=None, apps_property=None):
        self.debug = self.log
        contentList = []
        url = self.get_url(category, subcategory, apps_property)

        response = self.makeRequest(url, headers=self.headers)

        if None != response and 0 < len(response):
            self.debug(response)
            if category:
                contentList = self.mode(response)
        self.debug(str(contentList))
        return contentList

    def mode(self, response):
        contentList = []
        num = 51
        good_forums = ['TV', 'Anime', 'Movies']
        regex = '''<tr class=".+?" id=.+?</tr>'''
        regex_tr = r'''<a data-download .+? href="(.+?)" class=".+?"><i.+?<a.+?<a.+?<a href="(.+?html)" class=".+?">(.+?)</a>.+? in <span.+?"><strong>.+?">(.+?)</a>.+?<td class="nobr center">(.+?)</td>.+?<td class="center".+?>(\d+&nbsp;.+?)</td>.+?<td class="green center">(\d+?)</td>.+?<td class="red lasttd center">(\d+?)</td>'''
        for tr in re.compile(regex, re.DOTALL).findall(response):
            result=re.compile(regex_tr, re.DOTALL).findall(tr)
            if result:
                (link, infolink, title, forum, size, date, seeds, leechers)=result[0]
            # main
                if forum in good_forums:
                    info = {}
                    num = num - 1
                    original_title = None
                    year = 0
                    img = ''
                    # info

                    info['label'] = info['title'] = self.unescape(title)
                    info['link'] = link
                    info['infolink'] = self.baseurl + infolink
                    size = self.unescape(self.stripHtml(size))
                    date = self.unescape(self.stripHtml(date))
                    info['plot'] = info['title'] + '\r\n[I](%s) [S/L: %s/%s] [/I]\r\nAge: %s' % (
                    size, seeds, leechers, date)

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
