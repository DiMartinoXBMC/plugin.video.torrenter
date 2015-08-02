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

import os
import urllib
import json
import sys
from contextlib import contextmanager, closing, nested

import xbmc
import xbmcgui
import Downloader
import xbmcgui
import xbmcvfs
import Localization
from platform_pulsar import get_platform
import traceback
from btclient import *
from functions import calculate, showMessage, clearStorage, DownloadDB, get_ids_video, log, debug, is_writable
from argparse import Namespace
from Player import OverlayText
from Libtorrent import Libtorrent



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

class BTClientPlayer(xbmc.Player):
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
        log("[BTClientPlayer] Initalized")
        self.params = params
        self.get = self.params.get
        self.contentId = int(self.get("url"))
        self.platform = get_platform()
        self.init()

        self.torrent = Downloader.Torrent(self.userStorageDirectory, self.torrentUrl, self.torrentFilesDirectory).player
        self.lt=self.torrent.lt
        try:
            if self.get("url2"):
                self.ids_video = urllib.unquote_plus(self.get("url2")).split(',')
            else:
                self.ids_video = self.get_ids()
        except:
            pass

        args=Namespace(bt_download_limit=self.download_limit,#KB
                  bt_upload_limit=self.upload_limit,
                  choose_subtitles=False,
                  clear_older=0,
                  debug_log='',#os.path.join(self.userStorageDirectory, 'log.txt'),
                  delete_on_finish=False,
                  directory=self.userStorageDirectory,
                  listen_port_max=6891,#
                  listen_port_min=6881,
                  no_resume=False,
                  player='kodi',
                  port=5001,
                  print_pieces=False,
                  quiet=False,
                  stdin=False,
                  stream=True,
                  subtitles=None,
                  trace=False,
                  content_id=self.contentId,
                  url=self.torrentUrl)
        args=main(args) #config
        self.free_port = args.port
        log('BTClientPlayer: args '+str(args))

        self.btclient=self.stream(args, BTClient)

        #self.init()
        #self.setup_torrent()
        #if self.buffer():
        #    while True:
        #        if self.setup_play():
        #            debug('************************************* GOING LOOP')
        #            #self.torrent.continueSession(self.contentId)
        #            self.loop()
        #        else:
        #            break
        #        debug('************************************* GO NEXT?')
        #        if self.next_dl and self.next_dling and isinstance(self.next_contentId, int) and self.iterator == 100:
        #            self.contentId = self.next_contentId
        #            continue
        #        debug('************************************* NO! break')
        #        break
        #self.torrent.stopSession()
        #self.torrent.threadComplete = True
        #self.torrent.checkThread()

        #if '1' != self.__settings__.getSetting("keep_files") and 'Saved Files' not in self.userStorageDirectory:
        #    xbmc.sleep(1000)
        #    clearStorage(self.userStorageDirectory)
        #else:
        #    if self.seeding_status:
        #        showMessage(self.localize('Information'),
        #                    self.localize('Torrent is seeding. To stop it use Download Status.'), forced=True)
        #    else:
        #        if self.seeding: self.db_delete()
        #        showMessage(self.localize('Information'),
        #                    self.localize('Torrent downloading is stopped.'), forced=True)

    def on_exit(self):
        self.c.close()
        sys.exit(0)

    def stream(self, args, client_class):
        self.c = client_class(args.directory, args=args, lt=self.lt)
        try:
            while True:
                try:
                    s = socket.socket()
                    res = s.connect_ex(('127.0.0.1', self.free_port))
                    if res:
                        break
                finally:
                    s.close()
                self.free_port += 1

            self.server = StreamServer(('127.0.0.1', self.free_port), BTFileHandler, allow_range=True,
                                  status_fn=self.c.get_normalized_status)
            log('Started http server on port %d' % self.free_port)
            self.server.run()

            log('Starting btclient - libtorrent version %s' % self.lt.version)
            self.c.start_url(args.url)
            self.setup_torrent()

            if self.buffer():
                f = self.c._file
                self.server.set_file(f)
                self.setup_play()

                with closing(
                    OverlayText(w=OVERLAY_WIDTH, h=OVERLAY_HEIGHT, alignment=XBFONT_CENTER_X | XBFONT_CENTER_Y)) as overlay:
                    with nested(self.attach(overlay.show, self.on_playback_paused),
                                self.attach(overlay.hide, self.on_playback_resumed, self.on_playback_stopped)):
                        while True:
                            if xbmc.abortRequested or not self.isPlaying():
                                break

                            status = self.c.status
                            overlay.text = "\n".join(self._get_status_lines(status))
                            xbmc.sleep(1000)

            log('Play ended')
            if self.server:
                self.server.stop()
        except Exception:
            traceback.print_exc()
        finally:
            self.on_exit()

    def init(self):
        self.next_dl = True if self.__settings__.getSetting('next_dl') == 'true' and self.ids_video else False
        log('[BTClientPlayer]: init next_dl - ' + str(self.next_dl))
        self.next_contentId = False
        self.display_name = ''
        self.downloadedSize = 0
        self.dialog = xbmcgui.Dialog()
        self.on_playback_started = []
        self.on_playback_resumed = []
        self.on_playback_paused = []
        self.on_playback_stopped = []
        self.fullSize = 0
        if self.__settings__.getSetting("upload_limit") == "":
            self.upload_limit = 0.0
        else:
            self.upload_limit = float(self.__settings__.getSetting("upload_limit")) / 8 * 1024
        if self.__settings__.getSetting("download_limit") == "":
            self.download_limit = 0.0
        else:
            self.download_limit = float(self.__settings__.getSetting("download_limit")) / 8 * 1024

    def setup_torrent(self):
        if self.__settings__.getSetting('encryption') == 'true':
            self.c.encrypt()
        #if self.subs_dl:
        #    subs = self.torrent.getSubsIds(os.path.basename(self.torrent.getFilePath(self.contentId)))
        #    if len(subs) > 0:
        #        for ind, title in subs:
        #            self.torrent.continueSession(ind)

    def buffer(self):
        #iterator = 0
        progressBar = xbmcgui.DialogProgress()
        progressBar.create(self.localize('Please Wait') + str(' [%s]' % str(self.lt.version)),
                           self.localize('Seeds searching.'))
        while not self.c.is_file_ready: #iterator < 100:#or not self.torrent.is_playble()
            status = self.c.get_normalized_status()
            iterator = int(status['progress'] * 10000)
            if iterator > 99: iterator = 99
            if status['state'] in ['queued','checking','checking fastresume'] or (status['progress'] == 0 and status['num_pieces'] > 0):
                progressBar.update(iterator, self.localize('Checking preloaded files...'), ' ', ' ')
            elif status['state'] == 'downloading':
                dialogText = self.localize('Preloaded: ') + str(status['downloaded'] / 1024 / 1024) + ' MB / ' + str(
                    status['total_size'] / 1024 / 1024) + ' MB'
                peersText = ' [%s: %s; %s: %s]' % (
                    self.localize('Seeds'), str(status['seeds_connected']), self.localize('Peers'),
                    str(status['peers_connected']),)
                speedsText = '%s: %s Mbit/s; %s: %s Mbit/s' % (
                    self.localize('Downloading'), str(status['download_rate'] * 8 / 1000000),
                    self.localize('Uploading'), str(status['upload_rate'] * 8 / 1000000))
                #if self.debug:
                #    peersText=peersText + ' ' + self.torrent.get_debug_info('dht_state')
                #    dialogText=dialogText.replace(self.localize('Preloaded: '),'') + ' ' + self.torrent.get_debug_info('trackers_sum')
                progressBar.update(iterator, self.localize('Seeds searching.') + peersText, dialogText,
                                   speedsText)
            else:
                progressBar.update(iterator, self.localize('UNKNOWN STATUS'), ' ', ' ')
            if progressBar.iscanceled():
                self.c.close()
                break
            xbmc.sleep(1000)
        progressBar.update(0)
        progressBar.close()
        return True

    def setup_subs(self, label, path):
        iterator = 0
        subs = self.torrent.getSubsIds(label)
        debug('[setup_subs] subs: '+str(subs))
        if len(subs) > 0:
            showMessage(self.localize('Information'),
                        self.localize('Downloading and copy subtitles. Please wait.'), forced=True)
            for ind, title in subs:
                self.torrent.continueSession(ind)
            while iterator < 100:
                xbmc.sleep(1000)
                self.torrent.debug()
                status = self.torrent.torrentHandle.status()
                iterator = int(status.progress * 100)
            # xbmc.sleep(2000)
            for ind, title in subs:
                folder = title.split(os.sep)[0]
                temp = os.path.basename(title)
                addition = os.path.dirname(title).lstrip(folder + os.sep).replace(os.sep, '.').replace(' ', '_').strip()
                ext = temp.split('.')[-1]
                temp = temp[:len(temp) - len(ext) - 1] + '.' + addition + '.' + ext
                newFileName = os.path.join(os.path.dirname(path), temp)
                debug('[setup_subs]: '+str((os.path.join(os.path.dirname(os.path.dirname(path)),title),newFileName)))
                if not xbmcvfs.exists(newFileName):
                    xbmcvfs.copy(os.path.join(os.path.dirname(os.path.dirname(path)), title), newFileName)

    def setup_play(self):
        #self.next_dling = False
        #self.iterator = 0
        path = os.path.join(self.userStorageDirectory, self.c._file.path)
        label = os.path.basename(self.c._file.path)
        self.basename = label
        #self.seeding_run = False
        listitem = xbmcgui.ListItem(label)

        #if self.subs_dl:
        #    self.setup_subs(label, path)
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
                listitem = xbmcgui.ListItem(label)

                listitem.setInfo(type='video', infoLabels={'title': label,
                                                           'episode': int(self.episodeId),
                                                           'season': int(seasonId),
                                                           'tvshowtitle': title})
        except:
            log('[BTClientPlayer] Operation INFO failed!')

        thumbnail = self.get("thumbnail")
        if thumbnail:
            listitem.setThumbnailImage(urllib.unquote_plus(thumbnail))
        self.display_name = label

        base = 'http://127.0.0.1:' + str(self.free_port) + '/'
        url = urlparse.urljoin(base, urllib.quote(self.c._file.path))
        # мегакостыль!
        rpc = ({'jsonrpc': '2.0', 'method': 'Files.GetDirectory', 'params': {
            'media': 'video', 'directory': path}, 'id': 0})
        data = json.dumps(rpc)
        request = xbmc.executeJSONRPC(data)
        response = json.loads(request)
        while not response:
            xbmc.sleep(100)
        if response:
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            playlist.add(url, listitem)
            xbmc.Player().play(playlist)
        print "\nServing file on %s" % url
        return True

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

    def loop(self):
        debug_counter=0
        with closing(
                OverlayText(w=OVERLAY_WIDTH, h=OVERLAY_HEIGHT, alignment=XBFONT_CENTER_X | XBFONT_CENTER_Y)) as overlay:
            with nested(self.attach(overlay.show, self.on_playback_paused),
                        self.attach(overlay.hide, self.on_playback_resumed, self.on_playback_stopped)):
                while not xbmc.abortRequested and self.isPlaying() and not self.torrent.threadComplete:
                    self.torrent.checkThread()
                    if self.iterator == 100 and debug_counter < 100:
                        debug_counter += 1
                    else:
                        self.torrent.debug()
                        debug_counter=0
                    status = self.torrent.torrentHandle.status()
                    overlay.text = "\n".join(self._get_status_lines(status))
                    # downloadedSize = torrent.torrentHandle.file_progress()[contentId]
                    self.iterator = int(status.progress * 100)
                    xbmc.sleep(1000)
                    if self.iterator == 100 and self.next_dl:
                        next_contentId_index = self.ids_video.index(str(self.contentId)) + 1
                        if len(self.ids_video) > next_contentId_index:
                            self.next_contentId = int(self.ids_video[next_contentId_index])
                        else:
                            self.next_contentId = False
                            debug('[loop] next_contentId: '+str(self.next_contentId))
                    if not self.seeding_run and self.iterator == 100 and self.seeding:
                        self.seeding_run = True
                        self.seed(self.contentId)
                        self.seeding_status = True
                        # xbmc.sleep(7000)
                    if self.iterator == 100 and self.next_dl and not self.next_dling and isinstance(self.next_contentId,
                                                                                                    int) and self.next_contentId != False:
                        showMessage(self.localize('Torrent Downloading'),
                                    self.localize('Starting download next episode!'), forced=True)
                        self.torrent.stopSession()
                        # xbmc.sleep(1000)
                        path = self.torrent.getFilePath(self.next_contentId)
                        self.basename = self.display_name = os.path.basename(path)
                        self.torrent.continueSession(self.next_contentId)
                        self.next_dling = True

    def _get_status_lines(self, s):
        return [
            self.display_name.decode('utf-8'),
            "%.2f%% %s" % (s.progress * 100, self.localize(STATE_STRS[s.state]).decode('utf-8')),
            "D:%.2f%s U:%.2f%s S:%d P:%d" % (s.download_rate / 1024, self.localize('kb/s').decode('utf-8'),
                                             s.upload_rate / 1024, self.localize('kb/s').decode('utf-8'),
                                             s.num_seeds, s.num_peers)
        ]

    def db_delete(self):
        if self.basename:
            db = DownloadDB()
            get = db.get(self.basename)
            if get:
                db.delete(get[0])

    def seed(self, contentId):
        self.db_delete()
        exec_str = 'XBMC.RunPlugin(%s)' % \
                   ('%s?action=%s&url=%s&storage=%s&ind=%s') % \
                   (sys.argv[0], 'downloadLibtorrent', urllib.quote_plus(self.torrentUrl),
                    urllib.quote_plus(self.userStorageDirectory), str(contentId))
        xbmc.executebuiltin(exec_str)

    def get_ids(self):
        contentList = []
        for filedict in self.torrent.getContentList():
            contentList.append((filedict.get('title'), str(filedict.get('ind'))))
        contentList = sorted(contentList, key=lambda x: x[0])
        return get_ids_video(contentList)

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string
