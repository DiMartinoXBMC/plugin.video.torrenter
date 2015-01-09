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


class TFileME(SearcherABC.SearcherABC):
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
    searchIcon = '/resources/searchers/icons/TFileME.png'

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
        url='http://tfile.me/forum/ssearch.php?q=%s' % urllib.quote_plus(keyword.decode('utf-8').encode('cp1251'))
        url+='&c=2&f=4&f=1488&f=1379&f=1225&f=1331&f=1248&f=1197&f=1026&f=293&f=1227&f=577&f=298&f=297&f=290&f=299&f=230&f=303&f=292&f=1240&f=304&f=296&f=300&f=1332&f=1324&f=691&f=301&f=294&f=1241&f=498&f=367&f=574&f=1226&f=295&f=189&f=1525&f=1224&f=1388&f=1387&f=1276&f=1889&f=1917&f=1907&f=1908&f=1909&f=1910&f=1911&f=1890&f=1891&f=1892&f=1893&f=1912&f=1899&f=1894&f=1895&f=1903&f=1896&f=1897&f=1898&f=1900&f=1902&f=1901&f=1904&f=1905&f=1906&f=1913&f=15&f=1918&f=1374&f=1946&f=1579&f=1947&f=1242&f=1508&f=1165&f=1166&f=1245&f=1158&f=532&f=1167&f=1159&f=1244&f=1160&f=1173&f=1238&f=1678&f=1161&f=1320&f=1162&f=1246&f=496&f=1164&f=1163&f=1172&f=1243&f=1386&f=1312&f=1536&f=1919&f=1577&f=1989&f=1578&f=1554&f=1537&f=1538&f=1539&f=1540&f=1541&f=1542&f=1543&f=1555&f=1680&f=1544&f=1556&f=1545&f=1546&f=1547&f=1848&f=1548&f=1550&f=1620&f=1920&f=193&f=1968&f=1237&f=1420&f=1036&f=449&f=448&f=447&f=537&f=1170&f=37&f=1921&f=1323&f=1252&f=1685&f=697&f=172&f=311&f=183&f=130&f=1024&f=139&f=1023&f=179&f=392&f=308&f=342&f=1612&f=1015&f=96&f=353&f=997&f=285&f=154&f=1613&f=975&f=168&f=1849&f=1020&f=265&f=123&f=1614&f=1615&f=117&f=155&f=1611&f=1616&f=1617&f=152&f=105&f=312&f=127&f=1030&f=150&f=328&f=305&f=149&f=136&f=134&f=158&f=169&f=1421&f=768&f=767&f=309&f=377&f=1017&f=1590&f=1923&f=1591&f=1966&f=1592&f=1607&f=1593&f=1594&f=1595&f=1596&f=1597&f=1598&f=1599&f=1600&f=1844&f=1601&f=1602&f=1603&f=1604&f=1605&f=1681&f=17&f=1924&f=1415&f=1964&f=1416&f=1304&f=1146&f=1147&f=1156&f=1534&f=1142&f=29&f=85&f=1514&f=1148&f=1515&f=384&f=216&f=1149&f=232&f=1535&f=506&f=1517&f=1516&f=1000&f=1518&f=237&f=243&f=1150&f=244&f=239&f=197&f=236&f=1151&f=235&f=1152&f=234&f=1153&f=1018&f=1143&f=1563&f=1925&f=1564&f=1565&f=1566&f=1567&f=1568&f=1569&f=1570&f=1571&f=1572&f=1574&f=1575&f=1576&f=1926&f=175&f=1881&f=1256&f=1145&f=1140&f=1253&f=1157&f=727&f=1551&f=567&f=1254&f=219&f=568&f=974&f=495&f=743&f=494&f=401&f=731&f=499&f=500&f=538&f=206&f=1040&f=446&f=1005&f=210&f=203&f=207&f=204&f=1255&f=202&f=1141&f=16&f=1927&f=1380&f=1425&f=1438&f=1333&f=187&f=1062&f=1310&f=1059&f=1033&f=1509&f=1193&f=1195&f=1064&f=1063&f=1028&f=1058&f=1019&f=490&f=1397&f=1065&f=1419&f=1194&f=1070&f=274&f=1383&f=1334&f=1067&f=1068&f=1066&f=1069&f=1060&f=1282&f=19&f=1915&f=1872&f=1922&f=1284&f=1294&f=1301&f=1288&f=1291&f=1309&f=39&f=1285&f=1290&f=1306&f=1295&f=1300&f=1302&f=1287&f=1307&f=1292&f=1299&f=1297&f=1293&f=1888&f=1286&f=1298&f=1296&f=1519&f=1303&f=1527&g=&act=&y=&ql=&a=&d=&o=&size_min=0&size_max=0'
        headers = {('Origin', 'http://tfile.me'),
                   ('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'http://tfile.me/')}

        response = self.makeRequest(url, headers=headers)
        if None != response and 0 < len(response):
            response = response.decode('cp1251').encode('utf-8')
            self.cookieJar.save(ignore_discard=True)
            #self.check_login(response)
            #print response
            #bad_forums = [2,1,23,32,40,41]
            regex = '''<a href="/forum/viewforum\.php\?f=(\d+)">.+?<a href="/forum/viewtopic\.php\?t=.+?">(.+?)</a>.+?<a href="/forum/download\.php\?id=(\d+)">(.+?)</a>.+?class="sd">(\d+)</b>.+?class="lc">(\d+)'''
            for (forum, title, link, size, seeds, leechers) in re.compile(regex, re.DOTALL).findall(response):
                #if int(forum) not in bad_forums:
                title=self.clear_title(title)
                image = sys.modules["__main__"].__root__ + self.searchIcon
                link = 'http://tfile.me/forum/download.php?id='+link
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
            if re.compile('<input class="text" type="text" name="username"').search(response):
                print 'TFileME Not logged!'
                self.login()
                return False
        return True

    def getTorrentFile(self, url):
        self.timeout(5)
        self.check_login(self.makeRequest('http://tfile.me/'))
        content = self.makeRequest(url)
        #return url
        return self.saveTorrentFile(url, content)

    def login(self):
        data = {
            'password': 'torrenter',
            'username': 'torrenterpl',
            'login':'Вход'
        }
        x=self.makeRequest(
            'http://tfile.me/login/',
            data
        )
        self.cookieJar.save(ignore_discard=True)
        for cookie in self.cookieJar:
            if cookie.name == 'phpbb2mysql_data' and cookie.domain=='.tfile.me':
                return 'phpbb2mysql_data=' + cookie.value
        return False