# -*- coding: utf-8 -*-
'''
    Torrenter v2 plugin for XBMC/Kodi
    Copyright (C) 2012-2015 Vadim Skorba v1 - DiMartino v2
    https://forums.tvaddons.ag/addon-releases/29224-torrenter-v2.html

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
import tempfile
import hashlib
import os
from StringIO import StringIO
import zlib
import socket
import sys

proxy = int(sys.modules["__main__"].__settings__.getSetting("proxy"))
if proxy == 2:
    socks_ip = sys.modules["__main__"].__settings__.getSetting("socks_ip")
    from resources.proxy import socks
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, socks_ip,
                          int(sys.modules["__main__"].__settings__.getSetting("socks_port")))
    socket.socket = socks.socksocket
import urllib
import urllib2
import cookielib
import xbmcgui
import xbmc
import Localization
from functions import log, debug, showMessage

import ssl

#ssl._create_default_https_context = ssl._create_unverified_context
class SearcherABC:
    searchIcon = '/icons/video.png'
    sourceWeight = 1
    cookieJar = None
    timeout_multi=int(sys.modules["__main__"].__settings__.getSetting("timeout"))
    __plugin__='Empty v 0 0 0'
    baseurl = 'site.com'

    socket.setdefaulttimeout(10+(10*int(timeout_multi)))

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
        cookie=os.path.join(self.tempdir(), self.__class__.__name__+'.txt')
        self.cookieJar = cookielib.MozillaCookieJar(cookie)
        try:
            if os.path.exists(cookie): self.cookieJar.load(ignore_discard=True)
        except:
            self.log('[load_cookie]: os.remove(cookie)')
            os.remove(cookie)
            self.cookieJar = cookielib.MozillaCookieJar(cookie)

    def clear_cookie(self, domain):
        cookie=os.path.join(self.tempdir(),self.__class__.__name__+'.txt')
        self.cookieJar = cookielib.MozillaCookieJar(cookie)
        if os.path.exists(cookie):
            os.remove(cookie)
            self.log('[clear_cookie]: cookie cleared')

    def makeRequest(self, url, data={}, headers={}):
        self.load_cookie()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookieJar))
        if proxy == 1:
            try:
                from resources.proxy import antizapret
                opener.add_handler(antizapret.AntizapretProxyHandler())
                config = antizapret.config()
                self.debug('[antizapret]: '+str(config["domains"]))
                self.debug('[antizapret]: '+str(config["server"]))
            except:
                showMessage('AntiZapret', Localization.localize('Error'))
                self.debug('[antizapret]: OFF!')
        # python ssl Context support - PEP 0466
        if 'https:' in url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            log('urllib2.HTTPSHandler(context=ssl_context)')
            opener.add_handler(urllib2.HTTPSHandler(context=ssl_context))

        opener.addheaders = headers
        if 0 < len(data):
            encodedData = urllib.urlencode(data)
        else:
            encodedData = None
        try:
            response = opener.open(url, encodedData)
        except urllib2.HTTPError as e:
            if e.code == 404:
                self.log('[makeRequest]: Not Found! HTTP Error, e.code=' + str(e.code))
                return
            elif e.code in [503]:
                self.log('[makeRequest]: Denied, HTTP Error, e.code=' + str(e.code))
                return
            else:
                self.log('[makeRequest]: HTTP Error, e.code=' + str(e.code))
                return
        #self.cookieJar.extract_cookies(response, urllib2)
        #self.log(response.info().get('Set-Cookie'))
        if response.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(response.read())
            decomp = zlib.decompressobj(16 + zlib.MAX_WBITS)
            text = decomp.decompress(buf.getvalue())
        else:
            text = response.read()
        return text

    def askCaptcha(self, url):
        temp_dir = self.tempdir()
        if isinstance(temp_dir, list): temp_dir = temp_dir[0]
        urllib.URLopener().retrieve(url, temp_dir + '/captcha.png')
        window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
        if isinstance(temp_dir, list): temp_dir = temp_dir[0]
        image = xbmcgui.ControlImage(460, 20, 360, 160, temp_dir + '/captcha.png')
        window.addControl(image)
        keyboardCaptcha = xbmc.Keyboard('', '[%s] %s' % (self.__plugin__, Localization.localize('Input symbols from CAPTCHA image:')))
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
        ('"', '&#34;'),
        ("'", '&#39;'),
        ("&", '&#38;'),
        ("'", '&#039;'),
        ("&", '&#038;'),)

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
        localFileName = temp_dir + os.path.sep + self.md5(url) + ".torrent"

        localFile = open(localFileName, 'wb+')
        localFile.write(content)
        localFile.close()

        return localFileName

    def logout(self):
        pass

    def log(self, msg):
        log('[%s] ' % self.__plugin__ +msg)

    def debug(self, msg):
        debug('[%s] ' % self.__plugin__ +msg)

    def open2(self, url=''):
        import httplib
        conn = httplib.HTTPConnection(self.baseurl)
        conn.request("GET", str(url))
        r1 = conn.getresponse()
        status = str(r1.status) + " " + r1.reason
        content = r1.read()
        self.debug('[open2] status:'+str(status))
        return content

    def showMessage(self, heading, message, times=10000):
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (
            heading.replace('"', "'"), message.replace('"', "'"), times, self.searchIcon))
        self.log(str((heading.replace('"', "'"), message.replace('"', "'"), times, self.searchIcon)))