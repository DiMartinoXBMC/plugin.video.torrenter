# -*- coding: utf-8 -*-
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
from functions import calculate, showMessage, clearStorage, DownloadDB, cutFolder


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
        self._background = xbmcgui.ControlImage(x, y, w, h, os.path.join(RESOURCES_PATH, "images", "black.png"))
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
        res = tree.findall("./extension/res")[0]
        return int(res.attrib["width"]), int(res.attrib["height"])


class TorrentPlayer(xbmc.Player):
    __plugin__ = sys.modules["__main__"].__plugin__
    __settings__ = sys.modules["__main__"].__settings__
    ROOT = sys.modules["__main__"].__root__  #.decode('utf-8').encode(sys.getfilesystemencoding())
    USERAGENT = "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0"
    torrentFilesDirectory = 'torrents'
    debug = __settings__.getSetting('debug') == 'true'
    subs_dl = __settings__.getSetting('subs_dl') == 'true'
    seeding = __settings__.getSetting('keep_seeding') == 'true' and __settings__.getSetting('keep_files') == 'true'
    seeding_status=False
    seeding_run=False
    ids_video = None
    episodeId = None

    def __init__(self, userStorageDirectory, torrentUrl, params={}):
        self.userStorageDirectory = userStorageDirectory
        self.torrentUrl=torrentUrl
        xbmc.Player.__init__(self)
        print ("[TorrentPlayer] Initalized")
        self.params = params
        self.get = self.params.get
        self.contentId = int(self.get("url"))
        self.torrent = Downloader.Torrent(self.userStorageDirectory, self.torrentUrl, self.torrentFilesDirectory).player
        try:
            if self.get("url2"):
                self.ids_video = urllib.unquote_plus(self.get("url2")).split(',')
            else:
                self.ids_video = self.get_ids()
        except:
            pass
        self.init()
        self.setup_torrent()
        if self.buffer():
            while True:
                if self.setup_play():
                    #print '************************************* GOING LOOP'
                    self.torrent.continueSession(self.contentId)
                    self.loop()
                else:
                    break
                #print '************************************* GO NEXT?'
                if self.next_dl and self.next_dling and isinstance(self.next_contentId, int) and self.iterator == 100:
                    self.contentId = self.next_contentId
                    continue
                #print '************************************* NO! break'
                break

        self.torrent.stopSession()
        self.torrent.threadComplete = True
        self.torrent.checkThread()
        if 'false' == self.__settings__.getSetting("keep_files"):
            clearStorage(self.userStorageDirectory)
        else:
            if self.seeding_status:
                showMessage(Localization.localize('Information'),
                        Localization.localize('Torrent is seeding. To stop it use Download Status.'), forced=True)
            else:
                if self.seeding: self.db_delete()
                showMessage(Localization.localize('Information'),
                        Localization.localize('Torrent downloading is stopped.'), forced=True)

    def init(self):
        self.next_dl = True if self.__settings__.getSetting('next_dl') == 'true' and self.ids_video else False
        print str(self.next_dl)
        self.next_contentId = False
        self.display_name = ''
        self.downloadedSize = 0
        self.dialog = xbmcgui.Dialog()
        self.on_playback_started = []
        self.on_playback_resumed = []
        self.on_playback_paused = []
        self.on_playback_stopped = []

    def setup_torrent(self):
        self.torrent.startSession()
        upload_limit=self.__settings__.getSetting("upload_limit") if self.__settings__.getSetting("upload_limit")!="" else 0
        if 0 < int(upload_limit):
            self.torrent.setUploadLimit(int(upload_limit) * 1000000 / 8)  #MBits/second
        download_limit=self.__settings__.getSetting("download_limit") if self.__settings__.getSetting("download_limit")!="" else 0
        if 0 < int(download_limit):
            self.torrent.setDownloadLimit(
                int(download_limit) * 1000000 / 8)  #MBits/second
        self.torrent.status = False
        self.fullSize = self.torrent.getFileSize(self.contentId)
        Offset = calculate(self.fullSize)
        #print 'Offset: '+str(Offset)
        self.torrent.continueSession(self.contentId, Offset=Offset)

    def buffer(self):
        iterator = 0
        progressBar = xbmcgui.DialogProgress()
        progressBar.create(Localization.localize('Please Wait') + str(' [%s]' % str(self.torrent.lt.version)),
                           Localization.localize('Seeds searching.'))
        if self.subs_dl:
            subs=self.torrent.getSubsIds(os.path.basename(self.torrent.getFilePath(self.contentId)))
            if len(subs)>0:
                for ind, title in subs:
                    self.torrent.continueSession(ind)
        num_pieces=int(self.torrent.torrentFileInfo.num_pieces())
        while iterator < 100:
            xbmc.sleep(1000)
            self.torrent.debug()
            downloadedSize = self.torrent.torrentHandle.file_progress()[self.contentId]
            status = self.torrent.torrentHandle.status()
            iterator = int(status.progress * 100)
            if status.state == 0 or (status.progress == 0 and status.num_pieces > 0):
                iterator = int(status.num_pieces*100/num_pieces)
                if iterator > 99: iterator = 99
                progressBar.update(iterator, Localization.localize('Checking preloaded files...'), ' ', ' ')
            elif status.state == 3:
                dialogText = Localization.localize('Preloaded: ') + str(downloadedSize / 1024 / 1024) + ' MB / ' + str(
                    self.fullSize / 1024 / 1024) + ' MB'
                peersText = ' [%s: %s; %s: %s]' % (
                Localization.localize('Seeds'), str(self.torrent.getSeeds()), Localization.localize('Peers'),
                str(self.torrent.getPeers()),)
                speedsText = '%s: %s Mbit/s; %s: %s Mbit/s' % (
                Localization.localize('Downloading'), str(self.torrent.getDownloadRate() * 8 / 1000000),
                Localization.localize('Uploading'), str(self.torrent.getUploadRate() * 8 / 1000000))
                progressBar.update(iterator, Localization.localize('Seeds searching.') + peersText, dialogText,
                                   speedsText)
            else:
                progressBar.update(iterator, Localization.localize('UNKNOWN STATUS'), ' ', ' ')
            if progressBar.iscanceled():
                progressBar.update(0)
                progressBar.close()
                self.torrent.threadComplete = True
                self.torrent.checkThread()
                return
        progressBar.update(0)
        progressBar.close()
        return True

    def setup_subs(self, label, path):
        iterator=0
        subs=self.torrent.getSubsIds(label)
        #print str(subs)
        if len(subs)>0:
            showMessage(Localization.localize('Information'),
                                Localization.localize('Downloading and copy subtitles. Please wait.'), forced=True)
            for ind, title in subs:
                self.torrent.continueSession(ind)
            while iterator < 100:
                xbmc.sleep(1000)
                self.torrent.debug()
                status = self.torrent.torrentHandle.status()
                iterator = int(status.progress * 100)
            #xbmc.sleep(2000)
            for ind, title in subs:
                folder=title.split(os.sep)[0]
                temp=os.path.basename(title)
                addition=os.path.dirname(title).lstrip(folder+os.sep).replace(os.sep,'.').replace(' ','_').strip()
                ext=temp.split('.')[-1]
                temp = temp[:len(temp) - len(ext) - 1]+'.'+addition+'.'+ext
                newFileName=os.path.join(os.path.dirname(path),temp)
                #print str((os.path.join(os.path.dirname(os.path.dirname(path)),title),newFileName))
                if not xbmcvfs.exists(newFileName):
                    xbmcvfs.copy(os.path.join(os.path.dirname(os.path.dirname(path)),title),newFileName)

    def setup_play(self):
        self.next_dling = False
        self.iterator=0
        path = self.torrent.getFilePath(self.contentId)
        label = os.path.basename(path)
        self.basename=label
        self.seeding_run=False
        listitem = xbmcgui.ListItem(label, path=path)

        if self.subs_dl:
            self.setup_subs(label, path)
        try:
            seasonId = self.get("seasonId")
            self.episodeId = self.get("episodeId") if not self.episodeId else int(self.episodeId)+1
            title = urllib.unquote_plus(self.get("title")) if self.get("title") else None

            if self.get("label") and self.episodeId == self.get("episodeId"):
                label = urllib.unquote_plus(self.get("label"))
            elif seasonId and self.episodeId and title:
                label = '%s S%02dE%02d.%s (%s)' % (title, int(seasonId), int(self.episodeId), self.basename.split('.')[-1], self.basename)

            if seasonId and self.episodeId and label and title:
                listitem = xbmcgui.ListItem(label, path=path)

                listitem.setInfo(type='video', infoLabels={'title': label,
                                                           'episode': int(self.episodeId),
                                                           'season': int(seasonId),
                                                           'tvshowtitle': title})
        except:
            print '[TorrentPlayer] Operation INFO failed!'

        thumbnail = self.get("thumbnail")
        if thumbnail:
            listitem.setThumbnailImage(urllib.unquote_plus(thumbnail))
        self.display_name = label

        #мегакостыль!
        rpc = ({'jsonrpc': '2.0', 'method': 'Files.GetDirectory', 'params': {
            'media': 'video', 'directory': os.path.dirname(path)}, 'id': 0})
        data = json.dumps(rpc)
        request = xbmc.executeJSONRPC(data)
        response = json.loads(request)
        xbmc.sleep(300)

        if response:
            xbmc.Player().play(path, listitem)
            xbmc.sleep(3000)#very important, do not edit this, podavan
            return True

    def onPlayBackStarted(self):
        for f in self.on_playback_started:
            f()
        print(str(("video", "play", self.display_name)))

    def onPlayBackResumed(self):
        for f in self.on_playback_resumed:
            f()
        self.onPlayBackStarted()

    def onPlayBackPaused(self):
        for f in self.on_playback_paused:
            f()
        print(str(("video", "pause", self.display_name)))

    def onPlayBackStopped(self):
        for f in self.on_playback_stopped:
            f()
        print(str(("video", "stop", self.display_name)))

    @contextmanager
    def attach(self, callback, *events):
        for event in events:
            event.append(callback)
        yield
        for event in events:
            event.remove(callback)

    def loop(self):
        with closing(
                OverlayText(w=OVERLAY_WIDTH, h=OVERLAY_HEIGHT, alignment=XBFONT_CENTER_X | XBFONT_CENTER_Y)) as overlay:
            with nested(self.attach(overlay.show, self.on_playback_paused),
                        self.attach(overlay.hide, self.on_playback_resumed, self.on_playback_stopped)):
                while not xbmc.abortRequested and self.isPlaying() and not self.torrent.threadComplete:
                    self.torrent.checkThread()
                    self.torrent.debug()
                    status = self.torrent.torrentHandle.status()
                    overlay.text = "\n".join(self._get_status_lines(status))
                    #downloadedSize = torrent.torrentHandle.file_progress()[contentId]
                    self.iterator = int(status.progress * 100)
                    xbmc.sleep(1000)
                    if self.iterator == 100 and self.next_dl:
                        next_contentId_index = self.ids_video.index(str(self.contentId)) + 1
                        if len(self.ids_video) > next_contentId_index:
                            self.next_contentId = int(self.ids_video[next_contentId_index])
                        else:
                            self.next_contentId = False
                        print str(self.next_contentId)+'xxxxxx23'
                    if not self.seeding_run and self.iterator == 100 and self.seeding:
                        self.seeding_run=True
                        self.seed(self.contentId)
                        self.seeding_status=True
                        #xbmc.sleep(7000)
                    if self.iterator == 100 and self.next_dl and not self.next_dling and isinstance(self.next_contentId, int) and self.next_contentId!=False:
                        showMessage(Localization.localize('Torrent Downloading'),
                                    Localization.localize('Starting download next episode!'), forced=True)
                        self.torrent.stopSession()
                        #xbmc.sleep(1000)
                        path = self.torrent.getFilePath(self.next_contentId)
                        self.basename=self.display_name = os.path.basename(path)
                        self.torrent.continueSession(self.next_contentId)
                        self.next_dling = True

    def _get_status_lines(self, s):
        return [
            self.display_name.decode('utf-8'),
            "%.2f%% %s" % (s.progress * 100, Localization.localize(STATE_STRS[s.state]).decode('utf-8')),
            "D:%.2f%s U:%.2f%s S:%d P:%d" % (s.download_rate / 1000, Localization.localize('kb/s').decode('utf-8'),
                                             s.upload_rate / 1000, Localization.localize('kb/s').decode('utf-8'),
                                             s.num_seeds, s.num_peers)
        ]

    def db_delete(self):
        db=DownloadDB()
        get=db.get(self.basename)
        if get:
            db.delete(get[0])

    def seed(self, contentId):
        self.db_delete()
        exec_str='XBMC.RunPlugin(%s)' % \
                 ('%s?action=%s&url=%s&storage=%s&ind=%s') % \
                 (sys.argv[0], 'downloadLibtorrent', urllib.quote_plus(self.torrentUrl),
                  urllib.quote_plus(self.userStorageDirectory), str(contentId))
        xbmc.executebuiltin(exec_str)

    def get_ids(self):
        contentList = []
        #path=self.torrent.getContentList()[self.contentId]['title']
        #print path
        for filedict in self.torrent.getContentList():
            contentList.append((filedict.get('title'), str(filedict.get('ind'))))
        contentList = sorted(contentList, key=lambda x: x[0])
        #print str(contentList)

        #dirList, contentListNew = cutFolder(contentList)

        ids_video = []
        #print str(contentListNew)
        for title, identifier in contentList:
            try:
                ext = title.split('.')[-1]
                if ext.lower() in ['avi','mp4','mkv','flv','mov','vob','wmv','ogm','asx','mpg','mpeg','avc','vp3','fli','flc','m4v','iso']:
                    ids_video.append(str(identifier))
            except:
                pass

        #print 'get_ids:'+str(ids_video)
        return ids_video