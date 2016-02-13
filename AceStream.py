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

import os
import urllib2
import urllib
import hashlib
import re
import base64
from StringIO import StringIO
import gzip

from functions import file_decode, file_encode
from functions import magnet_alert, log, debug
import xbmcvfs


class AceStream:
    try:
        fpath = os.path.expanduser("~")
        pfile = os.path.join(fpath, 'AppData\Roaming\ACEStream\engine', 'acestream.port')
        gf = open(pfile, 'r')
        aceport = int(gf.read())
        gf.close()
        log('[AceStream]: aceport - '+str(aceport))
    except:
        aceport = 62062

    torrentFile = None
    magnetLink = None
    storageDirectory = ''
    torrentFilesDirectory = 'torrents'
    startPart = 0
    endPart = 0
    partOffset = 0
    torrentHandle = None
    session = None
    downloadThread = None
    threadComplete = False
    lt = None

    def __init__(self, storageDirectory='', torrentFile='', torrentFilesDirectory='torrents'):
        try:
            from ASCore import TSengine as tsengine

            log('Imported TSengine from ASCore')
        except Exception, e:
            log('Error importing TSengine from ASCore. Exception: ' + str(e))
            return

        self.TSplayer = tsengine()
        del tsengine
        self.torrentFilesDirectory = torrentFilesDirectory
        self.storageDirectory = storageDirectory
        _path = os.path.join(self.storageDirectory, self.torrentFilesDirectory) + os.sep
        if re.match("^magnet\:.+$", torrentFile):
            torrentFile = self.magnetToTorrent(torrentFile)
        if not xbmcvfs.exists(_path):
            xbmcvfs.mkdirs(_path)
        if xbmcvfs.exists(torrentFile):
            self.torrentFile = torrentFile
            content = xbmcvfs.File(torrentFile, "rb").read()
            self.torrentFileInfo = self.TSplayer.load_torrent(base64.b64encode(content), 'RAW')

    def __exit__(self):
        self.TSplayer.end()

    def play_url_ind(self, ind, label, icon):
        self.TSplayer.play_url_ind(int(ind), label, str(icon), '')

    def saveTorrent(self, torrentUrl):
        if re.match("^magnet\:.+$", torrentUrl):
            torrentFile = self.magnetToTorrent(torrentUrl)
            content = xbmcvfs.File(file_decode(torrentFile), "rb").read()
        else:
            torrentFile = self.storageDirectory + os.sep + self.torrentFilesDirectory + os.sep + self.md5(
                torrentUrl) + '.torrent'
            try:
                if not re.match("^http\:.+$", torrentUrl):
                    content = xbmcvfs.File(file_decode(torrentUrl), "rb").read()
                else:
                    request = urllib2.Request(torrentUrl)
                    request.add_header('Referer', torrentUrl)
                    request.add_header('Accept-encoding', 'gzip')
                    result = urllib2.urlopen(request)
                    if result.info().get('Content-Encoding') == 'gzip':
                        buf = StringIO(result.read())
                        f = gzip.GzipFile(fileobj=buf)
                        content = f.read()
                    else:
                        content = result.read()

                localFile = xbmcvfs.File(torrentFile, "w+b")
                localFile.write(content)
                localFile.close()
            except Exception, e:
                log('Unable to save torrent file from "' + torrentUrl + '" to "' + torrentFile +
                    '" in Torrent::saveTorrent' + '. Exception: ' + str(e))
                return
        if xbmcvfs.exists(torrentFile):
            self.torrentFile = torrentFile
            self.torrentFileInfo = self.TSplayer.load_torrent(base64.b64encode(content), 'RAW')
            return self.torrentFile

    def magnetToTorrent(self, magnet):
        try:
            from Libtorrent import Libtorrent
            torrent = Libtorrent(self.storageDirectory, magnet)
            torrent.magnetToTorrent(magnet)
            self.torrentFile = torrent.torrentFile
            log('[AceStream][magnetToTorrent]: self.torrentFile '+str(self.torrentFile))
            return self.torrentFile
        except:
            magnet_alert()
            exit()

    def getFilePath(self, contentId=0):
        fileList = self.getContentList()
        for i in fileList:
            if i['ind'] == contentId:
                return os.path.join(file_encode(self.storageDirectory), i['title'])

    def getContentList(self):
        filelist = []
        for k, v in self.TSplayer.files.iteritems():
            stringdata = {"title": urllib.unquote_plus(k), "ind": int(v)}
            filelist.append(stringdata)
        return filelist

    def md5(self, string):
        hasher = hashlib.md5()
        try:
            hasher.update(string)
        except:
            hasher.update(string.encode('utf-8', 'ignore'))
        return hasher.hexdigest()
