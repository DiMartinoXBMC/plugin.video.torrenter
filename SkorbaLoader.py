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

import thread
import os
import urllib2
import hashlib
import re
from StringIO import StringIO
import zlib
import sys

import xbmc
import xbmcgui
import xbmcvfs
import Localization
from functions import isSubtitle, DownloadDB, log, debug, is_writable,\
    vista_check, windows_check, localize_path, decode_str

class SkorbaLoader:
    magnetLink = None
    startPart = 0
    endPart = 0
    partOffset = 0
    torrentHandle = None
    session = None
    downloadThread = None
    threadComplete = False
    lt = None
    save_resume_data = None
    __settings__ = sys.modules["__main__"].__settings__
    enable_dht = __settings__.getSetting("enable_dht") == 'true'

    def __init__(self, storageDirectory='', torrentFile='', torrentFilesDirectory='torrents'):
        self.storageDirectory = storageDirectory
        self.torrentFilesPath = os.path.join(self.storageDirectory, torrentFilesDirectory) + os.sep
        if not is_writable(self.storageDirectory):
            xbmcgui.Dialog().ok(Localization.localize('Torrenter v2'),
                    Localization.localize('Your storage path is not writable or not local! Please change it in settings!'),
                    self.storageDirectory)

            sys.exit(1)

        try:
            from python_libtorrent import get_libtorrent
            libtorrent=get_libtorrent()
            log('Imported libtorrent v%s from python_libtorrent' %(libtorrent.version))
            module=True
        except Exception, e:
            module=False
            log('Error importing python_libtorrent Exception: %s' %( str(e)))
            import libtorrent

        try:
            if not module: log('Imported libtorrent v' + libtorrent.version + ' from system')
            self.lt = libtorrent
            del libtorrent

        except Exception, e:
            log('Error importing from system. Exception: ' + str(e))
            return

        if xbmcvfs.exists(torrentFile):
            self.torrentFile = torrentFile
            e=self.lt.bdecode(xbmcvfs.File(self.torrentFile,'rb').read())
            self.torrentFileInfo = self.lt.torrent_info(e)
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
            torrentFile = localize_path(os.path.join(self.torrentFilesPath, self.md5(torrentUrl) + '.torrent'))
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
                log('Unable to save torrent file from "' + torrentUrl + '" to "' + torrentFile + '" in Torrent::saveTorrent' + '. Exception: ' + str(e))
                return
            if xbmcvfs.exists(torrentFile):
                try:
                    e=self.lt.bdecode(xbmcvfs.File(torrentFile,'rb').read())
                    self.torrentFileInfo = self.lt.torrent_info(e)
                except Exception, e:
                    log('Exception: ' + str(e))
                    xbmcvfs.delete(torrentFile)
                    return
                if not xbmcvfs.exists(self.torrentFilesPath):
                    xbmcvfs.mkdirs(self.torrentFilesPath)
                newFile = localize_path(self.torrentFilesPath + self.md5(torrentUrl) + '.torrent')
                if newFile != torrentFile:
                    if xbmcvfs.exists(newFile):
                        xbmcvfs.delete(newFile)
                    if not xbmcvfs.exists(newFile):
                        try:
                            xbmcvfs.rename(torrentFile, newFile)
                        except Exception, e:
                            log('Unable to rename torrent file from %s to %s in Torrent::renameTorrent. Exception: %s' %
                                (torrentFile, newFile, str(e)))
                            return
                self.torrentFile = newFile
                if not self.torrentFileInfo:
                    e=self.lt.bdecode(xbmcvfs.File(self.torrentFile,'rb').read())
                    self.torrentFileInfo = self.lt.torrent_info(e)
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

    def getMagnetInfo(self):
        magnetSettings = {
            'url': self.magnetLink,
            'save_path': self.storageDirectory,
            'storage_mode': self.lt.storage_mode_t(0),
            'paused': True,
            #'auto_managed': True,
            'duplicate_is_error': False
        }
        progressBar = xbmcgui.DialogProgress()
        progressBar.create(Localization.localize('Please Wait'), Localization.localize('Magnet-link is converting'))
        self.torrentHandle = self.session.add_torrent(magnetSettings)
        iterator = 0
        if self.enable_dht: self.torrentHandle.force_dht_announce()
        while iterator < 100:
            xbmc.sleep(500)
            progressBar.update(iterator, Localization.localize('Please Wait'), Localization.localize('Magnet-link is converting')+'.' * (iterator % 4), ' ')
            iterator += 1
            if progressBar.iscanceled():
                progressBar.update(0)
                progressBar.close()
                return
            if self.torrentHandle.status().has_metadata:
                iterator = 100
        progressBar.update(0)
        progressBar.close()
        if self.torrentHandle.status().has_metadata:
            try:
                info = self.torrentHandle.torrent_file()
            except:
                info = self.torrentHandle.get_torrent_info()
            return info

    def magnetToTorrent(self, magnet):
        self.magnetLink = magnet
        self.initSession()
        torrentInfo = self.getMagnetInfo()
        if torrentInfo:
            try:
                torrentFile = self.lt.create_torrent(torrentInfo)
                if not xbmcvfs.exists(self.torrentFilesPath):
                    xbmcvfs.mkdirs(self.torrentFilesPath)
                self.torrentFile = self.torrentFilesPath + self.md5(magnet) + '.torrent'
                torentFileHandler = xbmcvfs.File(self.torrentFile, "w+b")
                torentFileHandler.write(self.lt.bencode(torrentFile.generate()))
                torentFileHandler.close()
                e=self.lt.bdecode(xbmcvfs.File(self.torrentFile,'rb').read())
                self.torrentFileInfo = self.lt.torrent_info(e)
            except:
                xbmc.executebuiltin("Notification(%s, %s, 7500)" % (Localization.localize('Error'), Localization.localize(
                    'Can\'t download torrent, probably no seeds available.')))
                self.torrentFileInfo = torrentInfo
            finally:
                self.session.remove_torrent(self.torrentHandle)
                self.torrentHandle = None

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
        return os.path.join(self.storageDirectory, decode_str(self.getContentList()[contentId]['title']))

    def getContentList(self):
        filelist = []
        #from functions import decode_str
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
        try:
            session_settings = self.session.get_settings()
            session_settings['upload_rate_limit'] = int(bytesPerSecond)
            self.session.set_settings(session_settings)
        except:
            #0.16 compatibility
            self.session.set_upload_rate_limit(int(bytesPerSecond))

    def setDownloadLimit(self, bytesPerSecond):
        try:
            session_settings = self.session.get_settings()
            session_settings['download_rate_limit'] = int(bytesPerSecond)
            self.session.set_settings(session_settings)
        except:
            #0.16 compatibility
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
            del db
            thread.start_new_thread(self.downloadLoop, (title,))

    def downloadLoop(self, title):
        db = DownloadDB()
        status = 'downloading'
        while db.get(title) and status != 'stopped':
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
            #self.debug()
            xbmc.sleep(3000)
        log('out of downloadLoop')
        self.session.remove_torrent(self.torrentHandle)
        return

    def initSession(self):
        self.session = self.lt.session()
        self.session.set_alert_mask(self.lt.alert.category_t.error_notification | self.lt.alert.category_t.status_notification | self.lt.alert.category_t.storage_notification)
        #self.session.set_alert_mask(self.lt.alert.category_t.all_categories)
        if self.enable_dht:
            self.session.add_dht_router("router.bittorrent.com", 6881)
            self.session.add_dht_router("router.utorrent.com", 6881)
            self.session.start_dht()
        self.session.start_lsd()
        self.session.start_upnp()
        self.session.start_natpmp()
        try:
            port = int(self.__settings__.getSetting('listen_port'))
            self.session.listen_on(port, port+10)
        except:
            try:
                log('listen_on(%d, %d) error' %(port, port+10))
            except:
                log('listen_port %s error' %(self.__settings__.getSetting('listen_port')))

        pc_config = int(self.__settings__.getSetting('pc_config'))

        # Session settings
        try:
            session_settings = self.session.get_settings()
            #
            session_settings['announce_to_all_tiers'] = True
            session_settings['announce_to_all_trackers'] = True
            session_settings['peer_connect_timeout'] = 2
            session_settings['rate_limit_ip_overhead'] = True
            session_settings['request_timeout'] = 1
            session_settings['torrent_connect_boost'] = 50
            session_settings['user_agent'] = ''
            if pc_config == 0:
                #good pc
                session_settings['connections_limit'] = 200
                session_settings['unchoke_slots_limit'] = 10
                session_settings['connection_speed'] = 200
                session_settings['file_pool_size'] = 40
            elif pc_config == 1:
                #bad pc/router
                session_settings['connections_limit'] = 100
                session_settings['half_open_limit'] = (lambda: windows_check() and
                                  (lambda: vista_check() and 4 or 8)() or 50)()
                session_settings['unchoke_slots_limit'] = 4
                session_settings['connection_speed'] = 100
                session_settings['file_pool_size'] = 40

            #session_settings['cache_size'] = 0
            #session_settings['use_read_cache'] = False

        except:
            #0.15 compatibility
            log('[initSession]: Session settings 0.15 compatibility')
            session_settings = self.session.settings()

            session_settings.announce_to_all_tiers = True
            session_settings.announce_to_all_trackers = True
            session_settings.connection_speed = 100
            session_settings.peer_connect_timeout = 2
            session_settings.rate_limit_ip_overhead = True
            session_settings.request_timeout = 1
            session_settings.torrent_connect_boost = 100
            session_settings.user_agent = ''
        #
        self.session.set_settings(session_settings)

    def encryptSession(self):
        # Encryption settings
        log('Encryption enabling...')
        try:
            encryption_settings = self.lt.pe_settings()
            encryption_settings.out_enc_policy = self.lt.enc_policy(self.lt.enc_policy.forced)
            encryption_settings.in_enc_policy = self.lt.enc_policy(self.lt.enc_policy.forced)
            encryption_settings.allowed_enc_level = self.lt.enc_level.both
            encryption_settings.prefer_rc4 = True
            self.session.set_pe_settings(encryption_settings)
            log('Encryption on!')
        except Exception, e:
            log('Encryption failed! Exception: ' + str(e))
            pass

    def startSession(self):
        if self.magnetLink:
            self.torrentFileInfo = self.getMagnetInfo()
        torrent_info={'ti': self.torrentFileInfo,
                      'save_path': self.storageDirectory,
                      'flags': 0x300,
                       #'storage_mode': self.lt.storage_mode_t(1),
                       'paused': False,
                       #'auto_managed': False,
                       'duplicate_is_error': True
                      }
        if self.save_resume_data:
            log('loading resume data')
            torrent_info['resume_data']=self.save_resume_data
        else:
            resume_file=self.resume_data_path()
            if xbmcvfs.exists(resume_file):
                log('loading resume data from file '+resume_file)
                try:
                    resumDataFile=xbmcvfs.File(resume_file,'rb')
                    self.save_resume_data=resumDataFile.read()
                    resumDataFile.close()
                    torrent_info['resume_data']=self.save_resume_data
    
                except:
                    log('Failed to load resume data from file '+ resume_file)
        self.torrentHandle = self.session.add_torrent(torrent_info)
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
        self.startPart = selectedFileInfo['offset'] / self.piece_length
        self.endPart = int((selectedFileInfo['offset'] + selectedFileInfo['size']) / self.piece_length)
        multiplier = self.partOffset / 5
        log('continueSession: multiplier ' + str(multiplier))
        for i in range(self.startPart, self.startPart + self.partOffset):
            if i <= self.endPart:
                self.torrentHandle.piece_priority(i, 7)
                if isMP4 and i % multiplier == 0:
                    self.torrentHandle.piece_priority(self.endPart - i / multiplier, 7)
                if multiplier >= i:
                    self.torrentHandle.piece_priority(self.endPart - i, 7)

    def checkThread(self):
        if self.threadComplete == True:
            self.resume_data()
            log('checkThread KIIIIIIIIIIILLLLLLLLLLLLLLL')
            try:
                self.session.remove_torrent(self.torrentHandle)
            except:
                log('RuntimeError: invalid torrent handle used')
            self.session.stop_natpmp()
            self.session.stop_upnp()
            self.session.stop_lsd()
            if self.enable_dht: self.session.stop_dht()

    def resume_data(self):
        wasPaused=self.session.is_paused()
        self.session.pause()
        self.save_resume_data=None

        try:
            if not self.torrentHandle.is_valid():
                return
            status = self.torrentHandle.status()
            if not status.has_metadata:
                return
            if not status.need_save_resume:
                return
    
            log('[save_resume_data]: waiting for alert...')
            self.torrentHandle.save_resume_data(self.lt.save_resume_flags_t.flush_disk_cache)
            received=False
            while not received:   
                self.session.wait_for_alert(1000)
                a = self.session.pop_alert()
                log('[save_resume_data]: ['+str(type(a))+'] the alert '+str(a)+' is received')
                if type(a) == self.lt.save_resume_data_alert:
                    received = True
                    debug('[save_resume_data]: '+str(dir(a)))
                    self.save_resume_data=self.lt.bencode(a.resume_data)
                    log('[save_resume_data]: the torrent resume data are received')
                    try:
                        resumeFileHandler = xbmcvfs.File(self.resume_data_path(), "w+b")
                        resumeFileHandler.write(self.save_resume_data)
                        resumeFileHandler.close()
                        log('[save_resume_data]: the torrent resume data to file' + self.resume_data_path()) 
                    except:
                       log('[save_resume_data]: failed to save the torrent resume data to file') 
                elif type(a) == self.lt.save_resume_data_failed_alert:
                    received = True
                    log('[save_resume_data]: save_resume_data() failed')
            log('[save_resume_data]: done.')
    
        finally:
            if not wasPaused:
                self.session.resume()

    def debug(self):
        #try:
        if 1==1:
            # log(str(self.getFilePath(0)))
            s = self.torrentHandle.status()
            #get_cache_status=self.session.get_cache_status()
            #log('get_cache_status - %s/%s' % (str(get_cache_status.blocks_written), str(get_cache_status.blocks_read)))
            # get_settings=self.torrentHandle.status
            # log(s.num_pieces)
            #priorities = self.torrentHandle.piece_priorities()
            #log(str(priorities))

            state_str = ['queued', 'checking', 'downloading metadata',
                         'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
            log('[%s] %.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' % \
                  (self.lt.version, s.progress * 100, s.download_rate / 1000,
                   s.upload_rate / 1000, s.num_peers, state_str[s.state]))
            #log('%s %s' % (self.get_debug_info('dht_state'), self.get_debug_info('trackers_sum')))
            #debug('TRACKERS:' +str(self.torrentHandle.trackers()))

            #received=self.session.pop_alert()
            #while received:
            #    debug('[debug]: ['+str(type(received))+'] the alert '+str(received)+' is received')
            #    #if type(received) == self.lt.torrent_finished_alert:
            #    #    self.session.pause()
            #    received = self.session.pop_alert()

            #log('is_dht_running:' +str(self.session.is_dht_running()))
            #log('dht_state:' +str(self.session.dht_state()))
            #i = 0
            # for t in s.pieces:
            #    if t: i=i+1
            #log(str(self.session.pop_alert())
            # log(str(s.pieces[self.startPart:self.endPart]))
            # log('True pieces: %d' % i)
            # log(s.current_tracker)
            # log(str(s.pieces))
        #except:
        else:
            log('debug error')
            pass

    def get_debug_info(self, info):
        result=''
        if info in ['trackers_full','trackers_sum']:
            trackers=[]
            for tracker in self.torrentHandle.trackers():
                trackers.append((tracker['url'], tracker['fails'], tracker['verified']))
            if info=='trackers_full':
                for url, fails, verified in trackers:
                    result=result+'%s: f=%d, v=%s' %(url, fails, str(verified))
            if info=='trackers_sum':
                fails_sum, verified_sum = 0, 0
                for url, fails, verified in trackers:
                    fails_sum+=fails
                    if verified: verified_sum+=1
                result=result+'Trackers: verified %d/%d, fails=%d' %(verified_sum, len(trackers)-1, fails_sum)
        if info=='dht_state':
            is_dht_running='ON' if self.session.is_dht_running() else 'OFF'
            try:
                nodes=self.session.dht_state().get('nodes')
            except:
                nodes=None
            nodes=len(nodes) if nodes else 0
            result='DHT: %s (%d)' % (is_dht_running, nodes)
        return result

    def dump(self, obj):
        for attr in dir(obj):
            try:
                log("'%s':'%s'," % (attr, getattr(obj, attr)))
            except:
                pass

    def resume_data_path(self):
        path=self.torrentFile + ".resume_data"
        return path
