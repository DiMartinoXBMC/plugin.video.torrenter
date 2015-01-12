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
import sys

import SearcherABC


class NNMClubRu(SearcherABC.SearcherABC):
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 2

    '''
    Relative (from root directory of plugin) path to image
    will shown as source image at result listing
    '''
    searchIcon = '/resources/searchers/icons/nnm-club.ru.png'

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
        url = "http://nnm-club.me/forum/tracker.php"

        data = {
            'prev_sd': '0',
            'prev_a': '0',
            'prev_my': '0',
            'prev_n': '0',
            'prev_shc': '0',
            'prev_shf': '1',
            'prev_sha': '1',
            'prev_shs': '0',
            'prev_shr': '0',
            'prev_sht': '0',
            'o': '10',
            's': '2',
            'tm': '-1',
            'sd': '1',
            'shc': '1',
            'shs': '1',
            'ta': '-1',
            'sns': '-1',
            'sds': '-1',
            'nm': keyword.decode('utf-8').encode('cp1251'),
            'submit': '%CF%EE%E8%F1%EA'}

        headers = {('Origin', 'http://nnm-club.me'),
                   ('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'http://nnm-club.me/forum/tracker.php?def=1')}

        response = self.makeRequest(url, data=data, headers=headers)
        if None != response and 0 < len(response):
            response = response.decode('cp1251').encode('utf-8')
            #self.check_login(response)
            #print response
            forums = [24, 27, 23, 14, 26, 15]
            regex = '<a class="gen" href="tracker\.php\?c=(\d+)&nm=.+?href="viewtopic\.php\?t=(\d+)"><b>(.+?)</b>.+?<td align="center" nowrap="nowrap">(?=#</td>|<a href="download\.php\?id=(\d+)".+?</td>).+?<td .+?><u>\d+?</u> (.+?)</td>.+?<td.+?title="Seeders".+?<b>(\d+)</b>.+?<td .+?title="Leechers".+?<b>(\d+)</b>.+?</tr>'
            for (forum, topic, title, link, size, seeds, leechers) in re.compile(regex, re.DOTALL).findall(response):
                if int(forum) in forums and link not in ['', None]:
                    image = sys.modules["__main__"].__root__ + self.searchIcon
                    link = 'http://nnm-club.me/forum/download.php?id=' + link + '&' + topic
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
            if re.compile('<a href="login.php" class="mainmenu">').search(response):
                print 'NNM-Club Not logged!'
                self.login()
                return False
        return True

    def getTorrentFile(self, url):
        self.timeout(5)

        referer = 'http://nnm-club.me/forum/viewtopic.php?t=' + re.search('(\d+)$', url).group(1)
        #print url

        headers=[('Referer', referer)]
        content = self.makeRequest(url,headers=headers)

        if not self.check_login(content):
            content = self.makeRequest(url,headers=headers)

        return self.saveTorrentFile(url, content)

    def login(self):
        data = {
            'password': 'torrenter',
            'username': 'torrenter-plugin',
            'login': '%C2%F5%EE%E4',
            'redirect': 'index.php',
            'autologin': 'on'
        }
        self.makeRequest(
            'http://nnm-club.me/forum/login.php',
            data
        )
        self.cookieJar.save(ignore_discard=True)
        for cookie in self.cookieJar:
            if cookie.name == 'phpbb2mysql_4_sid' and cookie.domain=='.nnm-club.me':
                return 'phpbb2mysql_4_sid=' + cookie.value
        return False