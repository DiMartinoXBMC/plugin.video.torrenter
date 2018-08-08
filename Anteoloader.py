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


import urllib2
import hashlib
import re
from StringIO import StringIO
import zlib

import xbmc
import xbmcgui
import xbmcvfs
import xbmcaddon
import Localization
from functions import localize_path, isSubtitle, loadsw_onstop, is_writable, file_url


import os
import urllib
import sys
from contextlib import contextmanager, closing, nested


from functions import foldername, showMessage, clearStorage, WatchedHistoryDB, get_ids_video, log, debug, ensure_str

from torrent2http import State, Engine, MediaType
author = 'Anteo'
__settings__ = xbmcaddon.Addon(id='script.module.torrent2http')
__version__ = __settings__.getAddonInfo('version')

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

class Encryption:
    FORCED = 0
    ENABLED = 1
    DISABLED = 2

class AnteoLoader:
    magnetLink = None
    engine = None
    torrentFile = None
    __plugin__ = sys.modules["__main__"].__plugin__
    __settings__ = sys.modules["__main__"].__settings__

    def __init__(self, storageDirectory='', torrentFile='', torrentFilesDirectory='torrents'):
        self.storageDirectory = storageDirectory
        self.torrentFilesPath = os.path.join(self.storageDirectory, torrentFilesDirectory) + os.sep
        if not is_writable(self.storageDirectory):
            xbmcgui.Dialog().ok(self.localize('Torrenter v2'),
                    self.localize('Your storage path is not writable or not local! Please change it in settings!'),
                    self.localize(self.storageDirectory))

            sys.exit(1)

        #pre settings
        if re.match("^magnet\:.+$", torrentFile):
            self.magnetLink = torrentFile
        else:
            self.torrentFile = torrentFile

    def setup_engine(self):
        encryption = Encryption.ENABLED if self.__settings__.getSetting('encryption') == 'true' else Encryption.DISABLED

        if self.__settings__.getSetting("connections_limit") not in ["",0,"0"]:
            connections_limit = int(self.__settings__.getSetting("connections_limit"))
        else:
            connections_limit = None

        use_random_port = True if self.__settings__.getSetting('use_random_port') == 'true' else False

        listen_port=int(self.__settings__.getSetting("listen_port")) if self.__settings__.getSetting(
            "listen_port") != "" else 6881

        if '1' != self.__settings__.getSetting("keep_files") and 'Saved Files' not in self.storageDirectory:
            keep_complete = False
            keep_incomplete = False
        else:
            keep_complete = True
            keep_incomplete = True

        dht_routers = ["router.bittorrent.com:6881", "router.utorrent.com:6881"]
        user_agent = ''
        self.engine = Engine(uri=file_url(localize_path(self.torrentFile)), download_path=self.storageDirectory,
                             connections_limit=connections_limit,
                             encryption=encryption, keep_complete=keep_complete, keep_incomplete=keep_incomplete,
                             dht_routers=dht_routers, use_random_port=use_random_port, listen_port=listen_port,
                             user_agent=user_agent)

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string

    def getContentList(self):
        try:
            from SkorbaLoader import SkorbaLoader
            torrent = SkorbaLoader(self.storageDirectory, self.torrentFile)
            return torrent.getContentList()
        except:
            import traceback
            log(traceback.format_exc())
            return self.getContentList_engine()

    def getContentList_engine(self):
        self.setup_engine()
        files = []
        filelist = []
        with closing(self.engine):
            self.engine.start()
            #media_types=[MediaType.VIDEO, MediaType.AUDIO, MediaType.SUBTITLES, MediaType.UNKNOWN]

            iterator = 0
            text = Localization.localize('Magnet-link is converting') if self.magnetLink\
                else Localization.localize('Opening torrent file')
            while not files and not xbmc.abortRequested and iterator < 100:
                files = self.engine.list()
                self.engine.check_torrent_error()
                if iterator==4:
                    progressBar = xbmcgui.DialogProgress()
                    progressBar.create(Localization.localize('Please Wait'),
                               Localization.localize('Magnet-link is converting'))
                elif iterator>4:
                    progressBar.update(iterator, Localization.localize('Please Wait'),text+'.' * (iterator % 4), ' ')
                    if progressBar.iscanceled():
                        progressBar.update(0)
                        progressBar.close()
                        return []
                xbmc.sleep(500)
                iterator += 1

            for fs in files:
                stringdata = {"title": ensure_str(fs.name), "size": fs.size, "ind": fs.index,
                              'offset': fs.offset}
                filelist.append(stringdata)
        return filelist

    def saveTorrent(self, torrentUrl):
        #if not xbmcvfs.exists(torrentUrl) or re.match("^http.+$", torrentUrl):
        if re.match("^magnet\:.+$", torrentUrl):
            self.magnetLink = torrentUrl
            self.magnetToTorrent(torrentUrl)
            self.magnetLink = None
            return self.torrentFile
        else:
            if not xbmcvfs.exists(self.torrentFilesPath): xbmcvfs.mkdirs(self.torrentFilesPath)
            torrentFile = os.path.join(self.torrentFilesPath, self.md5(torrentUrl) + '.torrent')
            try:
                if not re.match("^[htps]+?://.+$|^://.+$", torrentUrl):
                    log('xbmcvfs.File for %s' % torrentUrl)
                    content = xbmcvfs.File(torrentUrl, "rb").read()
                else:
                    log('request for %s' % torrentUrl)
                    content = self.makeRequest(torrentUrl)

                localFile = xbmcvfs.File(torrentFile, "w+b")
                localFile.write(content)
                localFile.close()
            except Exception, e:
                log('Unable to rename torrent file from %s to %s in AnteoLoader::saveTorrent. Exception: %s' %
                        (torrentUrl, torrentFile, str(e)))
                return
        if xbmcvfs.exists(torrentFile) and not os.path.exists(torrentFile):
            if not xbmcvfs.exists(self.torrentFilesPath): xbmcvfs.mkdirs(self.torrentFilesPath)
            torrentFile = os.path.join(self.torrentFilesPath, self.md5(torrentUrl) + '.torrent')
            xbmcvfs.copy(torrentUrl, torrentFile)
        if os.path.exists(torrentFile):
            self.torrentFile = torrentFile
            return self.torrentFile

    def makeRequest(self, torrentUrl):
        torrentUrl = re.sub('^://', 'http://', torrentUrl)
        x = re.search("://(.+?)/|://(.+?)$", torrentUrl)
        if x:
            baseurl = x.group(1) if x.group(1) else x.group(2)
        else:
            baseurl =''

        headers = [('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'http://%s/' % baseurl), ('Accept-encoding', 'gzip'), ]

        opener = urllib2.build_opener()
        opener.addheaders = headers
        result = opener.open(torrentUrl)
        if result.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(result.read())
            decomp = zlib.decompressobj(16 + zlib.MAX_WBITS)
            content = decomp.decompress(buf.getvalue())
        else:
            content = result.read()
        return content

    def md5(self, string):
        hasher = hashlib.md5()
        try:
            hasher.update(string)
        except:
            hasher.update(string.encode('utf-8', 'ignore'))
        return hasher.hexdigest()

    def magnetToTorrent(self, magnet):
        try:
            from SkorbaLoader import SkorbaLoader
            torrent = SkorbaLoader(self.storageDirectory, magnet)
            torrent.magnetToTorrent(magnet)
            self.torrentFile = torrent.torrentFile
        except:
            self.torrentFile = magnet
        log('[AnteoLoader][magnetToTorrent]: self.torrentFile '+ensure_str(self.torrentFile))

class AnteoPlayer(xbmc.Player):
    __plugin__ = sys.modules["__main__"].__plugin__
    __settings__ = sys.modules["__main__"].__settings__
    ROOT = sys.modules["__main__"].__root__
    USERAGENT = "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0"
    torrentFilesDirectory = 'torrents'
    debug = __settings__.getSetting('debug') == 'true'
    subs_dl = __settings__.getSetting('subs_dl') == 'true'
    seeding = __settings__.getSetting('keep_seeding') == 'true' and __settings__.getSetting('keep_files') == '1'
    seeding_status = False
    seeding_run = False
    ids_video = None
    episodeId = None
    fullSize = 0
    watchedTime = 0
    totalTime = 1
    seek = 0
    basename = ''

    def __init__(self, userStorageDirectory, torrentUrl, params={}):
        self.userStorageDirectory = userStorageDirectory
        self.torrentUrl = torrentUrl
        if not is_writable(self.userStorageDirectory):
            xbmcgui.Dialog().ok(Localization.localize('Torrenter v2'),
                    Localization.localize('Your storage path is not writable or not local! Please change it in settings!'),
                    self.storageDirectory)

            sys.exit(1)
        xbmc.Player.__init__(self)
        log("["+author+"Player] Initalized v"+__version__)
        self.params = params
        self.get = self.params.get
        self.contentId = int(self.get("url"))
        if self.get("seek"):
            self.seek = int(self.get("seek"))
        #self.torrent = AnteoLoader(self.userStorageDirectory, self.torrentUrl, self.torrentFilesDirectory)
        self.init()
        self.setup_engine()
        with closing(self.engine):
            self.engine.start(self.contentId)
            self.setup_nextep()
            while True:
                if self.buffer():
                    log('[AnteoPlayer]: ************************************* GOING LOOP')
                    if self.setup_play():
                        WatchedHistoryDB().add(self.basename, self.torrentUrl,
                                               foldername(self.getContentList()[self.contentId]['title']),
                                               self.watchedTime, self.totalTime, self.contentId, self.fullSize)
                        self.setup_subs()
                        self.loop()
                        WatchedHistoryDB().add(self.basename, self.torrentUrl, foldername(self.getContentList()[self.contentId]['title']), self.watchedTime, self.totalTime, self.contentId, self.fullSize)
                    else:
                        log('[AnteoPlayer]: ************************************* break')
                        break
                    log('[AnteoPlayer]: ************************************* GO NEXT?')
                    if self.next_dl and self.next_contentId != False and isinstance(self.next_contentId, int) and self.iterator == 100:
                        if not self.next_play:
                            xbmc.sleep(3000)
                            if not xbmcgui.Dialog().yesno(
                                self.localize('[%sPlayer v%s] ' % (author, __version__)),
                                self.localize('Would you like to play next episode?')):
                                break
                        self.contentId = self.next_contentId
                        continue

                    log('[AnteoPlayer]: ************************************* NO! break')
                    showMessage(self.localize('Information'),
                                self.localize('Stopping the torrent2http process...'))
                break

        xbmc.Player().stop()

        if '1' != self.__settings__.getSetting("keep_files") and 'Saved Files' not in self.userStorageDirectory:
            xbmc.sleep(1000)
            clearStorage(self.userStorageDirectory)

        showMessage(self.localize('Information'),
                    self.localize('torrent2http process stopped.'))

        loadsw_onstop()  # Reload Search Window

    def init(self):
        self.next_contentId = False
        self.display_name = ''
        self.downloadedSize = 0
        self.dialog = xbmcgui.Dialog()
        self.on_playback_started = []
        self.on_playback_resumed = []
        self.on_playback_paused = []
        self.on_playback_stopped = []
        self.torrentUrl = self.torrentUrl

    def setup_engine(self):

        encryption = Encryption.ENABLED if self.__settings__.getSetting('encryption') == 'true' else Encryption.DISABLED
        upload_limit = int(self.__settings__.getSetting("upload_limit"))*1024/8 if self.__settings__.getSetting(
            "upload_limit") != "" else 0
        download_limit = int(self.__settings__.getSetting("download_limit"))*1024/8 if self.__settings__.getSetting(
            "download_limit") != "" else 0

        if self.__settings__.getSetting("connections_limit") not in ["",0,"0"]:
            connections_limit = int(self.__settings__.getSetting("connections_limit"))
        else:
            connections_limit = None

        use_random_port = True if self.__settings__.getSetting('use_random_port') == 'true' else False

        listen_port=int(self.__settings__.getSetting("listen_port")) if self.__settings__.getSetting(
            "listen_port") != "" else 6881

        if '1' != self.__settings__.getSetting("keep_files") and 'Saved Files' not in self.userStorageDirectory:
            keep_complete = False
            keep_incomplete = False
            keep_files = False
            resume_file = None
        else:
            keep_complete = True
            keep_incomplete = True
            keep_files = True
            resume_file=os.path.join(self.userStorageDirectory, 'torrents', os.path.basename(self.torrentUrl)+'.resume_data')

        enable_dht = self.__settings__.getSetting("enable_dht") == 'true'
        dht_routers = ["router.bittorrent.com:6881","router.utorrent.com:6881"]
        user_agent = ''
        self.pre_buffer_bytes = int(self.__settings__.getSetting("pre_buffer_bytes"))*1024*1024

        self.engine = Engine(uri=file_url(self.torrentUrl), download_path=self.userStorageDirectory,
                             connections_limit=connections_limit, download_kbps=download_limit, upload_kbps=upload_limit,
                             encryption=encryption, keep_complete=keep_complete, keep_incomplete=keep_incomplete,
                             dht_routers=dht_routers, use_random_port=use_random_port, listen_port=listen_port,
                             keep_files=keep_files, user_agent=user_agent, resume_file=resume_file, enable_dht=enable_dht)

    def buffer(self):
        ready = False
        progressBar = xbmcgui.DialogProgress()
        progressBar.create('[%sPlayer v%s] ' % (author, __version__) + self.localize('Please Wait'),
                           self.localize('Seeds searching.'))

        while not xbmc.abortRequested and not ready:
            xbmc.sleep(500)
            status = self.engine.status()
            self.print_debug(status)
            #self.print_fulldebug()
            self.engine.check_torrent_error(status)
            file_status = self.engine.file_status(self.contentId)
            if not file_status:
                continue
            self.fullSize = int(file_status.size / 1024 / 1024)
            downloadedSize = status.total_download / 1024 / 1024
            getDownloadRate = status.download_rate / 1024 * 8
            getUploadRate = status.upload_rate / 1024 * 8
            getSeeds, getPeers = status.num_seeds, status.num_peers
            iterator = int(round(float(file_status.download) / self.pre_buffer_bytes, 2) * 100)
            if iterator > 99: iterator = 99
            if status.state == State.CHECKING_FILES:
                iterator = int(status.progress*100)
                if iterator > 99: iterator = 99
                progressBar.update(iterator, self.localize('Checking preloaded files...'), ' ', ' ')
            elif status.state == State.DOWNLOADING:
                dialogText = self.localize('Preloaded: ') + "%d MB / %d MB" % \
                                                            (int(downloadedSize), self.fullSize)
                peersText = ' [%s: %s; %s: %s]' % (
                    self.localize('Seeds'), getSeeds, self.localize('Peers'), getPeers)
                speedsText = '%s: %d Mbit/s; %s: %d Mbit/s' % (
                    self.localize('Downloading'), int(getDownloadRate),
                    self.localize('Uploading'), int(getUploadRate))
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
                self.iterator = 0
                ready = False
                break

        progressBar.update(0)
        progressBar.close()
        return ready

    def setup_nextep(self):
        try:
            if self.get("url2"):
                debug("[setup_nextep]: url2")
                self.ids_video = urllib.unquote_plus(self.get("url2")).split(',')
            else:
                debug("[setup_nextep]: not url2")
                self.ids_video = self.get_ids()
        except:
            pass

        if self.__settings__.getSetting('next_dl') == 'true' and self.ids_video and len(self.ids_video)>1:
            self.next_dl = True
        else:
            self.next_dl = False
        self.next_play = self.__settings__.getSetting('next_play') == 'true'
        log('[AnteoPlayer]: next_dl - %s, next_play - %s, ids_video - %s' % (str(self.next_dl), str(self.next_play), str(self.ids_video)))

    def setup_play(self):
        file_status = self.engine.file_status(self.contentId)
        self.iterator = 0
        self.watchedTime = 0
        self.totalTime = 1
        url = file_status.url
        label = os.path.basename(file_status.name)
        self.basename = label
        self.seeding_run = False
        listitem = xbmcgui.ListItem(label, path=url)

        if self.next_dl:
            next_contentId_index = self.ids_video.index(str(self.contentId)) + 1
            if len(self.ids_video) > next_contentId_index:
                self.next_contentId = int(self.ids_video[next_contentId_index])
            else:
                self.next_contentId = False
            log('[AnteoPlayer][setup_play]: next_contentId: '+str(self.next_contentId))
        try:
            seasonId = self.get("seasonId")
            self.episodeId = self.get("episodeId") if not self.episodeId else int(self.episodeId) + 1
            title = urllib.unquote_plus(self.get("title")) if self.get("title") else None

            if self.get("label") and self.episodeId == self.get("episodeId"):
                label = urllib.unquote_plus(self.get("label"))
            elif seasonId and self.episodeId and title:
                label = '%s S%02dE%02d.%s (%s)' % (
                title, int(seasonId), int(self.episodeId), self.basename.split('.')[-1], self.basename)

            if seasonId and self.episodeId and label and title:
                listitem = xbmcgui.ListItem(label, path=url)

                listitem.setInfo(type='video', infoLabels={'title': label,
                                                           'episode': int(self.episodeId),
                                                           'season': int(seasonId),
                                                           'tvshowtitle': title})
        except:
            log('[AnteoPlayer]: Operation INFO failed!')

        thumbnail = self.get("thumbnail")
        if thumbnail:
            listitem.setThumbnailImage(urllib.unquote_plus(thumbnail))
        self.display_name = label

        if self.get('listitem'):
            listitem = self.get('listitem')
            listitem.setPath(url)

        player = xbmc.Player()
        player.play(url, listitem)

        xbmc.sleep(2000)  # very important, do not edit this, podavan
        i = 0
        while not xbmc.abortRequested and not self.isPlaying() and i < 150:
            xbmc.sleep(200)
            i += 1

        log('[AnteoPlayer]: self.isPlaying() = %s, i = %d, xbmc.abortRequested - %s' % (str(self.isPlaying()), i, str(xbmc.abortRequested)))
        if not self.isPlaying() or xbmc.abortRequested:
            return False

        if self.seek > 0:
            log('[AnteoPlayer]: seekTime - '+str(self.seek))
            self.seekTime(self.seek)
        return True

    def setup_subs(self):
        if self.subs_dl:
            file_status = self.engine.file_status(self.contentId)
            subs = []
            filename = os.path.basename(file_status.name)
            sub_files = self.engine.list(media_types=[MediaType.SUBTITLES])
            for i in sub_files:
                if isSubtitle(filename, i.name):
                    subs.append(i)
            if subs:
                log("[AnteoPlayer][setup_subs]: Detected subtitles: %s" % str(subs))
                for sub in subs:
                    xbmc.Player().setSubtitles(sub.url)

    def loop(self):
        debug_counter = 0
        pause = True
        with closing(
                OverlayText(w=OVERLAY_WIDTH, h=OVERLAY_HEIGHT, alignment=XBFONT_CENTER_X | XBFONT_CENTER_Y)) as overlay:
            with nested(self.attach(overlay.show, self.on_playback_paused),
                        self.attach(overlay.hide, self.on_playback_resumed, self.on_playback_stopped)):
                while not xbmc.abortRequested and self.isPlaying():
                    #self.print_fulldebug()
                    status = self.engine.status()
                    file_status = self.engine.file_status(self.contentId)
                    self.watchedTime = xbmc.Player().getTime()
                    if self.iterator == 100 and debug_counter < 100:
                        debug_counter += 1
                    else:
                        self.totalTime = xbmc.Player().getTotalTime()
                        self.print_debug(status)
                        debug_counter=0

                    overlay.text = "\n".join(self._get_status_lines(status, file_status))

                    self.iterator = int(file_status.progress * 100)

                    if pause and self.__settings__.getSetting("pause_onplay") == 'true':
                        pause = False
                        xbmc.Player().pause()
                        log('[loop]: xbmc.Player().pause()')
                    xbmc.sleep(1000)

    def onPlayBackStarted(self):
        for f in self.on_playback_started:
            f()
        log('[onPlayBackStarted]: '+(str(("video", "play", self.display_name))))

    def onPlayBackResumed(self):
        for f in self.on_playback_resumed:
            f()
        self.onPlayBackStarted()

    def onPlayBackPaused(self):
        for f in self.on_playback_paused:
            f()
        log('[onPlayBackPaused]: '+(str(("video", "pause", self.display_name))))

    def onPlayBackStopped(self):
        for f in self.on_playback_stopped:
            f()
        log('[onPlayBackStopped]: '+(str(("video", "stop", self.display_name))))

    @contextmanager
    def attach(self, callback, *events):
        for event in events:
            event.append(callback)
        yield
        for event in events:
            event.remove(callback)

    def _get_status_lines(self, s, f):
        return [
            ensure_str(self.display_name),
            "%.2f%% %s" % (f.progress * 100, self.localize(STATE_STRS[s.state])),
            "D:%.2f%s U:%.2f%s S:%d P:%d" % (s.download_rate, self.localize('kb/s'),
                                             s.upload_rate, self.localize('kb/s'),
                                             s.num_seeds, s.num_peers)
        ]

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string

    def print_debug(self, status=None):
        #FileStatus = namedtuple('FileStatus', "name, save_path, url, size, offset, download, progress, index, media_type")

        #SessionStatus = namedtuple('SessionStatus', "name, state, state_str, error, progress, download_rate, upload_rate, "
        #                                    "total_download, total_upload, num_peers, num_seeds, total_seeds, "
        #                                    "total_peers")

        #log('[buffer] file_status:'+str(file_status))
        #log('[buffer] status:'+str(status))
        if not status:
            status = self.engine.status()
        self.engine.check_torrent_error(status)
        log('[AnteoPlayer]: %.2f%% complete (down: %.1f kb/s up: %.1f kb/s peers: %d) %s' % \
              (status.progress * 100, status.download_rate,
               status.upload_rate, status.num_peers, status.state_str))

    def print_fulldebug(self):
        status = self.engine.status()
        file_status = self.engine.file_status(self.contentId)
        log('[buffer] file_status:'+str(file_status))
        log('[buffer] status:'+str(status))

    def get_ids(self):
        contentList = []
        for fs in self.engine.list():
            contentList.append((fs.name, str(fs.index)))
        contentList = sorted(contentList, key=lambda x: x[0])
        return get_ids_video(contentList)

    def getContentList(self):
        filelist = []
        for fs in self.engine.list():
            stringdata = {"title": ensure_str(fs.name), "size": fs.size, "ind": fs.index,
                          'offset': fs.offset}
            filelist.append(stringdata)
        return filelist

class OverlayText(object):
    def __init__(self, w, h, *args, **kwargs):
        self.window = xbmcgui.Window(WINDOW_FULLSCREEN_VIDEO)
        viewport_w, viewport_h = self._get_skin_resolution()
        # Adjust size based on viewport, we are using 1080p coordinates
        w = int(w * viewport_w / VIEWPORT_WIDTH)
        h = int(h * viewport_h / VIEWPORT_HEIGHT)
        x = (viewport_w - w) / 2
        y = (viewport_h - h) / 2
        self._shown = False
        self._text = ""
        self._label = xbmcgui.ControlLabel(x, y, w, h, self._text, *args, **kwargs)
        filename = os.path.join(RESOURCES_PATH, "images", "black.png")
        self._background = xbmcgui.ControlImage(x, y, w, h, filename)
        self._background.setColorDiffuse("0xD0000000")

    def show(self):
        if not self._shown:
            self.window.addControls([self._background, self._label])
            self._shown = True
            self._background.setColorDiffuse("0xD0000000")

    def hide(self):
        if self._shown:
            self._shown = False
            self.window.removeControls([self._background, self._label])
            self._background.setColorDiffuse("0xFF000000")

    def close(self):
        self.hide()

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        if self._shown:
            self._label.setLabel(self._text)

    # This is so hackish it hurts.
    def _get_skin_resolution(self):
        import xml.etree.ElementTree as ET

        skin_path = xbmc.translatePath("special://skin/")
        tree = ET.parse(os.path.join(skin_path, "addon.xml"))
        res = None
        for element in tree.findall("./extension/res"):
            if element.attrib["default"] == 'true':
                res = element
                break
        if res is None: res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])