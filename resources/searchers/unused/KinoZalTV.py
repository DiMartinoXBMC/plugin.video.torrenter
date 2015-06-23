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
import urllib
import sys

import SearcherABC


class KinoZalTV(SearcherABC.SearcherABC):
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 1

    '''
    Relative (from root directory of plugin) path to image
    will shown as source image at result listing
    '''
    searchIcon = '/resources/searchers/icons/KinoZalTV.png'

    '''
    Flag indicates is this source - magnet links source or not.
    Used for filtration of sources in case of old library (setting selected).
    Old libraries won't to convert magnet as torrent file to the storage
    '''

    @property
    def isMagnetLinkSource(self):
        return False

    '''
    Main method should be implemented for search process.
    Receives keyword and have to return dictionary of proper tuples:
    filesList.append((
        int(weight),# Calculated global weight of sources
        int(seeds),# Seeds count
        str(title),# Title will be shown
        str(link),# Link to the torrent/magnet
        str(image),# Path/URL to image shown at the list
    ))'''

    def search(self, keyword):
        filesList = []
        url = 'http://kinozal.tv/browse.php?s=%s&g=0&c=0&v=0&d=0&w=0&t=1&f=0' % urllib.quote_plus(
            keyword.decode('utf-8').encode('cp1251'))

        headers = {('Origin', 'http://kinozal.tv'),
                   ('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'http://kinozal.tv/')}

        response = self.makeRequest(url, headers=headers)
        if None != response and 0 < len(response):
            response = response.decode('cp1251').encode('utf-8')
            # print response
            bad_forums = [2, 1, 23, 32, 40, 41]
            regex = '''onclick="cat\((\d+)\);".+?<a href="/details\.php\?id=(\d+)".+?>(.+?)</a>.+?<td class='s'>(.+?)</td>.+?class='sl_s'>(\d+)</td>.+?class='sl_p'>(\d+)</td>'''
            for (forum, topic, title, size, seeds, leechers) in re.compile(regex, re.DOTALL).findall(response):
                if int(forum) not in bad_forums:
                    image = sys.modules["__main__"].__root__ + self.searchIcon
                    link = 'http://kinozal.tv/download.php?id=' + topic
                    filesList.append((
                        int(int(self.sourceWeight) * int(seeds)),
                        int(seeds), int(leechers), size,
                        self.unescape(self.stripHtml(title)),
                        self.__class__.__name__ + '::' + link,
                        image,
                    ))
        return filesList

    def check_login(self, response=None):
        if None != response and 0 < len(response):
            if re.compile('<html><head>').search(response):
                print 'KinoZal Not logged!'
                self.login()
                return False
        return True

    def getTorrentFile(self, url):
        self.timeout(5)

        content = self.makeRequest(url)
        # print content
        if not self.check_login(content):
            content = self.makeRequest(url)
            # print content

        return self.saveTorrentFile(url, content)

    def login(self):
        data = {
            'password': 'torrenter',
            'username': 'torrenterpl',
            'returnto:': ''
        }
        self.makeRequest(
            'http://kinozal.tv/takelogin.php',
            data
        )
        self.cookieJar.save(ignore_discard=True)
        for cookie in self.cookieJar:
            uid, passed = None, None
            if cookie.name == 'uid':
                uid = cookie.value
            if cookie.name == 'pass':
                passed = cookie.value
            if uid and passed:
                return 'uid=' + uid + '; pass=' + passed
        return False
