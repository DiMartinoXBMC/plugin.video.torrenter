# -*- coding: utf-8 -*-
'''
    Torrenter v2 plugin for XBMC/Kodi
    Copyright (C) 2012-2015 Vadim Skorba v1 - DiMartino v2
    http://forum.kodi.tv/showthread.php?tid=214366

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

import abc
import urllib
import urllib2
import cookielib
import re
import tempfile
import hashlib
import os
from StringIO import StringIO
import gzip
import socket
import sys

import xbmcgui
import xbmc
import Localization


class SearcherABC:
    __metaclass__ = abc.ABCMeta

    searchIcon = '/icons/video.png'
    sourceWeight = 1
    cookieJar = None
    timeout_multi=int(sys.modules["__main__"].__settings__.getSetting("timeout"))

    socket.setdefaulttimeout(10+(10*int(timeout_multi)))

    @abc.abstractmethod
    def search(self, keyword):
        '''
        Retrieve keyword from the input and return a list of tuples:
        filesList.append((
            int(weight),
            int(seeds),
            str(title),
            str(link),
            str(image),
        ))
        '''
        return

    @abc.abstractproperty
    def isMagnetLinkSource(self):
        return 'Should never see this'

    def getTorrentFile(self, url):
        return url

    def sizeConvert(self, sizeBytes):
        if long(sizeBytes) >= 1024 * 1024 * 1024:
            size = str(long(sizeBytes) / (1024 * 1024 * 1024)) + 'GB'
        elif long(sizeBytes) >= 1024 * 1024:
            size = str(long(sizeBytes) / (1024 * 1024)) + 'MB'
        elif sizeBytes >= 1024:
            size = str(long(sizeBytes) / 1024) + 'KB'
        else:
            size = str(long(sizeBytes)) + 'B'

        return size

    def check_login(self, response=None):
        return True

    def login(self):
        return True

    def load_cookie(self):
        cookie=os.path.join(self.tempdir(),'cookie.txt')
        self.cookieJar = cookielib.MozillaCookieJar(cookie)
        if os.path.exists(cookie): self.cookieJar.load(ignore_discard=True)

    def makeRequest(self, url, data={}, headers={}):
        self.load_cookie()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))
        opener.addheaders = headers
        if 0 < len(data):
            encodedData = urllib.urlencode(data)
        else:
            encodedData = None
        try:
            response = opener.open(url, encodedData)
        except urllib2.HTTPError as e:
            if e.code == 404:
                print self.__class__.__name__+' [makeRequest]: Not Found! HTTP Error, e.code=' + str(e.code)
                return
            elif e.code in [503]:
                print self.__class__.__name__+' [makeRequest]: Denied, HTTP Error, e.code=' + str(e.code)
                return
            else:
                print self.__class__.__name__+' [makeRequest]: HTTP Error, e.code=' + str(e.code)
                return
        #self.cookieJar.extract_cookies(response, urllib2)
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(response.read())
            f = gzip.GzipFile(fileobj=buf)
            response = f.read()
        else:
            response = response.read()
        return response

    def askCaptcha(self, url):
        temp_dir = tempfile.gettempdir()
        if isinstance(temp_dir, list): temp_dir = temp_dir[0]
        urllib.URLopener().retrieve(url, temp_dir + '/captcha.png')
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        temp_dir = tempfile.gettempdir()
        if isinstance(temp_dir, list): temp_dir = temp_dir[0]
        image = xbmcgui.ControlImage(460, 20, 360, 160, temp_dir + '/captcha.png')
        window.addControl(image)
        keyboardCaptcha = xbmc.Keyboard('', Localization.localize('Input symbols from CAPTCHA image:'))
        keyboardCaptcha.doModal()
        captchaText = keyboardCaptcha.getText()
        window.removeControl(image)
        if not captchaText:
            return False
        else:
            return captchaText

    htmlCodes = (
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ('"', '&quot;'),
        ("'", '&#39;'),
        ("&", '&#38;'),)

    stripPairs = (
        ('<p>', '\n'),
        ('<li>', '\n'),
        ('<br>', '\n'),
        ('<.+?>', ' '),
        ('</.+?>', ' '),
        ('&nbsp;', ' '),
        ('&laquo;', '"'),
        ('&raquo;', '"'),
    )

    def unescape(self, string):
        for (symbol, code) in self.htmlCodes:
            string = re.sub(code, symbol, string)
        return string

    def stripHtml(self, string):
        for (html, replacement) in self.stripPairs:
            string = re.sub(html, replacement, string)
        return string

    def md5(self, string):
        hasher = hashlib.md5()
        hasher.update(string)
        return hasher.hexdigest()

    def tempdir(self):
        dirname = xbmc.translatePath('special://temp')
        for subdir in ('xbmcup', 'plugin.video.torrenter'):
            dirname = os.path.join(dirname, subdir)
            if not os.path.exists(dirname):
                os.mkdir(dirname)
        return dirname

    def timeout(self, add_seconds=0):
        seconds=10+(10*int(self.timeout_multi))+int(add_seconds)
        socket.setdefaulttimeout(int(seconds))

    def clean(self, string):
        specials = ['/', '\\', '-', '[', ']', '(', ')', ',']
        for symbol in specials:
            string = string.replace(symbol, ' ')
        if len(string) > 120:
            string = string[:120]
            last_piece = string.split(' ')[-1]
            string = string[:120 - len(last_piece)].strip()
        return string

    def saveTorrentFile(self, url, content):
        try:
            temp_dir = tempfile.gettempdir()
        except:
            temp_dir = self.tempdir()
        localFileName = temp_dir + os.path.sep + self.md5(url)

        localFile = open(localFileName, 'wb+')
        localFile.write(content)
        localFile.close()

        return localFileName

    def logout(self):
        pass