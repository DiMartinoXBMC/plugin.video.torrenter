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

import hashlib
import sys

from functions import log

class Torrent():
    __settings__ = sys.modules["__main__"].__settings__

    def __init__(self, storageDirectory='', torrentFile='', torrentFilesDirectory='torrents'):
        self.get_torrent_client()
        if self.player == 'libtorrent':
            import SkorbaLoader
            self.player = SkorbaLoader.SkorbaLoader(storageDirectory, torrentFile, torrentFilesDirectory)

        elif self.player == 'acestream':
            import AceStream
            self.player = AceStream.AceStream(storageDirectory, torrentFile, torrentFilesDirectory)

        elif self.player == 'anteo':
            import Anteoloader
            self.player = Anteoloader.AnteoLoader(storageDirectory, torrentFile, torrentFilesDirectory)
        
        elif self.player == 'inpos':
            import Inposloader
            self.player = Inposloader.InposLoader(storageDirectory, torrentFile, torrentFilesDirectory)

    def __exit__(self):
        self.player.__exit__()

    def get_torrent_client(self):
        player = self.__settings__.getSetting("torrent_player")
        if player == '0' or player == '4':
            self.player = 'libtorrent'
        elif player == '1':
            self.player = 'acestream'
        elif player == '2':
            self.player = 'anteo'
        elif player == '3':
            self.player = 'inpos'

    def play_url_ind(self, ind, label, icon):
        return self.player.play_url_ind(int(ind), label, str(icon))

    def saveTorrent(self, torrentUrl):
        return self.player.saveTorrent(torrentUrl)

    def getMagnetInfo(self):
        return self.player.getMagnetInfo()

    def magnetToTorrent(self, magnet):
        return self.player.magnetToTorrent(magnet)

    def getUploadRate(self):
        return self.player.getUploadRate()

    def getDownloadRate(self):
        return self.player.getDownloadRate()

    def getPeers(self):
        return self.player.getPeers()

    def getSeeds(self):
        return self.player.getSeeds()

    def getFileSize(self, contentId=0):
        return self.player.getFileSize(contentId)

    def getFilePath(self, contentId=0):
        return self.player.getFilePath(contentId)

    def getContentList(self):
        # print str(self.player.getContentList())
        return self.player.getContentList()

    def setUploadLimit(self, bytesPerSecond):
        return self.player.setUploadLimit(bytesPerSecond)

    def setDownloadLimit(self, bytesPerSecond):
        return self.player.setDownloadLimit(bytesPerSecond)

    def stopSession(self):
        return self.player.stopSession()

    def md5(self, string):
        hasher = hashlib.md5()
        try:
            hasher.update(string)
        except:
            hasher.update(string.encode('utf-8', 'ignore'))
        return hasher.hexdigest()

    def downloadProcess(self, contentId=None, encrytion=True):
        return self.player.downloadProcess(contentId, encrytion)

    def initSession(self):
        return self.player.initSession()

    def encryptSession(self):
        return self.player.encryptSession()

    def startSession(self):
        return self.player.startSession()

    def continueSession(self, contentId=0, Offset=155, seeding=True):
        return self.player.continueSession(contentId, Offset, seeding)

    def addToSeeding(self):
        return self.player.addToSeeding()

    def fetchParts(self):
        return self.player.fetchParts()

    def checkThread(self):
        return self.player.checkThread()

    def _makedirs(self, _path):
        return self.player._makedirs(_path)

    def debug(self):
        return self.player.debug()

    def dump(self, obj):
        for attr in dir(obj):
            try:
                log("'%s':'%s'," % (attr, getattr(obj, attr)))
            except:
                pass
