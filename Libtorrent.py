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
from functions import file_decode, file_encode, isSubtitle, DownloadDB, log, debug
from platform_pulsar import get_platform


class Libtorrent:
    torrentFile = None
    magnetLink = None
    storageDirectory = ''
    startPart = 0
    endPart = 0
    partOffset = 0
    torrentHandle = None
    session = None
    downloadThread = None
    threadComplete = False
    lt = None

    def __init__(self, storageDirectory='', torrentFile='', torrentFilesDirectory='torrents'):
        self.platform = get_platform()
        try:
            import libtorrent

            print '[Torrenter v2]: Imported libtorrent v' + libtorrent.version + ' from system'
        except Exception, e:
            print '[Torrenter v2]: Error importing from system. Exception: ' + str(e)
            from python_libtorrent import get_libtorrent
            libtorrent=get_libtorrent()

        try:
            self.lt = libtorrent
            del libtorrent
            print '[Torrenter v2]: Imported libtorrent v' + self.lt.version + ' from python_libtorrent.' + self.platform[
                    'system']
        except Exception, e:
            print '[Torrenter v2]: Error importing python_libtorrent.' + self.platform['system'] + '. Exception: ' + str(e)
            xbmcgui.Dialog().ok(Localization.localize('Python-Libtorrent Not Found'),
                                Localization.localize(self.platform["message"][0]),
                                Localization.localize(self.platform["message"][1]))
            return

        self.storageDirectory = storageDirectory
        self.torrentFilesPath = os.path.join(self.storageDirectory, torrentFilesDirectory) + os.sep
        if xbmcvfs.exists(torrentFile):
            self.torrentFile = torrentFile
            self.torrentFileInfo = self.lt.torrent_info(file_decode(self.torrentFile))
        elif re.match("^magnet\:.+$", torrentFile):
            self.magnetLink = torrentFile

    def saveTorrent(self, torrentUrl):
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
                print 'Unable to save torrent file from "' + torrentUrl + '" to "' + torrentFile + '" in Torrent::saveTorrent' + '. Exception: ' + str(
                    e)
                return
            if xbmcvfs.exists(torrentFile):
                try:
                    self.torrentFileInfo = self.lt.torrent_info(file_decode(torrentFile))
                except Exception, e:
                    print 'Exception: ' + str(e)
                    xbmcvfs.delete(torrentFile)
                    return
                baseName = file_encode(os.path.basename(self.getFilePath()))
                if not xbmcvfs.exists(self.torrentFilesPath):
                    xbmcvfs.mkdirs(self.torrentFilesPath)
                newFile = self.torrentFilesPath + self.md5(baseName) + '.' + self.md5(
                    torrentUrl) + '.torrent'  # + '.'+ baseName
                if xbmcvfs.exists(newFile):
                    xbmcvfs.delete(newFile)
                if not xbmcvfs.exists(newFile):
                    try:
                        xbmcvfs.rename(torrentFile, newFile)
                    except Exception, e:
                        print 'Unable to rename torrent file from "' + torrentFile + '" to "' + newFile + '" in Torrent::renameTorrent' + '. Exception: ' + str(
                            e)
                        return
                self.torrentFile = newFile
                if not self.torrentFileInfo:
                    self.torrentFileInfo = self.lt.torrent_info(file_decode(self.torrentFile))
                return self.torrentFile

    def getMagnetInfo(self):
        magnetSettings = {
            'save_path': self.storageDirectory,
            'storage_mode': self.lt.storage_mode_t(0),
            'paused': True,
            'auto_managed': True,
            'duplicate_is_error': True
        }
        progressBar = xbmcgui.DialogProgress()
        progressBar.create(Localization.localize('Please Wait'), Localization.localize('Magnet-link is converting'))
        self.torrentHandle = self.lt.add_magnet_uri(self.session, self.magnetLink, magnetSettings)
        iterator = 0
        while iterator < 100:
            xbmc.sleep(500)
            progressBar.update(iterator, Localization.localize('Please Wait'), Localization.localize('Magnet-link is converting')+'.' * (iterator % 4), ' ')
            iterator += 1
            if progressBar.iscanceled():
                progressBar.update(0)
                progressBar.close()
                return
            if self.torrentHandle.has_metadata():
                iterator = 100
        progressBar.update(0)
        progressBar.close()
        if self.torrentHandle.has_metadata():
            return self.torrentHandle.get_torrent_info()

    def magnetToTorrent(self, magnet):
        self.magnetLink = magnet
        self.initSession()
        torrentInfo = self.getMagnetInfo()
        try:
            torrentFile = self.lt.create_torrent(torrentInfo)
            baseName = os.path.basename(self.storageDirectory + os.sep + torrentInfo.files()[0].path)
            if not xbmcvfs.exists(self.torrentFilesPath):
                xbmcvfs.mkdirs(self.torrentFilesPath)
            self.torrentFile = self.torrentFilesPath + self.md5(baseName) + '.torrent'
            torentFileHandler = xbmcvfs.File(self.torrentFile, "w+b")
            torentFileHandler.write(self.lt.bencode(torrentFile.generate()))
            torentFileHandler.close()
            self.torrentFileInfo = self.lt.torrent_info(file_decode(self.torrentFile))
        except:
            xbmc.executebuiltin("Notification(%s, %s, 7500)" % (Localization.localize('Error'), Localization.localize(
                'Can\'t download torrent, probably no seeds available.')))
            self.torrentFileInfo = torrentInfo

    def getUploadRate(self):
        if None == self.torrentHandle:
            return 0
        else:
            return self.torrentHandle.status().upload_payload_rate

    def getDownloadRate(self):
        if None == self.torrentHandle:
            return 0
        else:
            return self.torrentHandle.status().download_payload_rate

    def getPeers(self):
        if None == self.torrentHandle:
            return 0
        else:
            return self.torrentHandle.status().num_peers

    def getSeeds(self):
        if None == self.torrentHandle:
            return 0
        else:
            return self.torrentHandle.status().num_seeds

    def getFileSize(self, contentId=0):
        return self.getContentList()[contentId]['size']

    def getFilePath(self, contentId=0):
        return os.path.join(self.storageDirectory, self.getContentList()[contentId]['title'])  # .decode('utf8')

    def getContentList(self):
        filelist = []
        for contentId, contentFile in enumerate(self.torrentFileInfo.files()):
            stringdata = {"title": contentFile.path, "size": contentFile.size, "ind": int(contentId),
                          'offset': contentFile.offset}
            filelist.append(stringdata)
        return filelist

    def getSubsIds(self, filename):
        subs = []
        for i in self.getContentList():
            if isSubtitle(filename, i['title']):
                subs.append((i['ind'], i['title']))
        return subs

    def setUploadLimit(self, bytesPerSecond):
        self.session.set_upload_rate_limit(int(bytesPerSecond))

    def setDownloadLimit(self, bytesPerSecond):
        self.session.set_download_rate_limit(int(bytesPerSecond))

    def md5(self, string):
        hasher = hashlib.md5()
        try:
            hasher.update(string)
        except:
            hasher.update(string.encode('utf-8', 'ignore'))
        return hasher.hexdigest()

    def downloadProcess(self, contentId, encrytion=True):
        self.initSession()
        if encrytion:
            self.encryptSession()
        self.startSession()
        self.paused = False
        db = DownloadDB()
        ContentList = self.getContentList()
        if contentId != None: contentId = int(contentId)
        if len(ContentList) == 1 or contentId not in [None, -1]:
            if not contentId: contentId = 0
            title = os.path.basename(ContentList[contentId]['title'])
            path = os.path.join(self.storageDirectory, ContentList[contentId]['title'])
            type = 'file'
        else:
            contentId = -1
            title = ContentList[0]['title'].split('\\')[0]
            path = os.path.join(self.storageDirectory, title)
            type = 'folder'

        add = db.add(title, path, type, {'progress': 0}, 'downloading', self.torrentFile, contentId,
                     self.storageDirectory)
        get = db.get(title)
        if add or get[5] == 'stopped':
            if get[5] == 'stopped':
                db.update_status(get[0], 'downloading')
            if contentId not in [None, -1]:
                self.continueSession(int(contentId), Offset=0, seeding=False)
            else:
                for i in range(self.torrentFileInfo.num_pieces()):
                    self.torrentHandle.piece_priority(i, 6)
            thread.start_new_thread(self.downloadLoop, (title,))

    def downloadLoop(self, title):
        db = DownloadDB()
        status = 'downloading'
        while db.get(title) and status != 'stopped':
            xbmc.sleep(3000)
            status = db.get_status(title)
            if not self.paused:
                if status == 'pause':
                    self.paused = True
                    self.session.pause()
            else:
                if status != 'pause':
                    self.paused = False
                    self.session.resume()
            s = self.torrentHandle.status()
            info = {}
            info['upload'] = s.upload_payload_rate
            info['download'] = s.download_payload_rate
            info['peers'] = s.num_peers
            info['seeds'] = s.num_seeds
            iterator = int(s.progress * 100)
            info['progress'] = iterator
            db.update(title, info)
            self.debug()
        self.session.remove_torrent(self.torrentHandle)
        return

    def initSession(self):
        try:
            self.session.remove_torrent(self.torrentHandle)
        except:
            pass
        self.session = self.lt.session()
        self.session.set_alert_mask(self.lt.alert.category_t.error_notification | self.lt.alert.category_t.status_notification | self.lt.alert.category_t.storage_notification)
        self.session.start_dht()
        self.session.add_dht_router("router.bittorrent.com", 6881)
        self.session.add_dht_router("router.utorrent.com", 6881)
        self.session.add_dht_router("router.bitcomet.com", 6881)
        self.session.start_lsd()
        self.session.start_upnp()
        self.session.start_natpmp()
        self.session.listen_on(6881, 6891)

        #tribler example never tested
        #self.session.set_severity_level(self.lt.alert.severity_levels.info)
        #self.session.add_extension("ut_pex")
        #self.session.add_extension("lt_trackers")
        #self.session.add_extension("metadata_transfer")
        #self.session.add_extension("ut_metadata")
        # Ban peers that sends bad data
        #self.session.add_extension("smart_ban")

        # Session settings
        #session_settings = self.session.settings()
        #
        #session_settings.announce_to_all_tiers = True
        #session_settings.announce_to_all_trackers = True
        #session_settings.connection_speed = 100
        #session_settings.peer_connect_timeout = 2
        #session_settings.rate_limit_ip_overhead = True
        #session_settings.request_timeout = 5
        #session_settings.torrent_connect_boost = 100
        #
        #self.session.set_settings(session_settings)

    def encryptSession(self):
        # Encryption settings
        print '[Torrenter v2]: Encryption enabling...'
        try:
            encryption_settings = self.lt.pe_settings()
            encryption_settings.out_enc_policy = self.lt.enc_policy(self.lt.enc_policy.forced)
            encryption_settings.in_enc_policy = self.lt.enc_policy(self.lt.enc_policy.forced)
            encryption_settings.allowed_enc_level = self.lt.enc_level.both
            encryption_settings.prefer_rc4 = True
            self.session.set_pe_settings(encryption_settings)
            print '[Torrenter v2]: Encryption on!'
        except Exception, e:
            print '[Torrenter v2]: Encryption failed! Exception: ' + str(e)
            pass

    def startSession(self):
        if None == self.magnetLink:
            self.torrentHandle = self.session.add_torrent({'ti': self.torrentFileInfo,
                                                           'save_path': self.storageDirectory,
                                                           #'flags': 0x300,
                                                           'paused': False,
                                                           'auto_managed': False,
                                                           'storage_mode': self.lt.storage_mode_t.storage_mode_allocate,
                                                           })
        else:
            self.torrentFileInfo = self.getMagnetInfo()
        self.torrentHandle.set_sequential_download(True)
        self.torrentHandle.set_max_connections(60)
        self.torrentHandle.set_max_uploads(-1)
        self.stopSession()

    def stopSession(self):
        for i in range(self.torrentFileInfo.num_pieces()):
            self.torrentHandle.piece_priority(i, 0)

    def continueSession(self, contentId=0, Offset=0, seeding=False, isMP4=False):
        self.piece_length = self.torrentFileInfo.piece_length()
        selectedFileInfo = self.getContentList()[contentId]
        if not Offset:
            Offset = selectedFileInfo['size'] / (1024 * 1024)
        self.partOffset = (Offset * 1024 * 1024 / self.piece_length) + 1
        # print 'partOffset ' + str(self.partOffset)+str(' ')
        self.startPart = selectedFileInfo['offset'] / self.piece_length
        self.endPart = int((selectedFileInfo['offset'] + selectedFileInfo['size']) / self.piece_length)
        # print 'part ' + str(self.startPart)+ str(' ')+ str(self.endPart)
        multiplier = self.partOffset / 5
        log('continueSession: multiplier ' + str(multiplier))
        for i in range(self.startPart, self.startPart + self.partOffset):
            if i <= self.endPart:
                self.torrentHandle.piece_priority(i, 7)
                if isMP4 and i % multiplier == 0:
                    self.torrentHandle.piece_priority(self.endPart - i / multiplier, 7)
                    # print str(i)
                if multiplier >= i:
                    self.torrentHandle.piece_priority(self.endPart - i, 7)
                    # print str(i)

    def fetchParts(self):
        priorities = self.torrentHandle.piece_priorities()
        status = self.torrentHandle.status()
        if len(status.pieces) == 0:
            return
        if priorities[self.startPart] == 0:
            self.torrentHandle.piece_priority(self.startPart, 2)
        for part in range(self.startPart, self.endPart + 1):
            if priorities[part] == 0:
                self.torrentHandle.piece_priority(part, 1)

    def checkThread(self):
        if self.threadComplete == True:
            log('checkThread KIIIIIIIIIIILLLLLLLLLLLLLLL')
            try:
                self.session.remove_torrent(self.torrentHandle)
            except:
                log('RuntimeError: invalid torrent handle used')
            self.session.stop_natpmp()
            self.session.stop_upnp()
            self.session.stop_lsd()
            self.session.stop_dht()

    def debug(self):
        try:
            # print str(self.getFilePath(0))
            s = self.torrentHandle.status()
            # get_settings=self.torrentHandle.status
            # print s.num_pieces
            # priorities = self.torrentHandle.piece_priorities()
            # self.dump(priorities)
            # print str('anonymous_mode '+str(get_settings['anonymous_mode']))

            state_str = ['queued', 'checking', 'downloading metadata',
                         'downloading', 'finished', 'seeding', 'allocating']
            log('[%s] %.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
                  (self.lt.version, s.progress * 100, s.download_rate / 1000,
                   s.upload_rate / 1000,
                   s.num_peers, state_str[s.state]))
            debug('TRACKERS:' +str(self.torrentHandle.trackers()))
            #i = 0
            # for t in s.pieces:
            #    if t: i=i+1
            # print str(self.session.pop_alert())
            # print str(s.pieces[self.startPart:self.endPart])
            # print 'True pieces: %d' % i
            # print s.current_tracker
            # print str(s.pieces)
        except:
            print 'debug error'
            pass

    def dump(self, obj):
        for attr in dir(obj):
            try:
                print "'%s':'%s'," % (attr, getattr(obj, attr))
            except:
                pass
