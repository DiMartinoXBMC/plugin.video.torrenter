# -*- coding: utf-8 -*-
'''
    Torrenter v2 plugin for XBMC/Kodi
    Copyright (C) 2012-2015 Vadim Skorba v1 - DiMartino v2

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

import thread
import os
import urllib2
import hashlib
import re
from StringIO import StringIO
import gzip

import xbmc
import xbmcgui
import xbmcvfs
import Localization
from functions import file_encode, isSubtitle, DownloadDB, log, debug, is_writable, unquote


import os
import urllib
import json
import sys
from contextlib import contextmanager, closing, nested


from functions import calculate, showMessage, clearStorage, DownloadDB, get_ids_video, log, debug

from torrent2http import State, Engine, MediaType

ROOT = sys.modules["__main__"].__root__
RESOURCES_PATH = os.path.join(ROOT, 'resources')
TORRENT2HTTP_TIMEOUT = 20
TORRENT2HTTP_POLL = 1000
PLAYING_EVENT_INTERVAL = 60
MIN_COMPLETED_PIECES = 0.5

WINDOW_FULLSCREEN_VIDEO = 12005

XBFONT_LEFT = 0x00000000
XBFONT_RIGHT = 0x00000001
XBFONT_CENTER_X = 0x00000002
XBFONT_CENTER_Y = 0x00000004
XBFONT_TRUNCATED = 0x00000008
XBFONT_JUSTIFY = 0x00000010

STATE_STRS = [
    'Queued',
    'Checking',
    'Downloading metadata',
    'Downloading',
    'Finished',
    'Seeding',
    'Allocating',
    'Allocating file & Checking resume'
]

VIEWPORT_WIDTH = 1920.0
VIEWPORT_HEIGHT = 1088.0
OVERLAY_WIDTH = int(VIEWPORT_WIDTH * 0.7)  # 70% size
OVERLAY_HEIGHT = 150

ENCRYPTION_SETTINGS = {
    "Forced": 0,
    "Enabled": 1,
    "Disabled": 2,
}

class AnteoLoader:
    magnetLink = None
    engine = None
    torrentFile = None

    def __init__(self, storageDirectory='', torrentFile='', torrentFilesDirectory='torrents'):
        self.storageDirectory = storageDirectory
        self.torrentFilesPath = os.path.join(self.storageDirectory, torrentFilesDirectory) + os.sep
        if not is_writable(self.storageDirectory):
            xbmcgui.Dialog().ok(self.localize('Torrenter v2'),
                    self.localize('Your storage path is not writable or not local! Please change it in settings!'),
                    self.localize(self.storageDirectory))

            sys.exit(1)

        #pre settings
        if xbmcvfs.exists(torrentFile):
            self.torrentFile = "file:///"+torrentFile.replace('\\','//').replace('////','//')
        elif re.match("^magnet\:.+$", torrentFile):
            self.magnetLink = torrentFile

    def __exit__(self):
        log('on __exit__')
        if self.engine:
            self.engine.close()
            log('__exit__ worked!')

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string

    def getContentList(self):
        self.engine = Engine(uri=self.torrentFile)
        files = []
        filelist = []
        with closing(self.engine):
            self.engine.start()
            #media_types=[MediaType.VIDEO, MediaType.AUDIO, MediaType.SUBTITLES, MediaType.UNKNOWN]

            while not files and not xbmc.abortRequested:
                files = self.engine.list()
                self.engine.check_torrent_error()
                xbmc.sleep(200)

            for fs in files:
                stringdata = {"title": fs.name, "size": fs.size, "ind": fs.index,
                              'offset': fs.offset}
                filelist.append(stringdata)
        return filelist

    def saveTorrent(self, torrentUrl):
        if not xbmcvfs.exists(torrentUrl):
            if re.match("^magnet\:.+$", torrentUrl):
                self.magnetLink = torrentUrl
                self.magnetToTorrent(torrentUrl)
                self.magnetLink = None
                return self.torrentFile
            else:
                if not xbmcvfs.exists(self.torrentFilesPath):
                    xbmcvfs.mkdirs(self.torrentFilesPath)
                torrentFile = self.torrentFilesPath + self.md5(
                    torrentUrl) + '.torrent'
                try:
                    if not re.match("^http\:.+$", torrentUrl):
                        content = xbmcvfs.File(torrentUrl, "rb").read()
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
                    print 'Unable to save torrent file from "' + torrentUrl + '" to "' + torrentFile + '" in Torrent::saveTorrent' + '. Exception: ' + str(
                        e)
                    return
        else:
            torrentFile = torrentUrl
        if xbmcvfs.exists(torrentFile):
            self.torrentFile = "file:///"+torrentFile.replace('\\','//').replace('////','//')
            return self.torrentFile

    def md5(self, string):
        hasher = hashlib.md5()
        try:
            hasher.update(string)
        except:
            hasher.update(string.encode('utf-8', 'ignore'))
        return hasher.hexdigest()

    def magnetToTorrent(self, magnet):
        self.torrentFile = magnet

class AnteoPlayer(xbmc.Player):
    __plugin__ = sys.modules["__main__"].__plugin__
    __settings__ = sys.modules["__main__"].__settings__
    ROOT = sys.modules["__main__"].__root__  # .decode('utf-8').encode(sys.getfilesystemencoding())
    USERAGENT = "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0"
    torrentFilesDirectory = 'torrents'
    debug = __settings__.getSetting('debug') == 'true'
    subs_dl = __settings__.getSetting('subs_dl') == 'true'
    seeding = __settings__.getSetting('keep_seeding') == 'true' and __settings__.getSetting('keep_files') == '1'
    seeding_status = False
    seeding_run = False
    ids_video = None
    episodeId = None
    basename = ''

    def __init__(self, userStorageDirectory, torrentUrl, params={}):
        self.userStorageDirectory = userStorageDirectory
        self.torrentUrl = torrentUrl
        xbmc.Player.__init__(self)
        log("[TorrentPlayer] Initalized")
        self.params = params
        self.get = self.params.get
        self.contentId = int(self.get("url"))
        self.torrent = AnteoLoader(self.userStorageDirectory, self.torrentUrl, self.torrentFilesDirectory)
        try:
            if self.get("url2"):
                self.ids_video = urllib.unquote_plus(self.get("url2")).split(',')
            else:
                self.ids_video = self.get_ids()
        except:
            pass
        self.init()
        self.setup_engine()
        with closing(self.engine):
            self.engine.start(self.contentId)
            ready = self.buffer()
            if ready:
                self.stream()


    def __exit__(self):
        log('on __exit__')
        if self.engine:
            self.engine.close()
            log('__exit__ worked!')

    def init(self):
        self.next_dl = True if self.__settings__.getSetting('next_dl') == 'true' and self.ids_video else False
        log('[AnteoPlayer]: init - ' + str(self.next_dl))
        self.next_contentId = False
        self.display_name = ''
        self.downloadedSize = 0
        self.dialog = xbmcgui.Dialog()
        self.on_playback_started = []
        self.on_playback_resumed = []
        self.on_playback_paused = []
        self.on_playback_stopped = []
        if xbmcvfs.exists(self.torrentUrl):
            self.torrentUrl = "file:///"+str(self.torrentUrl).replace('\\','//').replace('////','//')

    def setup_engine(self):
        encryption = True if self.__settings__.getSetting('encryption') == 'true' else False

        upload_limit = self.__settings__.getSetting("upload_limit") if self.__settings__.getSetting(
            "upload_limit") != "" else 0
        download_limit = self.__settings__.getSetting("download_limit") if self.__settings__.getSetting(
            "download_limit") != "" else 0
        self.pre_buffer_bytes = 15*1024*1024
        self.engine = Engine(uri=self.torrentUrl)

    def buffer(self):
        ready = False
        progressBar = xbmcgui.DialogProgress()
        progressBar.create(self.localize('Please Wait'),
                           self.localize('Seeds searching.'))
        #if self.subs_dl:
        #    subs = self.torrent.getSubsIds(os.path.basename(self.torrent.getFilePath(self.contentId)))
        #    if len(subs) > 0:
        #        for ind, title in subs:
        #            self.torrent.continueSession(ind)

        #FileStatus = namedtuple('FileStatus', "name, save_path, url, size, offset, download, progress, index, media_type")

        #SessionStatus = namedtuple('SessionStatus', "name, state, state_str, error, progress, download_rate, upload_rate, "
        #                                    "total_download, total_upload, num_peers, num_seeds, total_seeds, "
        #                                    "total_peers")

        while not xbmc.abortRequested and not ready:
            xbmc.sleep(500)
            status = self.engine.status()
            self.engine.check_torrent_error(status)
            file_status = self.engine.file_status(self.contentId)
            if not file_status:
                continue
            log('[buffer] file_status:'+str(file_status))
            log('[buffer] status:'+str(status))
            #self.torrent.debug()
            fullSize = file_status.size / 1024 / 1024
            downloadedSize = status.total_download / 1024 / 1024
            getDownloadRate = status.download_rate / 1024 * 8
            getUploadRate = status.upload_rate / 1024 * 8
            getSeeds, getPeers = status.num_seeds, status.num_peers
            iterator = int(round(float(file_status.download) / self.pre_buffer_bytes, 2) * 100)
            if iterator > 99: iterator = 99
            if status.state == State.QUEUED_FOR_CHECKING:
                progressBar.update(iterator, self.localize('Checking preloaded files...'), ' ', ' ')
            elif status.state == State.DOWNLOADING:
                dialogText = self.localize('Preloaded: ') + "%d MB / %d MB" % \
                                                            (int(downloadedSize), int(fullSize))
                peersText = ' [%s: %s; %s: %s]' % (
                    self.localize('Seeds'), getSeeds, self.localize('Peers'), getPeers)
                speedsText = '%s: %d Mbit/s; %s: %d Mbit/s' % (
                    self.localize('Downloading'), int(getDownloadRate),
                    self.localize('Uploading'), int(getUploadRate))
                #if self.debug:
                #    peersText=peersText + ' ' + self.torrent.get_debug_info('dht_state')
                #    dialogText=dialogText.replace(self.localize('Preloaded: '),'') + ' ' + self.torrent.get_debug_info('trackers_sum')
                progressBar.update(iterator, self.localize('Seeds searching.') + peersText, dialogText,
                                   speedsText)

                if file_status.download >= self.pre_buffer_bytes:
                    ready = True
                    break
            elif status.state in [State.FINISHED, State.SEEDING]:
                    ready = True
                    break
            else:
                progressBar.update(iterator, self.localize('UNKNOWN STATUS'), ' ', ' ')
            if progressBar.iscanceled():
                ready = False
                break

        progressBar.update(0)
        progressBar.close()
        return ready

    def stream(self):
        file_status = self.engine.file_status(self.contentId)
        listitem = xbmcgui.ListItem('xxxx')
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        playlist.add(file_status.url, listitem)
        xbmc.Player().play(playlist)
        while not xbmc.abortRequested and xbmc.Player().isPlaying():
            xbmc.sleep(500)
        xbmc.Player().stop()

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string