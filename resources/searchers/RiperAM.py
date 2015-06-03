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

import urllib
import re
import sys

import SearcherABC


class RiperAM(SearcherABC.SearcherABC):
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
    searchIcon = '/resources/searchers/icons/RiperAM.png'

    '''
    Flag indicates is this source - magnet links source or not.
    Used for filtration of sources in case of old library (setting selected).
    Old libraries won't to convert magnet as torrent file to the storage
    '''

    @property
    def isMagnetLinkSource(self):
        return True

    '''
    Main method should be implemented for search process.
    Receives keyword and have to return dictionary of proper tuples:
    filesList.append((
        int(weight),# Calculated global weight of sources
        int(seeds),# Seeds count
        str(title),# Title will be shown
        str(link),# Link to the torrent/magnet
        str(image),# Path/URL to image shown at the list
    ))
    '''

    def search(self, keyword):
        filesList = []

        url = "http://www.riper.am/search.php?sr=topics&sf=titleonly&fp=1&tracker_search=torrent&keywords=" + urllib.quote_plus(keyword)
            #keyword) + "&terms=all&fp=1&author=&fid%5B%5D=238&fid%5B%5D=368&fid%5B%5D=425&fid%5B%5D=50&fid%5B%5D=52&fid%5B%5D=424&fid%5B%5D=51&fid%5B%5D=371&fid%5B%5D=251&fid%5B%5D=349&fid%5B%5D=350&fid%5B%5D=351&fid%5B%5D=352&fid%5B%5D=239&fid%5B%5D=420&fid%5B%5D=12&fid%5B%5D=13&fid%5B%5D=423&fid%5B%5D=16&fid%5B%5D=17&fid%5B%5D=18&fid%5B%5D=46&fid%5B%5D=15&fid%5B%5D=14&fid%5B%5D=240&fid%5B%5D=19&fid%5B%5D=216&fid%5B%5D=363&fid%5B%5D=118&fid%5B%5D=153&fid%5B%5D=632&fid%5B%5D=319&fid%5B%5D=183&fid%5B%5D=178&fid%5B%5D=364&fid%5B%5D=267&fid%5B%5D=365&fid%5B%5D=353&fid%5B%5D=710&fid%5B%5D=266&fid%5B%5D=268&fid%5B%5D=160&fid%5B%5D=20&fid%5B%5D=210&fid%5B%5D=969&fid%5B%5D=707&fid%5B%5D=685&fid%5B%5D=1004&fid%5B%5D=1028&fid%5B%5D=711&fid%5B%5D=736&fid%5B%5D=550&fid%5B%5D=601&fid%5B%5D=979&fid%5B%5D=692&fid%5B%5D=1038&fid%5B%5D=48&fid%5B%5D=555&fid%5B%5D=781&fid%5B%5D=790&fid%5B%5D=791&fid%5B%5D=509&fid%5B%5D=803&fid%5B%5D=994&fid%5B%5D=735&fid%5B%5D=992&fid%5B%5D=748&fid%5B%5D=771&fid%5B%5D=656&fid%5B%5D=501&fid%5B%5D=980&fid%5B%5D=1002&fid%5B%5D=964&fid%5B%5D=746&fid%5B%5D=976&fid%5B%5D=958&fid%5B%5D=719&fid%5B%5D=1006&fid%5B%5D=798&fid%5B%5D=768&fid%5B%5D=984&fid%5B%5D=732&fid%5B%5D=376&fid%5B%5D=152&fid%5B%5D=628&fid%5B%5D=563&fid%5B%5D=565&fid%5B%5D=562&fid%5B%5D=797&fid%5B%5D=983&fid%5B%5D=774&fid%5B%5D=989&fid%5B%5D=354&fid%5B%5D=640&fid%5B%5D=684&fid%5B%5D=1024&fid%5B%5D=961&fid%5B%5D=639&fid%5B%5D=703&fid%5B%5D=1013&fid%5B%5D=1040&fid%5B%5D=131&fid%5B%5D=727&fid%5B%5D=1015&fid%5B%5D=641&fid%5B%5D=686&fid%5B%5D=644&fid%5B%5D=760&fid%5B%5D=373&fid%5B%5D=654&fid%5B%5D=779&fid%5B%5D=372&fid%5B%5D=957&fid%5B%5D=1016&fid%5B%5D=766&fid%5B%5D=687&fid%5B%5D=991&fid%5B%5D=272&fid%5B%5D=761&fid%5B%5D=653&fid%5B%5D=551&fid%5B%5D=645&fid%5B%5D=986&fid%5B%5D=795&fid%5B%5D=750&fid%5B%5D=635&fid%5B%5D=962&fid%5B%5D=683&fid%5B%5D=708&fid%5B%5D=978&fid%5B%5D=997&fid%5B%5D=1026&fid%5B%5D=787&fid%5B%5D=773&fid%5B%5D=671&fid%5B%5D=1019&fid%5B%5D=1023&fid%5B%5D=225&fid%5B%5D=799&fid%5B%5D=788&fid%5B%5D=680&fid%5B%5D=794&fid%5B%5D=972&fid%5B%5D=359&fid%5B%5D=756&fid%5B%5D=1000&fid%5B%5D=552&fid%5B%5D=706&fid%5B%5D=1003&fid%5B%5D=630&fid%5B%5D=966&fid%5B%5D=226&fid%5B%5D=960&fid%5B%5D=995&fid%5B%5D=699&fid%5B%5D=714&fid%5B%5D=755&fid%5B%5D=358&fid%5B%5D=642&fid%5B%5D=1039&fid%5B%5D=360&fid%5B%5D=981&fid%5B%5D=977&fid%5B%5D=681&fid%5B%5D=675&fid%5B%5D=988&fid%5B%5D=355&fid%5B%5D=1025&fid%5B%5D=973&fid%5B%5D=445&fid%5B%5D=678&fid%5B%5D=970&fid%5B%5D=733&fid%5B%5D=505&fid%5B%5D=646&fid%5B%5D=1031&fid%5B%5D=990&fid%5B%5D=691&fid%5B%5D=1033&fid%5B%5D=690&fid%5B%5D=1030&fid%5B%5D=804&fid%5B%5D=780&fid%5B%5D=778&fid%5B%5D=805&fid%5B%5D=500&fid%5B%5D=743&fid%5B%5D=21&fid%5B%5D=185&fid%5B%5D=463&fid%5B%5D=633&fid%5B%5D=772&fid%5B%5D=606&fid%5B%5D=789&fid%5B%5D=162&fid%5B%5D=151&fid%5B%5D=22&fid%5B%5D=198&fid%5B%5D=232&fid%5B%5D=245&fid%5B%5D=246&fid%5B%5D=592&fid%5B%5D=594&fid%5B%5D=591&fid%5B%5D=595&fid%5B%5D=596&fid%5B%5D=597&fid%5B%5D=242&fid%5B%5D=164&fid%5B%5D=167&fid%5B%5D=165&fid%5B%5D=166&fid%5B%5D=241&fid%5B%5D=23&fid%5B%5D=446&fid%5B%5D=366&fid%5B%5D=553&fid%5B%5D=693&fid%5B%5D=229&fid%5B%5D=967&fid%5B%5D=975&fid%5B%5D=491&fid%5B%5D=516&fid%5B%5D=1032&fid%5B%5D=528&fid%5B%5D=577&fid%5B%5D=770&fid%5B%5D=478&fid%5B%5D=534&fid%5B%5D=540&fid%5B%5D=674&fid%5B%5D=1010&fid%5B%5D=471&fid%5B%5D=593&fid%5B%5D=538&fid%5B%5D=744&fid%5B%5D=561&fid%5B%5D=526&fid%5B%5D=605&fid%5B%5D=713&fid%5B%5D=344&fid%5B%5D=459&fid%5B%5D=959&fid%5B%5D=191&fid%5B%5D=519&fid%5B%5D=527&fid%5B%5D=460&fid%5B%5D=190&fid%5B%5D=659&fid%5B%5D=477&fid%5B%5D=255&fid%5B%5D=256&fid%5B%5D=634&fid%5B%5D=574&fid%5B%5D=764&fid%5B%5D=637&fid%5B%5D=33&fid%5B%5D=270&fid%5B%5D=450&fid%5B%5D=514&fid%5B%5D=658&fid%5B%5D=209&fid%5B%5D=530&fid%5B%5D=800&fid%5B%5D=475&fid%5B%5D=517&fid%5B%5D=548&fid%5B%5D=740&fid%5B%5D=741&fid%5B%5D=737&fid%5B%5D=587&fid%5B%5D=718&fid%5B%5D=1011&fid%5B%5D=456&fid%5B%5D=682&fid%5B%5D=469&fid%5B%5D=479&fid%5B%5D=480&fid%5B%5D=696&fid%5B%5D=996&fid%5B%5D=189&fid%5B%5D=1027&fid%5B%5D=541&fid%5B%5D=785&fid%5B%5D=668&fid%5B%5D=560&fid%5B%5D=752&fid%5B%5D=533&fid%5B%5D=447&fid%5B%5D=775&fid%5B%5D=993&fid%5B%5D=529&fid%5B%5D=793&fid%5B%5D=586&fid%5B%5D=525&fid%5B%5D=522&fid%5B%5D=1018&fid%5B%5D=1020&fid%5B%5D=472&fid%5B%5D=769&fid%5B%5D=484&fid%5B%5D=1009&fid%5B%5D=971&fid%5B%5D=511&fid%5B%5D=531&fid%5B%5D=638&fid%5B%5D=269&fid%5B%5D=1017&fid%5B%5D=782&fid%5B%5D=754&fid%5B%5D=524&fid%5B%5D=228&fid%5B%5D=715&fid%5B%5D=559&fid%5B%5D=765&fid%5B%5D=636&fid%5B%5D=730&fid%5B%5D=679&fid%5B%5D=493&fid%5B%5D=545&fid%5B%5D=537&fid%5B%5D=792&fid%5B%5D=547&fid%5B%5D=731&fid%5B%5D=468&fid%5B%5D=588&fid%5B%5D=348&fid%5B%5D=539&fid%5B%5D=982&fid%5B%5D=747&fid%5B%5D=490&fid%5B%5D=536&fid%5B%5D=742&fid%5B%5D=544&fid%5B%5D=963&fid%5B%5D=457&fid%5B%5D=786&fid%5B%5D=520&fid%5B%5D=518&fid%5B%5D=575&fid%5B%5D=489&fid%5B%5D=495&fid%5B%5D=271&fid%5B%5D=496&fid%5B%5D=689&fid%5B%5D=515&fid%5B%5D=449&fid%5B%5D=492&fid%5B%5D=535&fid%5B%5D=1021&fid%5B%5D=1005&fid%5B%5D=1012&fid%5B%5D=783&fid%5B%5D=521&fid%5B%5D=470&fid%5B%5D=698&fid%5B%5D=451&fid%5B%5D=694&fid%5B%5D=697&fid%5B%5D=762&fid%5B%5D=677&fid%5B%5D=1008&fid%5B%5D=753&fid%5B%5D=497&fid%5B%5D=188&fid%5B%5D=494&fid%5B%5D=738&fid%5B%5D=767&fid%5B%5D=1034&fid%5B%5D=543&fid%5B%5D=448&fid%5B%5D=59&fid%5B%5D=279&fid%5B%5D=281&fid%5B%5D=1035&fid%5B%5D=280&fid%5B%5D=542&fid%5B%5D=676&fid%5B%5D=763&fid%5B%5D=576&fid%5B%5D=578&fid%5B%5D=579&fid%5B%5D=589&fid%5B%5D=580&fid%5B%5D=581&fid%5B%5D=582&fid%5B%5D=583&fid%5B%5D=584&fid%5B%5D=585&fid%5B%5D=24&fid%5B%5D=194&fid%5B%5D=69&fid%5B%5D=669&fid%5B%5D=704&fid%5B%5D=88&fid%5B%5D=379&fid%5B%5D=68&fid%5B%5D=65&fid%5B%5D=784&fid%5B%5D=729&fid%5B%5D=89&fid%5B%5D=701&fid%5B%5D=643&fid%5B%5D=532&fid%5B%5D=63&fid%5B%5D=590&fid%5B%5D=796&fid%5B%5D=652&fid%5B%5D=498&fid%5B%5D=614&fid%5B%5D=739&fid%5B%5D=801&fid%5B%5D=965&fid%5B%5D=974&fid%5B%5D=670&fid%5B%5D=650&fid%5B%5D=252&fid%5B%5D=649&fid%5B%5D=802&fid%5B%5D=647&fid%5B%5D=728&fid%5B%5D=452&fid%5B%5D=323&fid%5B%5D=998&fid%5B%5D=599&fid%5B%5D=333&fid%5B%5D=672&fid%5B%5D=655&fid%5B%5D=1014&fid%5B%5D=1007&fid%5B%5D=712&fid%5B%5D=673&fid%5B%5D=759&fid%5B%5D=758&fid%5B%5D=334&fid%5B%5D=999&fid%5B%5D=332&fid%5B%5D=660&fid%5B%5D=648&fid%5B%5D=331&fid%5B%5D=335&fid%5B%5D=327&fid%5B%5D=324&fid%5B%5D=705&fid%5B%5D=1029&fid%5B%5D=329&fid%5B%5D=336&fid%5B%5D=702&fid%5B%5D=328&fid%5B%5D=1022&fid%5B%5D=325&fid%5B%5D=337&fid%5B%5D=330&fid%5B%5D=326&fid%5B%5D=25&fid%5B%5D=127&fid%5B%5D=616&fid%5B%5D=201&fid%5B%5D=146&fid%5B%5D=145&fid%5B%5D=985&fid%5B%5D=661&fid%5B%5D=211&fid%5B%5D=192&fid%5B%5D=622&fid%5B%5D=346&fid%5B%5D=199&sc=1&sf=firstpost&sr=topics&sk=ts&sd=d&st=0&ch=300&t=0&submit=%D0%9F%D0%BE%D0%B8%D1%81%D0%BA"
        headers = [('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'http://www.riper.am/'), ]
        #('Cookie',str(sys.modules[ "__main__" ].__settings__.getSetting("rutor-auth")))]
        response = self.makeRequest(url, headers=headers)

        if None != response and 0 < len(response):
            self.cookieJar.save(ignore_discard=True)
            self.check_login(response)
            print response
            dat = re.compile(
                r'<a href="\.(/download/.+?)".+?<font size="3pt">(.+?)</font></a>.+?Размер: <b>(.+?)</b>.+?" title="Сидеров"><b>(\d+?)</b>.+?title="Личеров"><b>(\d+?)</b></span></dd>',
                re.DOTALL | re.I).findall(response)
            if dat:
                for (link, title, size, seeds, leechers) in dat:
                    torrentTitle = title
                    size = self.stripHtml(size)
                    link = 'http://www.riper.am' + link
                    image = sys.modules["__main__"].__root__ + self.searchIcon
                    filesList.append((
                        int(int(self.sourceWeight) * int(seeds)),
                        int(seeds), int(leechers), size,
                        self.unescape(self.stripHtml(torrentTitle)),
                        self.__class__.__name__ + '::' + link,
                        image,
                    ))
        return filesList

    def getTorrentFile(self, label):
        if re.search('/download/', label):
            return label
        elif label.startswith('http'):
            return self.getByLink(label)
        else:
            return self.getByLabel(label)


    def getByLink(self, label):
        response = self.makeRequest(label)
        if None != response and 0 < len(response):
            link = re.compile('(/download/file\.php\?id=\d+)',
                              re.DOTALL | re.MULTILINE).findall(response)[0]
            return 'http://www.riper.am' + link

    def login(self):
        data = {
            'password': 'torrenter',
            'username': 'torrenter-plugin',
            'remember':'1',
            'autologin':'on',
            #'redirect':'./ucp.php?mode=login',
            'sid':'593f325609a91bf52ed8c424cd0ef270',
            'redirect':'index.php',
            'login':urllib.quote_plus('Вход')
        }
        headers = [('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'http://www.riper.am/'), ]
        x=self.makeRequest(
            'http://www.riper.am/ucp.php?mode=login',data=data, headers=headers)
        if re.search('{"status":"OK"',x):
            print 'LOGGED RiperAM'
        self.cookieJar.save(ignore_discard=True)
        for cookie in self.cookieJar:
            if cookie.name == 'phpbb_63646738_sid' and cookie.domain=='.riper.am':
                return 'phpbb_63646738_sid=' + cookie.value
        return False

    def check_login(self, response=None):
        if None != response and 0 < len(response):
            #print response
            if re.compile('ucp.php\?mode=login" title="Вход"').search(response):
                print 'RiperAM Not logged!'
                self.login()
                return False
        print 'RiperAM logged!'
        return True