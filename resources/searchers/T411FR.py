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
import os
import urllib
import tempfile
import sys

import SearcherABC


class T411FR(SearcherABC.SearcherABC):
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
    searchIcon = '/resources/searchers/icons/T411FR.png'

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

    headers = {('Origin', 'http://t411.io'),
                   ('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'http://t411.io/'),('X-NewRelic-ID','x='),
                   ('X-Requested-With','XMLHttpRequest'),}

    def search(self, keyword):
        filesList = []
        url='http://www.t411.io/torrents/search/?search=%s' % urllib.quote_plus(keyword.decode('utf-8').encode('cp1251'))
        url+='&order=seeders&type=desc'
        response = self.makeRequest(url, headers=self.headers)
        if None != response and 0 < len(response):
            #self.cookieJar.save(ignore_discard=True)
            #self.check_login(response)
            #print response
            regex = '''<a href="//.+?" title="(.+?)">.+?<span class="up">.+?<a href="/torrents/nfo/\?id=(\d+)" class="ajax nfo"></a>.+?</td>.+?<td align="center">.+?</td>.+?<td align="center">.+?</td>.+?<td align="center">(.+?)</td>.+?<td align="center" class="up">(\d+)</td>.+?<td align="center" class="down">(\d+)</td>'''
            for (title, link, size, seeds, leechers) in re.compile(regex, re.DOTALL).findall(response):
                title=self.clear_title(title)
                image = sys.modules["__main__"].__root__ + self.searchIcon
                link = 'http://www.t411.io/torrents/download/?id='+link
                filesList.append((
                    int(int(self.sourceWeight) * int(seeds)),
                    int(seeds), int(leechers), size,
                    title,
                    self.__class__.__name__ + '::' + link,
                    image,
                ))
        return filesList

    def clear_title(self, s):
        return self.stripHtml(self.unescape(s)).replace('   ',' ').replace('  ',' ').strip()

    def check_login(self, response=None):
        if None != response and 0 < len(response):
            #print response
            if re.compile('<input class="userInput"').search(response) or \
                    re.compile('start cache').search(response):
                print 'T411FR Not logged!'
                self.login()
                return False
        return True

    def getTorrentFile(self, url):
        content = self.makeRequest(url, headers=self.headers)
        #print content
        if not self.check_login(content):
            content = self.makeRequest(url, headers=self.headers)
        #return url
        return self.saveTorrentFile(url, content)

    def login(self):
        data = {
            'password': 'toraddon20',
            'login': 'zombitorrent',
            'remember':'1'
        }
        x=self.makeRequest(
            'http://www.t411.io/users/auth/',data=data, headers=self.headers)
        if re.search('{"status":"OK"',x):
            print 'LOGGED T411FR'
        self.cookieJar.save(ignore_discard=True)
        for cookie in self.cookieJar:
            if cookie.name == 'authKey' and cookie.domain=='.t411.io':
                return 'authKey=' + cookie.value
        return False