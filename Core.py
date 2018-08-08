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
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the#
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import Downloader
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs
from functions import *

class Core:
    __plugin__ = sys.modules["__main__"].__plugin__
    __settings__ = sys.modules["__main__"].__settings__
    ROOT = sys.modules["__main__"].__root__
    userStorageDirectory = localize_path(xbmc.translatePath(__settings__.getSetting("storage")))#file_encode(__settings__.getSetting("storage"))
    torrentFilesDirectory = 'torrents'
    debug = __settings__.getSetting('debug') == 'true'
    torrent_player = __settings__.getSetting("torrent_player")
    history_bool = __settings__.getSetting('history') == 'true'
    open_option = int(__settings__.getSetting('open_option'))
    language = {0: 'en', 1: 'ru', 2: 'uk', 3: 'he', 4: 'hu'}.get(int(__settings__.getSetting("language")))
    scrapperDB_ver = {'en':'1.1', 'ru':'1.3', 'he':'1.3'}
    torrent_info_style = int(__settings__.getSetting('torrent_info_style'))
    searchwindowmode = int(__settings__.getSetting('searchwindowmode'))

    log('SYS ARGV: ' + str(sys.argv))

    def __init__(self):
        #print '!!!!!!!!!!!!!!!!!! BORN '+self.__class__.__name__
        if len(self.userStorageDirectory) == 0:
            download_dir = get_download_dir()
        else:
            download_dir = self.userStorageDirectory
        self.userStorageDirectory = os.path.join(download_dir, 'Torrenter')

    def sectionMenu(self):
        if self.__settings__.getSetting('plugin_name') != self.__plugin__:
            #Every update run
            first_run_260()
            if self.version_check():
                estuary()

            self.__settings__.setSetting('first_run_260', 'True')
            self.__settings__.setSetting('plugin_name', self.__plugin__)
            #check_network_advancedsettings()
            check_download_dir()
            #if self.__plugin__ == 'Torrenter v.2.4.1b':
            #    first_run_242()
            #    pass

        ListString = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?action=%s&action2=%s&%s=%s')
        contextMenu = [(self.localize('Search Control Window'),
                'xbmc.RunScript(%s,)' % os.path.join(ROOT, 'controlcenter.py'))]

        #Search Window
        if self.searchwindowmode < 3:
            self.drawItem('< %s >' % self.localize('Search Window'), 'searchWindow',
                          image=self.ROOT + '/icons/kodi.png', isFolder=False)

        #History
        if self.history_bool and self.searchwindowmode > 0:
            HistorycontextMenu = []
            HistorycontextMenu.extend(contextMenu)
            HistorycontextMenu.append(
                (self.localize('Clear %s') % self.localize('Search History'),
                 ListString % ('History', 'clear', 'addtime', '')))
            if self.searchwindowmode == 1:
                self.drawItem('< %s >' % self.localize('Search History'), 'swHistory',
                              image=self.ROOT + '/icons/history2.png', contextMenu=HistorycontextMenu, replaceMenu=False)
            else:
                self.drawItem('< %s >' % self.localize('Search History'), 'History',
                              image=self.ROOT + '/icons/history2.png', contextMenu=HistorycontextMenu, replaceMenu=False)

        #Search
        if self.searchwindowmode == 1:
            self.drawItem('< %s >' % self.localize('Search'), 'swsearch', image=self.ROOT + '/icons/search.png',)
        elif self.searchwindowmode > 1:
            self.drawItem('< %s >' % self.localize('Search'), 'search', image=self.ROOT + '/icons/search.png', )

        #Media
        CLcontextMenu=[]
        CLcontextMenu.extend(contextMenu)
        CLcontextMenu.append((self.localize('Reset All Cache DBs'),
                            ListString % ('full_download', '', 'url', json.dumps({'action': 'delete'}))))
        self.drawItem('< %s >' % self.localize('Content Lists'), 'openContent', image=self.ROOT + '/icons/media.png',
                      contextMenu=CLcontextMenu, replaceMenu=False)

        #DL Status
        DLScontextMenu=[(self.localize('Start All'), ListString % ('DownloadStatus', 'startall', 'addtime', '')),
                        (self.localize('Stop All'), ListString % ('DownloadStatus', 'stopall', 'addtime', '')),]
        DLScontextMenu.append(
                (self.localize('Clear %s') % self.localize('Download Status'), ListString % ('DownloadStatus', 'clear', 'addtime', '')))
        DLScontextMenu.extend(contextMenu)

        if self.searchwindowmode == 1:
            self.drawItem('< %s >' % self.localize('Download Status'), 'swDownloadStatus',
                          image=self.ROOT + '/icons/download.png',
                          contextMenu=DLScontextMenu, replaceMenu=False)
        elif self.searchwindowmode > 1:
            self.drawItem('< %s >' % self.localize('Download Status'), 'DownloadStatus',
                          image=self.ROOT + '/icons/download.png',
                          contextMenu=DLScontextMenu, replaceMenu=False)

        #Torrent-client
        if self.searchwindowmode == 1:
            self.drawItem('< %s >' % self.localize('Torrent-client Browser'), 'swuTorrentBrowser',
                          image=self.ROOT + '/icons/' + getTorrentClientIcon())
        elif self.searchwindowmode > 1:
            self.drawItem('< %s >' % self.localize('Torrent-client Browser'), 'uTorrentBrowser',
                          image=self.ROOT + '/icons/' + getTorrentClientIcon())

        #Watched
        if self.history_bool and self.searchwindowmode > 0:
            WatchedHistorycontextMenu=[]
            WatchedHistorycontextMenu.extend(contextMenu)
            WatchedHistorycontextMenu.append(
                (self.localize('Clear %s') % self.localize('Watched History'), ListString % ('WatchedHistory', 'clear', 'addtime', '')))
            if self.searchwindowmode == 1:
                self.drawItem('< %s >' % self.localize('Watched History'), 'swWatchedHistory',
                              image=self.ROOT + '/icons/watched.png', contextMenu=WatchedHistorycontextMenu,
                              replaceMenu=False)
            else:
                self.drawItem('< %s >' % self.localize('Watched History'), 'WatchedHistory',
                      image=self.ROOT + '/icons/watched.png', contextMenu=WatchedHistorycontextMenu,
                              replaceMenu=False)

        #Torr player
        self.drawItem('< %s >' % self.localize('.torrent Player'), 'torrentPlayer',
                      image=self.ROOT + '/icons/torrentPlayer.png', isFolder = False)

        #Search Control Window
        self.drawItem('< %s >' % self.localize('Search Control Window'), 'controlCenter',
                      image=self.ROOT + '/icons/settings.png', isFolder=False)

        #Magnet player
        self.drawItem('< %s >' % self.localize('Magnet-link Player'), 'magentPlayer',
                      image=self.ROOT + '/icons/magnet.png', isFolder = False)

        #Debug
        if self.debug:
            self.drawItem('full_download', 'full_download', image=self.ROOT + '/icons/magnet.png')
            self.drawItem('test', 'test', image=self.ROOT + '/icons/magnet.png', isFolder=False)

        #Clear storage
        if '0' != self.__settings__.getSetting("keep_files"):
            self.drawItem('< %s >' % self.localize('Clear Storage'), 'clearStorage', isFolder=True,
                          image=self.ROOT + '/icons/clear.png')

        view_style('sectionMenu')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def test_scrapper(self):
        ok = xbmcgui.Dialog().yesno(self.localize('Content Lists'),
                                    self.localize('Reset All Cache DBs'), )
        if ok:
            dirname = xbmc.translatePath('special://temp')
            dirname = os.path.join(dirname, 'xbmcup', 'plugin.video.torrenter')
            scrapers = {'tvdb': 'TheTVDB.com', 'tmdb': 'TheMovieDB.org', 'kinopoisk': 'KinoPoisk.ru'}
            for i in scrapers.keys():
                xbmcvfs.delete(os.path.join(dirname, i +'.'+ self.language + '.db'))
                xbmcvfs.copy(os.path.join(dirname, i+'.'+ self.language + ' - копия.db'), os.path.join(dirname, i+'.'+ self.language + '.db'))

        test = [(15, u'Mujaki no Rakue', u'\u041d\u0435\u0432\u0438\u043d\u043d\u044b\u0439 \u0440\u0430\u0439', 2014,
                 u'http://media9.fast-torrent.ru/media/files/s4/lz/jx/cache/nevinnyij-raj_video_list.jpg',
                 {'year': 2014, 'title': u'\u041d\u0435\u0432\u0438\u043d\u043d\u044b\u0439 \u0440\u0430\u0439',
                  'link': u'/film/nevinnyij-raj.html',
                  'label': u'\u041d\u0435\u0432\u0438\u043d\u043d\u044b\u0439 \u0440\u0430\u0439'}), (
                14, u'Appleseed Alpha', u'\u041f\u0440\u043e\u0435\u043a\u0442 \u0410\u043b\u044c\u0444\u0430', 2014,
                u'http://media9.fast-torrent.ru/media/files/s2/qr/wm/cache/proekt-alfa_video_list.jpg',
                {'year': 2014, 'title': u'\u041f\u0440\u043e\u0435\u043a\u0442 \u0410\u043b\u044c\u0444\u0430',
                 'link': u'/film/proekt-alfa.html',
                 'label': u'\u041f\u0440\u043e\u0435\u043a\u0442 \u0410\u043b\u044c\u0444\u0430'}), (
                13, u'Omoide no Marnie',
                u'\u0412\u0441\u043f\u043e\u043c\u0438\u043d\u0430\u044f \u041c\u0430\u0440\u043d\u0438', 2014,
                u'http://media9.fast-torrent.ru/media/files/s1/qs/oy/cache/vspominaya-marni_video_list.jpg',
                {'year': 2014,
                 'title': u'\u0412\u0441\u043f\u043e\u043c\u0438\u043d\u0430\u044f \u041c\u0430\u0440\u043d\u0438',
                 'link': u'/film/vspominaya-marni.html',
                 'label': u'\u0412\u0441\u043f\u043e\u043c\u0438\u043d\u0430\u044f \u041c\u0430\u0440\u043d\u0438'}), (
                12, u'Sakasama no Patema: Beginning of the Day',
                u'\u041f\u0430\u0442\u044d\u043c\u0430 \u043d\u0430\u043e\u0431\u043e\u0440\u043e\u0442', 2014,
                u'http://media9.fast-torrent.ru/media/files/s4/bh/ii/cache/perevyornutaya-patema-nachalo-_video_list.jpg',
                {'year': 2014,
                 'title': u'\u041f\u0430\u0442\u044d\u043c\u0430 \u043d\u0430\u043e\u0431\u043e\u0440\u043e\u0442',
                 'link': u'/film/perevyornutaya-patema-nachalo-dnya.html',
                 'label': u'\u041f\u0430\u0442\u044d\u043c\u0430 \u043d\u0430\u043e\u0431\u043e\u0440\u043e\u0442'}), (
                11, u'Tsubasa to Hotaru',
                u'\u0426\u0443\u0431\u0430\u0441\u0430 \u0438 \u0441\u0432\u0435\u0442\u043b\u044f\u0447\u043a\u0438',
                2014, u'http://media9.fast-torrent.ru/media/files/s1/ou/tj/cache/tsubasa-i-svetlyachki_video_list.jpg',
                {'year': 2014,
                 'title': u'\u0426\u0443\u0431\u0430\u0441\u0430 \u0438 \u0441\u0432\u0435\u0442\u043b\u044f\u0447\u043a\u0438',
                 'link': u'/film/tsubasa-i-svetlyachki.html',
                 'label': u'\u0426\u0443\u0431\u0430\u0441\u0430 \u0438 \u0441\u0432\u0435\u0442\u043b\u044f\u0447\u043a\u0438'}),
                (10, u'Harmonie', u'\u0413\u0430\u0440\u043c\u043e\u043d\u0438\u044f', 2014,
                 u'http://media9.fast-torrent.ru/media/files/s4/os/it/cache/garmonija_video_list.jpg',
                 {'year': 2014, 'title': u'\u0413\u0430\u0440\u043c\u043e\u043d\u0438\u044f',
                  'link': u'/film/garmonija.html', 'label': u'\u0413\u0430\u0440\u043c\u043e\u043d\u0438\u044f'}), (
                9, u'Z-Kai: Cross Road', u'\u041f\u0435\u0440\u0435\u043f\u0443\u0442\u044c\u0435', 2014,
                u'http://media9.fast-torrent.ru/media/files/s4/rr/mc/cache/perepute_video_list.png',
                {'year': 2014, 'title': u'\u041f\u0435\u0440\u0435\u043f\u0443\u0442\u044c\u0435',
                 'link': u'/film/perepute.html', 'label': u'\u041f\u0435\u0440\u0435\u043f\u0443\u0442\u044c\u0435'}), (
                8, u'Giovanni no Shima',
                u'\u041e\u0441\u0442\u0440\u043e\u0432 \u0414\u0436\u043e\u0432\u0430\u043d\u043d\u0438', 2014,
                u'http://media9.fast-torrent.ru/media/files/s3/gi/rq/cache/ostrov-dzhovanni_video_list.jpg',
                {'year': 2014,
                 'title': u'\u041e\u0441\u0442\u0440\u043e\u0432 \u0414\u0436\u043e\u0432\u0430\u043d\u043d\u0438',
                 'link': u'/film/ostrov-dzhovanni.html',
                 'label': u'\u041e\u0441\u0442\u0440\u043e\u0432 \u0414\u0436\u043e\u0432\u0430\u043d\u043d\u0438'}), (
                7, u'Kaze tachinu', u'\u0412\u0435\u0442\u0435\u0440 \u043a\u0440\u0435\u043f\u0447\u0430\u0435\u0442',
                2014, u'http://media9.fast-torrent.ru/media/files/s2/ol/br/cache/veter-krepchaet-1_video_list.jpg',
                {'year': 2014,
                 'title': u'\u0412\u0435\u0442\u0435\u0440 \u043a\u0440\u0435\u043f\u0447\u0430\u0435\u0442',
                 'link': u'/film/veter-krepchaet-1.html',
                 'label': u'\u0412\u0435\u0442\u0435\u0440 \u043a\u0440\u0435\u043f\u0447\u0430\u0435\u0442'}), (
                6, u'Majokko Shimai no Yoyo to Nene',
                u'\u0421\u0435\u0441\u0442\u0440\u044b-\u043a\u043e\u043b\u0434\u0443\u043d\u044c\u0438 \u0419\u043e-\u0439\u043e \u0438 \u041d\u044d\u043d\u044d',
                2013,
                u'http://media9.fast-torrent.ru/media/files/s1/nt/rq/cache/sestryi-kolduni-jo-jo-i-nene_video_list.jpg',
                {'year': 2013,
                 'title': u'\u0421\u0435\u0441\u0442\u0440\u044b-\u043a\u043e\u043b\u0434\u0443\u043d\u044c\u0438 \u0419\u043e-\u0439\u043e \u0438 \u041d\u044d\u043d\u044d',
                 'link': u'/film/sestryi-kolduni-jo-jo-i-nene.html',
                 'label': u'\u0421\u0435\u0441\u0442\u0440\u044b-\u043a\u043e\u043b\u0434\u0443\u043d\u044c\u0438 \u0419\u043e-\u0439\u043e \u0438 \u041d\u044d\u043d\u044d'}),
                (5, u'Bayonetta: Bloody Fate',
                 u'\u0411\u0430\u0439\u043e\u043d\u0435\u0442\u0442\u0430: \u041a\u0440\u043e\u0432\u0430\u0432\u0430\u044f \u0441\u0443\u0434\u044c\u0431\u0430',
                 2013,
                 u'http://media9.fast-torrent.ru/media/files/s1/ho/ba/cache/bajonetta-krovavaya-sudba_video_list.jpg',
                 {'year': 2013,
                  'title': u'\u0411\u0430\u0439\u043e\u043d\u0435\u0442\u0442\u0430: \u041a\u0440\u043e\u0432\u0430\u0432\u0430\u044f \u0441\u0443\u0434\u044c\u0431\u0430',
                  'link': u'/film/bajonetta-krovavaya-sudba.html',
                  'label': u'\u0411\u0430\u0439\u043e\u043d\u0435\u0442\u0442\u0430: \u041a\u0440\u043e\u0432\u0430\u0432\u0430\u044f \u0441\u0443\u0434\u044c\u0431\u0430'}),
                (4, u'Lupin III: Princess of the Breeze',
                 u'\u041b\u044e\u043f\u0435\u043d III: \u041f\u0440\u0438\u043d\u0446\u0435\u0441\u0441\u0430 \u043c\u043e\u0440\u0441\u043a\u043e\u0433\u043e \u0431\u0440\u0438\u0437\u0430',
                 2013,
                 u'http://media9.fast-torrent.ru/media/files/s1/oz/ox/cache/lyupen-iii-printsessa-morskogo_video_list.jpg',
                 {'year': 2013,
                  'title': u'\u041b\u044e\u043f\u0435\u043d III: \u041f\u0440\u0438\u043d\u0446\u0435\u0441\u0441\u0430 \u043c\u043e\u0440\u0441\u043a\u043e\u0433\u043e \u0431\u0440\u0438\u0437\u0430',
                  'link': u'/film/lyupen-iii-printsessa-morskogo-briza.html',
                  'label': u'\u041b\u044e\u043f\u0435\u043d III: \u041f\u0440\u0438\u043d\u0446\u0435\u0441\u0441\u0430 \u043c\u043e\u0440\u0441\u043a\u043e\u0433\u043e \u0431\u0440\u0438\u0437\u0430'}),
                (3, u'Ansatsu Kyoushitsu',
                 u'\u0423\u0431\u0438\u0439\u0441\u0442\u0432\u043e \u0432 \u043a\u043b\u0430\u0441\u0441\u043d\u043e\u0439 \u043a\u043e\u043c\u043d\u0430\u0442\u0435',
                 2013,
                 u'http://media9.fast-torrent.ru/media/files/s4/fl/td/cache/ubijstvo-v-klassnoj-komnate_video_list.jpg',
                 {'year': 2013,
                  'title': u'\u0423\u0431\u0438\u0439\u0441\u0442\u0432\u043e \u0432 \u043a\u043b\u0430\u0441\u0441\u043d\u043e\u0439 \u043a\u043e\u043c\u043d\u0430\u0442\u0435',
                  'link': u'/film/ubijstvo-v-klassnoj-komnate.html',
                  'label': u'\u0423\u0431\u0438\u0439\u0441\u0442\u0432\u043e \u0432 \u043a\u043b\u0430\u0441\u0441\u043d\u043e\u0439 \u043a\u043e\u043c\u043d\u0430\u0442\u0435'}),
                (2, u'Kobayashi ga Kawai Sugite Tsurai!',
                 u'\u041a\u043e\u0431\u0430\u044f\u0448\u0438 \u043d\u0430\u0441\u0442\u043e\u043b\u044c\u043a\u043e \u043c\u0438\u043b\u044b, \u0447\u0442\u043e \u0430\u0436 \u0434\u0443\u0448\u0443 \u0442\u0435\u0440\u0435\u0431\u0438\u0442!!',
                 2013,
                 u'http://media9.fast-torrent.ru/media/files/s2/st/ya/cache/kobayashi-nastolko-milyi-chto-_video_list.jpg',
                 {'year': 2013,
                  'title': u'\u041a\u043e\u0431\u0430\u044f\u0448\u0438 \u043d\u0430\u0441\u0442\u043e\u043b\u044c\u043a\u043e \u043c\u0438\u043b\u044b, \u0447\u0442\u043e \u0430\u0436 \u0434\u0443\u0448\u0443 \u0442\u0435\u0440\u0435\u0431\u0438\u0442!!',
                  'link': u'/film/kobayashi-nastolko-milyi-chto-azh-dushu-terebit.html',
                  'label': u'\u041a\u043e\u0431\u0430\u044f\u0448\u0438 \u043d\u0430\u0441\u0442\u043e\u043b\u044c\u043a\u043e \u043c\u0438\u043b\u044b, \u0447\u0442\u043e \u0430\u0436 \u0434\u0443\u0448\u0443 \u0442\u0435\u0440\u0435\u0431\u0438\u0442!!'}),
                (1, u'Rescue Me!', u'\u0421\u043f\u0430\u0441\u0438 \u043c\u0435\u043d\u044f!', 2013,
                 u'http://media9.fast-torrent.ru/media/files/s4/eh/tl/cache/spasi-menya-2_video_list.jpg',
                 {'year': 2013, 'title': u'\u0421\u043f\u0430\u0441\u0438 \u043c\u0435\u043d\u044f!',
                  'link': u'/film/spasi-menya-2.html',
                  'label': u'\u0421\u043f\u0430\u0441\u0438 \u043c\u0435\u043d\u044f!'})]
        test = [(1, u'Rescue Me!', u'\u0421\u043f\u0430\u0441\u0438 \u043c\u0435\u043d\u044f!', 2013,
                 u'http://media9.fast-torrent.ru/media/files/s4/eh/tl/cache/spasi-menya-2_video_list.jpg',
                 {'year': 2013, 'title': u'\u0421\u043f\u0430\u0441\u0438 \u043c\u0435\u043d\u044f!',
                  'link': u'/film/spasi-menya-2.html',
                  'label': u'\u0421\u043f\u0430\u0441\u0438 \u043c\u0435\u043d\u044f!'}), (
                9, u'Z-Kai: Cross Road', u'\u041f\u0435\u0440\u0435\u043f\u0443\u0442\u044c\u0435', 2014,
                u'http://media9.fast-torrent.ru/media/files/s4/rr/mc/cache/perepute_video_list.png',
                {'year': 2014, 'title': u'\u041f\u0435\u0440\u0435\u043f\u0443\u0442\u044c\u0435',
                 'link': u'/film/perepute.html', 'label': u'\u041f\u0435\u0440\u0435\u043f\u0443\u0442\u044c\u0435'}), (
                8, u'Giovanni no Shima',
                u'\u041e\u0441\u0442\u0440\u043e\u0432 \u0414\u0436\u043e\u0432\u0430\u043d\u043d\u0438', 2014,
                u'http://media9.fast-torrent.ru/media/files/s3/gi/rq/cache/ostrov-dzhovanni_video_list.jpg',
                {'year': 2014,
                 'title': u'\u041e\u0441\u0442\u0440\u043e\u0432 \u0414\u0436\u043e\u0432\u0430\u043d\u043d\u0438',
                 'link': u'/film/ostrov-dzhovanni.html',
                 'label': u'\u041e\u0441\u0442\u0440\u043e\u0432 \u0414\u0436\u043e\u0432\u0430\u043d\u043d\u0438'}), ]
        self.drawcontentList(test)
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
        lockView('wide')

    def test(self, params={}):
        pass
        xbmc.Player().play('D:\\filmz\\The Missing (2014).mp4')
        from Anteoloader import OverlayText, OVERLAY_WIDTH, OVERLAY_HEIGHT, XBFONT_CENTER_X,XBFONT_CENTER_Y
        overlay = OverlayText(w=OVERLAY_WIDTH, h=OVERLAY_HEIGHT,
                    alignment=XBFONT_CENTER_X | XBFONT_CENTER_Y)
        overlay.show()
        overlay.text = 'XXXXXXXXXXXXXXXXXxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXXXXXXXXXXXXXXXXXX\r\n' \
                       'YYyyyYyYYyYyY'
        time.sleep(5)
        overlay.hide()
        time.sleep(1)
        xbmc.Player().stop()

    def swHistory(self, params={}):
        import searchwindow
        params = {'mode': 'history'}
        searchwindow.main(params)

    def swDownloadStatus(self, params={}):
        import searchwindow
        params = {'mode': 'downloadstatus'}
        searchwindow.main(params)

    def swuTorrentBrowser(self, params={}):
        import searchwindow
        params = {'mode': 'browser'}
        searchwindow.main(params)

    def swWatchedHistory(self, params={}):
        import searchwindow
        params = {'mode': 'watched'}
        searchwindow.main(params)

    def swsearch(self, params={}):
        if len(Searchers().get_active())<1:
            noActiveSerachers()
            return
        keyboard = xbmc.Keyboard('', self.localize('Search Phrase'))
        keyboard.doModal()
        params["query"] = keyboard.getText()
        if keyboard.isConfirmed():
            params["mode"] = 'search'
            import searchwindow
            searchwindow.main(params)

    def DownloadStatus(self, params={}):
        db = DownloadDB()
        get = params.get
        action2 = get('action2')
        type = get('type')
        path = get('path')
        addtime = get('addtime')

        if action2 == 'notfinished':
            showMessage(self.localize('Download Status'), self.localize('Download has not finished yet'))

        if action2 == 'play':
            if type=='file':
                xbmc.Player().play(urllib.unquote_plus(path))
            else:
                path=urllib.unquote_plus(path)
                dirs, files=xbmcvfs.listdir(path+os.sep)
                if len(dirs)>0:
                    for dir in dirs:
                        link={'action2':'play', 'type':'folder', 'path':os.path.join(path,dir)}
                        self.drawItem(dir, 'DownloadStatus', link, image='', isFolder=True)
                for file in files:
                    link={'action2':'play', 'type':'file', 'path':os.path.join(path,file)}
                    self.drawItem(file, 'DownloadStatus', link, image='', isFolder=False)
                view_style('DownloadStatus')
                xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
                return

        if action2 == 'delete':
            db.delete(addtime)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Download Status'), self.localize('Stopped and Deleted!'))

        if action2 == 'pause':
            db.update_status(addtime, 'pause')
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Download Status'), self.localize('Paused!'))

        if action2 == 'stop':
            db.update_status(addtime, 'stopped')
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Download Status'), self.localize('Stopped!'))

        if action2 == 'start':
            start=db.get_byaddtime(addtime)
            torrent, ind=start[6], start[7]
            storage=get('storage') if get('storage') else ''
            start_exec='XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s&ind=%s&storage=%s') % (
                     sys.argv[0], 'downloadLibtorrent', urllib.quote_plus(torrent.encode('utf-8')), str(ind), storage)
            xbmc.executebuiltin(start_exec)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Download Status'), self.localize('Started!'))

        if action2 == 'startall':
            items = db.get_all()
            if items:
                for addtime, title, path, type, info, status, torrent, ind, lastupdate, storage in items:
                    start_exec='XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s&ind=%s&storage=%s') % (
                    sys.argv[0], 'downloadLibtorrent', urllib.quote_plus(torrent.encode('utf-8')), str(ind), urllib.quote_plus(storage.encode('utf-8')))
                    xbmc.executebuiltin(start_exec)
                    xbmc.sleep(1000)
            showMessage(self.localize('Download Status'), self.localize('Started All!'))

        if action2 == 'stopall':
            items = db.get_all()
            if items:
                for addtime, title, path, type, info, status, torrent, ind, lastupdate, storage in items:
                    db.update_status(addtime, 'stopped')
                    xbmc.sleep(1000)
            showMessage(self.localize('Download Status'), self.localize('Stopped All!'))

        if action2 == 'unpause':
            db.update_status(addtime, 'downloading')
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Download Status'), self.localize('Unpaused!'))

        if action2 == 'clear':
            db.clear()
            showMessage(self.localize('Download Status'), self.localize('Clear!'))

        if not action2:
            items = db.get_all()
            if items:
                for addtime, title, path, type, info, status, torrent, ind, lastupdate, storage in items:
                    ListString = 'XBMC.RunPlugin('+sys.argv[0] + '?action=DownloadStatus&storage='+urllib.quote_plus(storage.encode('utf-8'))+'&addtime='+str(addtime)+'&action2='
                    jsoninfo=json.loads(urllib.unquote_plus(info))

                    if status!='stopped' and int(lastupdate)<int(time.time())-10:
                        status='stopped'
                        db.update_status(addtime, status)

                    progress=int(jsoninfo.get('progress'))
                    if status=='pause':
                        status_sign='[||]'
                        img = os.path.join(self.ROOT, 'icons', 'pause-icon.png')
                    elif status=='stopped':
                        status_sign='[X]'
                        img = os.path.join(self.ROOT, 'icons', 'stop-icon.png')
                    else:
                        status_sign='[>]'
                        if progress==100:
                            img = os.path.join(self.ROOT, 'icons', 'upload-icon.png')
                        else:
                            img = os.path.join(self.ROOT, 'icons', 'download-icon.png')

                    title = '[%d%%]%s %s'  % (progress, status_sign, title)
                    if jsoninfo.get('seeds')!=None and jsoninfo.get('peers')!=None and \
                                jsoninfo.get('download')!=None and jsoninfo.get('upload')!=None:
                            d,u=float(jsoninfo['download'])/ 1000000, float(jsoninfo['upload']) / 1000000
                            s,p=str(jsoninfo['seeds']),str(jsoninfo['peers'])
                            title='%s [D/U %.2f/%.2f (MB/s)][S/L %s/%s]' %(title,d,u,s,p)

                    if status=='pause':
                        contextMenu=[(self.localize('Unpause'), ListString+'unpause)'),
                                     (self.localize('Delete'), ListString+'delete)'),]
                    elif status=='stopped':
                        contextMenu=[(self.localize('Start'), ListString+'start)'),
                                     (self.localize('Delete'), ListString+'delete)'),]
                    else:
                        contextMenu=[(self.localize('Pause'), ListString+'pause)'),
                                     (self.localize('Stop'), ListString+'stop)'),
                                     (self.localize('Delete'), ListString+'delete)'),]

                    if progress==100 or progress>30 and type=='file':
                        link={'action2':'play', 'type':type, 'path':path.encode('utf-8')}
                        self.drawItem('[B]%s[/B]' % title, 'DownloadStatus', link, image=img, contextMenu=contextMenu, replaceMenu=False, isFolder=type=='folder')
                    else:
                        link={'action2':'notfinished'}
                        self.drawItem(title, 'DownloadStatus', link, image=img, contextMenu=contextMenu, replaceMenu=False)
            view_style('DownloadStatus')
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
            return

    def History(self, params={}):
        db = HistoryDB()
        get = params.get
        action2 = get('action2')
        url = get('url')
        addtime = get('addtime')

        if action2 == 'add':
            db.add(url)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Search History'), self.localize('Added!'))

        if action2 == 'edit':
            db.delete(addtime)
            title = get('title')
            showMessage(self.localize('Search History'), self.localize('Deleted!'))
            xbmc.executebuiltin('XBMC.ActivateWindow(Videos,%s)' % (sys.argv[0] + '?action=%s&action2=%s&%s=%s') % ('search', '&showKey=true', 'url', title))

        if action2 == 'delete':
            db.delete(addtime)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Search History'), self.localize('Deleted!'))

        if action2 == 'fav':
            db.fav(addtime)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Favourites'), self.localize('Added!'))

        if action2 == 'unfav':
            db.unfav(addtime)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Favourites'), self.localize('Deleted!'))

        if action2 == 'clear':
            db.clear()
            showMessage(self.localize('Search History'), self.localize('Clear!'))

        if not action2:
            items = db.get_all()
            favlist = [(1, '[B]%s[/B]'), (0, '%s')]
            if items:
                ListString = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?action=%s&action2=%s&%s=%s')
                for favbool, bbstring in favlist:
                    for addtime, string, fav in items:
                        if favbool == int(fav):
                            title = string.encode('utf-8')
                            contextMenu = [(self.localize('Search Control Window'),
                                            'xbmc.RunScript(%s,)' % os.path.join(ROOT, 'controlcenter.py'))]

                            contextMenu.append((self.localize('Individual Tracker Options'),
                                                    'XBMC.RunScript(%s)' % (os.path.join(ROOT, 'controlcenter.py,') + 'addtime=%s&title=%s' % (str(addtime), title))))
                            contextMenu.append((self.localize('Keyboard'),
                                                    'XBMC.ActivateWindow(Videos,%s)' % (sys.argv[0] + '?action=%s&action2=%s&%s=%s') % ('search', '&showKey=true', 'url', urllib.quote_plus(title))))
                            if int(fav) == 1:
                                contextMenu.append((self.localize('Delete from %s') % self.localize('Favourites SH'),
                                                    ListString % ('History', 'unfav', 'addtime', str(addtime))))
                                img = self.ROOT + '/icons/fav.png'
                            else:
                                contextMenu.append((self.localize('Add to %s') % self.localize('Favourites SH'),
                                                    ListString % ('History', 'fav', 'addtime', str(addtime)),))
                                img = self.ROOT + '/icons/unfav.png'
                            contextMenu.append((self.localize('Edit'),
                                                ListString % ('History', 'edit', 'addtime='+str(addtime)+'&title', urllib.quote_plus(title))))
                            contextMenu.append((self.localize('Delete from %s') % self.localize('Search History'),
                                                ListString % ('History', 'delete', 'addtime', str(addtime))))

                            link = {'url': title, 'addtime': str(addtime)}
                            self.drawItem(bbstring % title, 'search', link, image=img, contextMenu=contextMenu, replaceMenu=False)
            view_style('History')
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def WatchedHistory(self, params={}):
        db = WatchedHistoryDB()
        get = params.get
        action2 = get('action2')
        url = get('url')
        addtime = get('addtime')

        if action2 == 'add':
            db.add(url)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Watched History'), self.localize('Added!'))

        if action2 == 'delete':
            db.delete(addtime)
            xbmc.executebuiltin('Container.Refresh')
            showMessage(self.localize('Watched History'), self.localize('Deleted!'))

        if action2 == 'open':
            filename, foldername, path, url, seek, length, ind = db.get('filename, foldername, path, url, seek, length, ind', 'addtime', str(addtime))
            if os.path.exists(path):
                self.__settings__.setSetting("lastTorrent", path)
            else:
                torrent = Downloader.Torrent(self.userStorageDirectory, torrentFilesDirectory=self.torrentFilesDirectory)
                path = torrent.saveTorrent(url)
                self.__settings__.setSetting("lastTorrent", path)
            xbmc.executebuiltin(
                            'XBMC.ActivateWindow(%s)' % 'Videos,plugin://plugin.video.torrenter/?action=%s&url=%s'
            % ('torrentPlayer', path.encode('utf-8')))

        if action2 == 'playnoseek' or action2 == 'playwithseek':
            filename, path, url, seek, length, ind = db.get('filename, path, url, seek, length, ind', 'addtime', str(addtime))

            if action2 == 'playwithseek':
                #seek = seeking_warning(seek)
                seek = int(seek)
            else:
                seek = 0
            if os.path.exists(path):
                self.__settings__.setSetting("lastTorrent", path)
            else:
                torrent = Downloader.Torrent(self.userStorageDirectory, torrentFilesDirectory=self.torrentFilesDirectory)
                self.__settings__.setSetting("lastTorrent", torrent.saveTorrent(url))
            xbmc.executebuiltin('xbmc.RunPlugin("plugin://plugin.video.torrenter/?action=playTorrent&url='+str(ind)+'&seek='+str(seek)+'")')

        if action2 == 'clear':
            db.clear()
            showMessage(self.localize('Watched History'), self.localize('Clear!'))

        if not action2:
            items = db.get_all()
            debug('[WatchedHistory]: items - '+str(items))
            #favlist = [(1, '[B]%s[/B]'), (0, '%s')]
            if items:
                ListString = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?action=%s&action2=%s&%s=%s')
                #for favbool, bbstring in favlist:
                for addtime, filename, foldername, path, url, seek, length, ind, size in items:
                    seek = int(seek) if int(seek) > 3*60 else 0
                    watchedPercent = int((float(seek) / float(length if length else 1)) * 100)
                    duration = '%02d:%02d:%02d' % ((length / (60*60)), (length / 60) % 60, length % 60)
                    title = '[%d%%][%s] %s [%d MB]' %\
                            (watchedPercent, duration, filename.encode('utf-8'), int(size))
                    clDimgray = '[COLOR FF696969]%s[/COLOR]'

                    title = title + chr(10) + clDimgray % '(%s)' % foldername.encode('utf-8')
                    if self.torrent_player != '1' and seek > 0:
                        seek_text = '%02d:%02d:%02d' % ((seek / (60*60)), (seek / 60) % 60, seek % 60)
                        contextMenu = [(self.localize('Play (from %s)') % seek_text, ListString % ('WatchedHistory', 'playwithseek', 'addtime', str(addtime))),
                                       (self.localize('Play (from start)'), ListString % ('WatchedHistory', 'playnoseek', 'addtime', str(addtime))),]
                    else:
                        contextMenu = [(self.localize('Play'), ListString % ('WatchedHistory', 'playnoseek', 'addtime', str(addtime))),]
                    contextMenu.append((self.localize('Open Torrent'), ListString % ('WatchedHistory', 'open', 'addtime', str(addtime))),)
                    if watchedPercent >= 85:
                        img = self.ROOT + '/icons/stop-icon.png'
                    else:
                        img = self.ROOT + '/icons/pause-icon.png'

                    contextMenu.append((self.localize('Delete from %s') % self.localize('Watched History'),
                                        ListString % ('WatchedHistory', 'delete', 'addtime', str(addtime))))

                    link = {'url': str(ind), 'action2': 'play', 'addtime': str(addtime)}
                    self.drawItem(title, 'context', link, image=img, contextMenu=contextMenu, replaceMenu=False)
            view_style('History')
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def List(self, params={}):
        db = ListDB()
        get = params.get
        action2 = get('action2')
        info = get('info')
        addtime = get('addtime')

        if action2 == 'add':
            db.add(info)
            showMessage(self.localize('Personal List'), self.localize('Added!'))

        if action2 == 'delete':
            db.delete(addtime)
            showMessage(self.localize('Personal List'), self.localize('Deleted!'))

        if not action2:
            items = db.get_all()
            contentList = []
            if items:
                for addtime, info in items:
                    num = addtime * -1
                    jinfo = json.loads(urllib.unquote_plus(info))
                    title = jinfo.get('title')
                    original_title = jinfo.get('original_title')
                    year = jinfo.get('year')
                    img = jinfo.get('img')
                    info = jinfo.get('info')

                    contentList.append((
                        (int(num)), original_title, title, int(year), img, info,
                    ))
            self.drawcontentList(contentList, params)
            view_style('List')
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def drawContent(self, category_dict, provider=None, category=None, subcategory=None):
        if not category and not provider:
            self.drawItem('[COLOR FFFFFFFF][B]< %s >[/B][/COLOR]' % self.localize('Personal List'), 'List', image=self.ROOT + '/icons/list.png')
            for cat in category_dict.keys():
                cat_con = category_dict[cat]
                if isinstance(cat_con, dict):
                    link = json.dumps({'category': cat})
                else:
                    link = json.dumps({'category': cat, 'subcategory': True})
                self.drawItem('< %s >' % self.Content.translate(cat), 'openContent', link, isFolder=True)

        if category == 'sites' and not provider:
            for cat in category_dict.keys():
                link = json.dumps({'provider': cat})
                self.drawItem('[B]%s[/B]' % cat if self.contenterObject.get(cat).isScrappable() else cat, 'openContent',
                              link, isFolder=True)
        elif category == 'search' and not provider:
            keyboard = xbmc.Keyboard('', self.localize('Search Phrase') + ':')
            keyboard.doModal()
            query = keyboard.getText()
            if not query:
                return
            elif keyboard.isConfirmed():
                subcategory = query
            if subcategory:
                for cat in self.Contenters.get_active():
                    if self.contenterObject[cat].has_category(category):
                        link = json.dumps({'category': category, 'subcategory': subcategory, 'provider': cat})
                        title = '< %s - %s >' % (cat.encode('utf-8'), subcategory)
                        self.drawItem('[B]%s[/B]' % title if self.contenterObject.get(cat).isScrappable() else title,
                                      'openContent', link, isFolder=True)
        elif category and not provider and not subcategory:
            if isinstance(category_dict.get(category), dict):
                for cat in category_dict[category].keys():
                    if not cat == category:
                        link = json.dumps({'category': category, 'subcategory': cat, 'provider': provider})
                        self.drawItem('< %s >' % self.Content.translate(category, cat), 'openContent', link,
                                      isFolder=True)
            else:
                for cat in self.Contenters.get_active():
                    if self.contenterObject[cat].has_category(category):
                        link = json.dumps({'category': category, 'subcategory': subcategory, 'provider': cat})
                        self.drawItem('[B]%s[/B]' % cat if self.contenterObject.get(cat).isScrappable() else cat,
                                      'openContent', link, isFolder=True)

        if category and subcategory and not provider:
            for cat in category_dict.keys():
                if self.contenterObject.get(cat).has_category(category, subcategory):
                    link = json.dumps({'category': category, 'subcategory': subcategory, 'provider': cat})
                    self.drawItem('[B]%s[/B]' % cat if self.contenterObject.get(cat).isScrappable() else cat,
                                  'openContent', link, isFolder=True)

        if provider and not category:
            for cat in category_dict.keys():
                if isinstance(category_dict.get(cat), dict):
                    link = json.dumps({'category': cat, 'provider': provider})
                else:
                    link = json.dumps({'category': cat, 'subcategory': True, 'provider': provider})
                self.drawItem('< %s - %s >' % (provider.encode('utf-8'), self.Content.translate(cat)), 'openContent',
                              link, isFolder=True)

        if provider and category and not subcategory:
            for cat in category_dict[category].keys():
                if not cat == category:
                    link = json.dumps({'category': category, 'subcategory': cat, 'provider': provider})
                    self.drawItem('< %s - %s >' % (provider.encode('utf-8'), self.Content.translate(category, cat)),
                                  'openContent', link, isFolder=True)

        view_style('drawContent')
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def openContent(self, params={}):
        import Content
        self.contenterObject = {}
        self.Content = Content.Content()
        self.Contenters = Contenters()
        self.Contenters.first_time(self.scrapperDB_ver, self.language)
        get = params.get
        try:
            apps = json.loads(urllib.unquote_plus(get("url")))
        except:
            apps = {}
        category = apps.get('category')
        subcategory = apps.get('subcategory')
        provider = apps.get('provider')

        contenters = self.Contenters.list()
        for contenter in contenters:
            if ROOT + os.sep + 'resources' + os.sep + 'contenters' not in sys.path:
                sys.path.insert(0, ROOT + os.sep + 'resources' + os.sep + 'contenters')
            try:
                self.contenterObject[contenter] = getattr(__import__(contenter), contenter)()
            except Exception, e:
                log('Unable to use contenter: ' + contenter + ' at ' + ' Content(). Exception: ' + str(e))

        if not subcategory:
            if not category and not provider:
                self.drawContent(category_dict=self.Content.category_dict)

            if category and not provider:
                category_dict = self.Content.category_dict
                if category == 'sites':
                    category_dict = self.Contenters.get_activedic()
                self.drawContent(category_dict=category_dict, category=category)

            if provider:
                self.Content = self.contenterObject[provider]
                self.drawContent(category_dict=self.Content.category_dict, category=category, provider=provider)
        else:
            if provider:
                self.Content = self.contenterObject[provider]
                if category == 'search' and provider and subcategory == True:
                    keyboard = xbmc.Keyboard('', self.localize('Search Phrase') + ':')
                    keyboard.doModal()
                    query = keyboard.getText()
                    if not query:
                        return
                    elif keyboard.isConfirmed():
                        subcategory = query
                    if subcategory:
                        apps['subcategory'] = subcategory.decode('utf-8')
                    else:
                        return

                if not self.Content.isTracker():
                    self.draw(apps, mode='content')
                else:
                    self.draw(apps, mode='tracker')
            elif not provider:
                category_dict = self.Contenters.get_activedic()
                self.drawContent(category_dict=category_dict, category=category, subcategory=subcategory)

    def draw(self, apps, mode):
        category = apps.get('category')
        subcategory = apps.get('subcategory')
        provider = apps.get('provider')
        page = apps.get('page') if apps.get('page') else 1
        sort = apps.get('sort') if apps.get('sort') else 0
        apps_property={'page':page, 'sort':sort}
        log('draw: '+str((category, subcategory)))
        property = self.Content.get_property(category, subcategory)
        contentList = self.Content.get_contentList(category, subcategory, apps_property)
        if property and property.get('page'):
            apps['page'] = page + 1
            #print str(apps)
            self.drawItem('[COLOR FFFFFFFF][B]%s[/B][/COLOR]' % self.localize('Next Page'), 'openContent',
                          json.dumps(apps), isFolder=True)
        if property and property.get('sort'):
            if len(property.get('sort'))>sort+1:
                apps['sort'] = int(sort) + 1
            else:
                apps['sort'] = 0
            self.drawItem('[COLOR FFFFFFFF][B]%s %s[/B][/COLOR]' % (self.localize('Sort'), self.localize(property['sort'][apps['sort']]['name'])), 'openContent',
                          json.dumps(apps), isFolder=True)

        if mode == 'tracker':
            self.drawtrackerList(provider, contentList)
            view_style('drawtrackerList')
        elif mode == 'content':
            self.drawcontentList(contentList)
            view_style('drawcontentList')
            #if not self.debug: view_style('drawcontentList')

        if property and property.get('page'):
            self.drawItem('[COLOR FFFFFFFF][B]%s[/B][/COLOR]' % self.localize('Next Page'), 'openContent',
                          json.dumps(apps), isFolder=True)

        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def full_download(self, params={}):
        import Content
        self.contenterObject = {}
        self.Content = Content.Content()
        self.Contenters = Contenters()
        self.Contenters.first_time(self.scrapperDB_ver, self.language)
        self.breakdown = False

        get = params.get
        try:
            apps = json.loads(urllib.unquote_plus(get("url")))
        except:
            apps = {}
        provider = apps.get('provider')
        action = apps.get('action')

        if action == 'delete':
            dirname = xbmc.translatePath('special://temp')
            dirname = os.path.join(dirname, 'xbmcup', 'plugin.video.torrenter')
            scrapers = {'tvdb': 'TheTVDB.com', 'tmdb': 'TheMovieDB.org', 'kinopoisk': 'KinoPoisk.ru'}
            for i in scrapers.keys():
                xbmcvfs.delete(os.path.join(dirname, i +'.'+self.language+ '.db'))
            showMessage(self.localize('Reset All Cache DBs'), self.localize('Deleted!'))
            return

        if action == 'reset':
            self.__settings__.setSetting('oldc_metadata', 'false')
            self.__settings__.setSetting('metadata', 'false')
            showMessage('Done', 'Reset')
            return

        contenters = self.Contenters.list()
        for contenter in contenters:
            if ROOT + os.sep + 'resources' + os.sep + 'contenters' not in sys.path:
                sys.path.insert(0, ROOT + os.sep + 'resources' + os.sep + 'contenters')
            try:
                self.contenterObject[contenter] = getattr(__import__(contenter), contenter)()
            except Exception, e:
                log('Unable to use contenter: ' + contenter + ' at ' + ' Content(). Exception: ' + str(e))

        if provider:
            for cat in self.Contenters.get_activedic().keys():
                if provider == 'all' or cat == provider:
                    self.Content = self.contenterObject[cat]
                    if self.Content.isScrappable():
                        self.provider = cat
                        category_dict = self.Content.category_dict
                        for category in category_dict.keys():
                            if category not in ['search']:
                                if isinstance(category_dict.get(category), dict):
                                    for subcategory in category_dict.get(category).keys():
                                        if subcategory != category and not subcategory == True:
                                            if self.Content.isPages() and self.Content.get_property(category,
                                                                                                    subcategory):
                                                for i in range(1, 5 if category!='year' else 2):
                                                    contentList = self.Content.get_contentList(category, subcategory, {'page':i})
                                                    self.drawcontentList(contentList)
                                                    if self.breakdown: break
                                            else:
                                                contentList = self.Content.get_contentList(category, subcategory)
                                                self.drawcontentList(contentList)
                                        if self.breakdown: break
                                if not isinstance(category_dict.get(category), dict):
                                    contentList = self.Content.get_contentList(category, subcategory=True)
                                    self.drawcontentList(contentList)

                                if self.breakdown: break
                        showMessage('','')
                        xbmc.sleep(1000)
                        showMessage('','')
                        xbmc.sleep(1000)
                        showMessage('','')
                        dialog=xbmcgui.Dialog()
                        x=dialog.ok('Done!','Bases are up to date!')
        else:
            self.drawItem('[B]%s[/B]' % "Download All", 'full_download', json.dumps({'provider': "all"}), isFolder=True)
            for cat in self.Contenters.get_activedic().keys():
                link = json.dumps({'provider': cat})
                if self.contenterObject.get(cat).isScrappable():
                    self.drawItem('[B]%s[/B]' % cat, 'full_download', link, isFolder=True)
            self.drawItem(self.localize('Reset All Cache DBs'), 'full_download', json.dumps({'action': 'delete'}),
                          isFolder=True)
            self.drawItem('Reset metadata config', 'full_download', json.dumps({'action': 'reset'}), isFolder=True)
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def drawcontentList(self, contentList, params={}):
        from resources.scrapers.scrapers import Scrapers
        contentList = sorted(contentList, key=lambda x: x[0], reverse=True)
        self.Scraper = Scrapers()
        progressBar = xbmcgui.DialogProgress()
        progressBar.create(self.localize('Please Wait'), self.localize('Waiting for website response...'))
        i = 0
        debug = 0
        ListString = 'XBMC.RunPlugin(%s)' % (sys.argv[0] + '?action=List&action2=%s&%s=%s')
        meta = None
        scrapers = {'tvdb': 'TheTVDB.com', 'tmdb': 'TheMovieDB.org', 'kinopoisk': 'KinoPoisk.ru'}
        for num, originaltitle, title, year, img, info in contentList:
            i = i + 1
            time.sleep(0.005)
            ListInfo = {u'title': title, u'original_title': originaltitle, u'year': year, u'img': img, u'info': info}
            iterator = int((float(i) / len(contentList)) * 100)
            dialogText = self.localize('Search and cache information for:')
            label = title
            title = contenter_title = title.encode('utf-8', 'ignore')
            search_url = {}
            if title:               search_url['title'] = title
            if img:                 search_url['img'] = img
            if originaltitle:       search_url['originaltitle'] = originaltitle
            if year:                search_url['year'] = str(year)
            if info.get('episode'): search_url['episode'] = str(info.get('episode'))
            if info.get('season'):  search_url['season'] = str(info.get('season'))

            if self.__settings__.getSetting("metadata") == 'true':

                if originaltitle:
                    search = [originaltitle, label]
                else:
                    search = [label]

                if info.get('tvshowtitle'):
                    scraper = 'tvdb'
                else:
                    scraper = 'tmdb'

                progressBar.update(iterator, dialogText, title, scrapers[scraper])
                meta = self.Scraper.scraper(scraper, {'label': title, 'search': search, 'year': year}, self.language)
                log('meta:'+str(meta))
                if self.language == 'ru':
                    if not meta.get('info').get('title') or \
                            not meta.get('properties').get('fanart_image') or not meta.get('icon'):
                        scraper = 'kinopoisk'
                        progressBar.update(iterator, dialogText, title, scrapers[scraper])
                        if info.get('tvshowtitle'):
                            if originaltitle:
                                search = [originaltitle, label + u' (сериал)']
                            else:
                                search = [label + u' (сериал)']
                        kinometa = self.Scraper.scraper(scraper, {'label': title, 'search': search,
                                                                  'year': year}, self.language)

                        log('kinometa:'+str(kinometa))

                        for section in kinometa.keys():
                            if isinstance(kinometa[section], dict):
                                if not meta.get(section):
                                    meta[section] = kinometa[section]
                                    continue
                                else:
                                    for sitem in kinometa[section].keys():
                                        meta[section][sitem] = kinometa[section][sitem]
                            elif not meta.get(section):
                                meta[section] = kinometa[section]

                #print 'meta:'+str(meta)
                #if self.debug and meta.get('info').get('title') and meta.get('info').get('title').encode('utf-8')==title: continue

                #print 'meta: '+str((scraper, {'label': title, 'search': [label, originaltitle],
                #                                 'year': year}))
                debug = 0
                if meta.get('info').get('title'):
                    if self.debug and 1 == debug:
                        title = meta.get('info').get('title').encode('utf-8') + '/' + title + '/'
                        if originaltitle: title += originaltitle.encode('utf-8')
                    else:
                        title = meta.get('info').get('title')

            listitem = xbmcgui.ListItem(title)
            images = {'thumb': img, #'icon': img,
                      'poster': img,# 'banner': img,
                      #'fanart': img, 'landscape': img,
                      # 'clearart': image, 'clearlogo': image,
                      }
            listitem.setArt(images)
            listitem.setInfo(type='Video', infoLabels=info)
            if meta:
                listitem=itemScrap(listitem, meta)
                if meta.get('icon'):
                    search_url['img'] = meta.get('icon')
                if meta.get('info').get('title'):
                    search_url['title'] = meta.get('info').get('title').encode('utf-8')
                    if search_url['title'] != contenter_title:
                        search_url['contenter_title'] = contenter_title
                if meta.get('info').get('originaltitle'):
                    search_url['originaltitle'] = meta.get('info').get('originaltitle').encode('utf-8')

            contextMenu = [(self.localize('Search Control Window'),
                            'xbmc.RunScript(%s,)' % os.path.join(ROOT, 'controlcenter.py'))]
            if params.get('action') == 'List':
                contextMenu.append((self.localize('Delete from %s') % self.localize('Personal List'),
                                    ListString % ('delete', 'addtime', str(num * -1))))
            else:
                contextMenu.append((self.localize('Add to %s') % self.localize('Personal List'),
                                    ListString % ('add', 'info', urllib.quote_plus(json.dumps(ListInfo)))), )

            contextMenu.append((self.localize('Information'), 'xbmc.Action(Info)'))

            listitem.addContextMenuItems(contextMenu, replaceItems=False)
            url = '%s?action=%s&url=%s' % (sys.argv[0], 'searchOption', urllib.quote_plus(json.dumps(search_url)))
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True)

            if progressBar.iscanceled():
                self.breakdown = True
                showMessage('< %s >' % self.localize('Content Lists'), self.localize('Canceled by User'))
                break
                #break

        progressBar.update(0)
        progressBar.close()
        if self.debug and 1 == debug: lockView('wide')

    def drawtrackerList(self, provider, contentList):
        contentList = sorted(contentList, key=lambda x: x[0], reverse=True)
        if self.contenterObject[provider].isSearcher():
            Searchers().checkExist(provider)
        for num, originaltitle, title, year, img, info in contentList:
            if not info.get('label'):
                continue

            try:#spanish non utf-8 fix
                title = title.encode('utf-8', 'ignore')
            except:
                continue
            log(str(info))

            if info.get('link'):
                if isinstance(info.get('link'), tuple):
                    url=info.get('link')[0]
                else:
                    url=info.get('link')

                if self.contenterObject[provider].isSearcher():
                    link = {'url': '%s::%s' % (provider, url), 'thumbnail': img}
                else:
                    link = {'url': url, 'thumbnail': img}

            contextMenu = [
                    (self.localize('Download via T-client'),
                     'XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s') % (
                     sys.argv[0], 'downloadFilesList', urllib.quote_plus(link['url']))),
                    (self.localize('Download via Libtorrent'),
                     'XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s') % (
                     sys.argv[0], 'downloadLibtorrent', urllib.quote_plus(link['url'])))
                ]

            if isinstance(info, dict) and info.get('infolink'):
                contextMenu.append((self.localize('Information'),
                    'XBMC.RunPlugin(%s)' % ('%s?action=%s&provider=%s&url=%s&link=%s') % (
                    sys.argv[0], 'ActionInfo', provider, info.get('infolink'), link['url'])))

            if self.open_option==0:
                self.drawItem(title, 'openTorrent', link, image=img, info=info, contextMenu=contextMenu, replaceMenu=False)
            elif self.open_option==1:
                self.drawItem(title, 'context', link, image=img, info=info, contextMenu=contextMenu, replaceMenu=False)
            elif self.open_option==2:
                self.drawItem(title, 'downloadFilesList', link, image=img, info=info, contextMenu=contextMenu, replaceMenu=False)
            elif self.open_option==3:
                self.drawItem(title, 'downloadLibtorrent', link, image=img, info=info, contextMenu=contextMenu, replaceMenu=False)
            #self.drawItem(title, 'openTorrent', link, img, info=info, contextMenu=contextMenu, replaceMenu=False)

    def searchOption(self, params={}):
        try:
            apps = json.loads(urllib.unquote_plus(params.get("url")))
            get = apps.get
        except:
            return

        options = []

        img, save_folder = '',''
        if get('img'): img = get('img')

        if get('title'):
            save_folder=get('title')
            options.append(get('title'))

        if get('originaltitle') and get('originaltitle') != get('title'):
            options.append(get('originaltitle'))

        if get('contenter_title') and get('contenter_title') != get('title') and get('originaltitle') != get(
                'contenter_title'):
            options.append(get('contenter_title'))

        if get('year'):
            save_folder=save_folder+' ('+get('year')+')'
            if get('title'): options.append('%s %s' % (get('title'), get('year')))
            if get('originaltitle') and get('originaltitle') != get('title'): options.append(
                '%s %s' % (get('originaltitle'), get('year')))
            if get('contenter_title') and get('contenter_title') != get('title') and get('originaltitle') != get(
                    'contenter_title'): options.append('%s %s' % (get('contenter_title'), get('year')))

        if get('episode') and get('season'):
            if get('title'): options.append('%s S%2dE%2d' % (get('title'), int(get('season')), int(get('episode'))))
            if get('original_title'): options.append(
                '%s S%2dE%2d' % (get('original_title'), int(get('season')), int(get('episode'))))

        search_phrase=self.__settings__.getSetting('search_phrase')
        if search_phrase!='':
            x=[]
            x.extend(options)
            for title in x:
                options.append(title+' '+search_phrase)

        for title in options:
            try:
                title=title.encode('utf-8')
                save_folder=save_folder.encode('utf-8')
            except: pass
            link = {'url': title, 'thumbnail': img, 'save_folder':save_folder}
            #print str(link)
            self.drawItem(title, 'search', link, img)

        view_style('searchOption')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def drawItem(self, title, action, link='', image='', isFolder=True, contextMenu=None, replaceMenu=True, action2='', fileSize=0L,
                 info={}):
        #log('[drawItem]:'+str((title, action, image, isFolder, contextMenu, replaceMenu, action2, info)))
        listitem = xbmcgui.ListItem(title)
        images = {'icon':image, 'thumb':image}
        images = {'icon': image, 'thumb': image,
                  'poster': image, 'banner': image,
                  #'fanart': image, 'landscape': image,
                  #'clearart': image, 'clearlogo': image,
                  }
        listitem.setArt(images)
        """
        setArt(values) -- Sets the listitem's art
         values : dictionary - pairs of { label: value }.
            - Some default art values (any string possible):
                - thumb : string - image filename
                - poster : string - image filename
                - banner : string - image filename
                - fanart : string - image filename
                - clearart : string - image filename
                - clearlogo : string - image filename
                - landscape : string - image filename
                - icon : string - image filename
        example:
                - self.list.getSelectedItem().setArt({ 'poster': 'poster.png', 'banner' : 'banner.png' })
        """
        if not info: info = {"Title": title, "plot": title}
        if not isFolder and fileSize:
            info['size'] = fileSize
        if isinstance(link, dict):
            link_url = ''
            for key in link.keys():
                if link.get(key):
                    link_url = '%s&%s=%s' % (link_url, key, urllib.quote_plus(link.get(key)))
            url = '%s?action=%s' % (sys.argv[0], action) + link_url
        else:
            url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(link))
        if action2:
            url = url + '&url2=%s' % urllib.quote_plus(ensure_str(action2))
        if not contextMenu:
            contextMenu = [(self.localize('Search Control Window'),
                            'xbmc.RunScript(%s,)' % os.path.join(ROOT, 'controlcenter.py'))]
            replaceMenu = False
        if isFolder:
            listitem.setProperty("Folder", "true")
            listitem.setInfo(type='Video', infoLabels=info)
        else:
            listitem.setInfo(type='Video', infoLabels=info)
            listitem.setArt({'thumb': image})
        if contextMenu:
            listitem.addContextMenuItems(contextMenu, replaceItems=replaceMenu)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=isFolder)

    def getParameters(self, parameterString):
        commands = {}
        splitCommands = parameterString[parameterString.find('?') + 1:].split('&')
        for command in splitCommands:
            if (len(command) > 0):
                splitCommand = command.split('=')
                if (len(splitCommand) > 1):
                    name = splitCommand[0]
                    value = splitCommand[1]
                    commands[name] = value
        return commands

    def executeAction(self, params={}):
        get = params.get
        if hasattr(self, get("action")):
            getattr(self, get("action"))(params)
        else:
            self.sectionMenu()

    def uTorrentBrowser(self, params={}):
        from resources.utorrent.net import Download
        menu, dirs = [], []
        contextMenustring = 'XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s') % (sys.argv[0], 'uTorrentBrowser', '%s')
        get = params.get
        try:
            apps = json.loads(urllib.unquote_plus(get("url")))
        except:
            apps = {}
        action = apps.get('action')
        hash = apps.get('hash')
        ind = apps.get('ind')
        tdir = apps.get('tdir')

        #print str(action)+str(hash)+str(ind)+str(tdir)

        DownloadList = Download().list()
        if DownloadList == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
            return

        if action:
            if action == 'context':
                xbmc.executebuiltin("Action(ContextMenu)")
                return
            if (ind or ind == 0) and action in ('0', '3'):
                Download().setprio_simple(hash, action, ind)
            elif action in ['play','copy']:
                p, dllist, i, folder, filename = DownloadList, Download().listfiles(hash), 0, None, None
                for data in p:
                    if data['id'] == hash:
                        folder = data['dir']
                        break
                if isRemoteTorr():
                    t_dir = self.__settings__.getSetting("torrent_dir")
                    torrent_replacement = self.__settings__.getSetting("torrent_replacement")
                    empty = [None, '']
                    if t_dir in empty or torrent_replacement in empty:
                        if xbmcgui.Dialog().yesno(
                                self.localize('Remote Torrent-client'),
                                self.localize('You didn\'t set up replacement path in setting.'),
                                self.localize('For example /media/dl_torr/ to smb://SERVER/dl_torr/. Setup now?')):
                            if t_dir in empty:
                                torrent_dir()
                            self.__settings__.openSettings()
                        return
                    #print str(folder)+str(torrent_dir)+str(torrent_replacement)+str(tdir)
                    folder = folder.replace(t_dir, torrent_replacement)
                if (ind or ind == 0) and action == 'play':
                    for data in dllist:
                        if data[2] == int(ind):
                            filename = data[0]
                            break
                    filename = os.path.join(folder, filename)
                    xbmc.executebuiltin('xbmc.PlayMedia("' + filename.encode('utf-8') + '")')
                elif tdir and action == 'copy':
                    path = os.path.join(localize_path(folder), localize_path(tdir))
                    dirs, files=xbmcvfs.listdir(path)
                    if len(dirs) > 0:
                        dirs.insert(0, self.localize('./ (Root folder)'))
                        for dd in dirs:
                            dd = file_decode(dd)
                            dds=xbmcvfs.listdir(os.path.join(path,dd))[0]
                            if len(dds)>0:
                                for d in dds:
                                    dirs.append(dd+os.sep+d)
                        ret = xbmcgui.Dialog().select(self.localize('Choose directory:'), dirs)
                        if ret > 0:
                            path=os.path.join(path, dirs[ret])
                            dirs, files=xbmcvfs.listdir(path)
                    for file in files:
                        file = localize_path(file)
                        if not xbmcvfs.exists(os.path.join(path, file)):
                            xbmcvfs.delete(os.path.join(path, file))
                        xbmcvfs.copy(os.path.join(path, file),os.path.join(folder, file))
                        i=i+1
                    showMessage(self.localize('Torrent-client Browser'), self.localize('Copied %d files!') % i, forced=True)
                return
            elif not tdir and action not in ('0', '3'):
                Download().action_simple(action, hash)
            elif action in ('0', '3'):
                dllist = sorted(Download().listfiles(hash), key=lambda x: x[0])
                for name, percent, ind, size in dllist:
                    if tdir:
                        if '/' in name and tdir in name:
                            menu.append((hash, action, str(ind)))
                    else:
                        menu.append((hash, action, str(ind)))
                Download().setprio_simple_multi(menu)
                return
            xbmc.executebuiltin('Container.Refresh')
            return

        if not hash:
            for data in DownloadList:
                status = " "
                img=''
                if data['status'] in ('seed_pending', 'stopped'):
                    status = TextBB(' [||] ', 'b')
                elif data['status'] in ('seeding', 'downloading'):
                    status = TextBB(' [>] ', 'b')
                if data['status']   == 'seed_pending':
                    img = os.path.join(self.ROOT, 'icons', 'pause-icon.png')
                elif data['status'] == 'stopped':
                    img = os.path.join(self.ROOT, 'icons', 'stop-icon.png')
                elif data['status'] == 'seeding':
                    img = os.path.join(self.ROOT, 'icons', 'upload-icon.png')
                elif data['status'] == 'downloading':
                    img = os.path.join(self.ROOT, 'icons', 'download-icon.png')
                menu.append(
                    {"title": '[' + str(data['progress']) + '%]' + status + data['name'] + ' [' + str(
                        data['ratio']) + ']', "image":img,
                     "argv": {'hash': str(data['id'])}})
        elif not tdir:
            dllist = sorted(Download().listfiles(hash), key=lambda x: x[0])
            for name, percent, ind, size in dllist:
                if '/' not in name:
                    menu.append({"title": '[' + str(percent) + '%]' + '[' + str(size) + '] ' + name, "image":'',
                                 "argv": {'hash': hash, 'ind': str(ind), 'action': 'context'}})
                else:
                    tdir = name.split('/')[0]
                    # tfile=name[len(tdir)+1:]
                    if tdir not in dirs: dirs.append(tdir)
        elif tdir:
            dllist = sorted(Download().listfiles(hash), key=lambda x: x[0])
            for name, percent, ind, size in dllist:
                if '/' in name and tdir in name:
                    menu.append(
                        {"title": '[' + str(percent) + '%]' + '[' + str(size) + '] ' + name[len(tdir) + 1:], "image":'',
                         "argv": {'hash': hash, 'ind': str(ind), 'action': 'context'}})

        for i in dirs:
            app = {'hash': hash, 'tdir': i}
            link = json.dumps(app)
            popup = []
            folder = True
            actions = [('3', self.localize('High Priority Files')), ('copy', self.localize('Copy Files in Root')), ('0', self.localize('Skip All Files'))]
            for a, title in actions:
                app['action'] = a
                popup.append((self.localize(title), contextMenustring % urllib.quote_plus(json.dumps(app))))
            self.drawItem(unicode(i), 'uTorrentBrowser', link, isFolder=folder, contextMenu=popup, replaceMenu=True)

        for i in menu:
            app = i['argv']
            link = json.dumps(app)
            img = i['image']
            popup = []
            if not hash:
                actions = [('start', self.localize('Start')), ('stop', self.localize('Stop')),
                           ('remove', self.localize('Remove')),
                           ('3', self.localize('High Priority Files')), ('0', self.localize('Skip All Files')),
                           ('removedata', self.localize('Remove with files'))]

                folder = True
            else:
                actions = [('3', self.localize('High Priority')), ('0', self.localize('Skip File')),
                           ('play', self.localize('Play File'))]
                folder = False
            for a, title in actions:
                app['action'] = a
                popup.append((self.localize(title), contextMenustring % urllib.quote_plus(json.dumps(app))))

            self.drawItem(unicode(i['title']), 'uTorrentBrowser', link, image=img, isFolder=folder, contextMenu=popup,
                          replaceMenu=True)
        view_style('uTorrentBrowser')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
        #xbmc.sleep(30000)
        #xbmc.executebuiltin('Container.Refresh')
        return

    def clearStorage(self, params={}):
        clearStorage(self.userStorageDirectory, force=True)

    def magentPlayer(self, params={}):
        defaultKeyword = params.get('url')
        if not defaultKeyword:
            defaultKeyword = ''
            keyboard = xbmc.Keyboard(defaultKeyword, self.localize('Magnet-link (magnet:...)') + ':')
            keyboard.doModal()
            query = keyboard.getText()
            if not query:
                return
            if not re.match("^magnet\:.+$", query):
                showMessage(self.localize('Error'), self.localize('Not a magnet-link!'))
                return
            elif keyboard.isConfirmed():
                params["url"] = urllib.quote_plus(unescape(urllib.unquote_plus(query)))
        else:
            params["url"] = urllib.quote_plus(unescape(urllib.unquote_plus(defaultKeyword)))
        self.torrentPlayer(params)

    def torrentPlayer(self, params={}):
        get = params.get
        url = unquote(get("url"), None)
        tdir = unquote(get("url2"), None)

        if not url:
            action = xbmcgui.Dialog()
            url = action.browse(1, self.localize('Choose .torrent in video library'), 'video', '.torrent')
            url = urllib.quote_plus(url)
            torrent = Downloader.Torrent(self.userStorageDirectory, torrentFilesDirectory=self.torrentFilesDirectory)
            self.__settings__.setSetting("lastTorrent", torrent.saveTorrent(url))
            self.__settings__.setSetting("lastTorrentUrl", url)
            if url:
                xbmc.executebuiltin("Dialog.Close(all,true)")
                xbmc.executebuiltin(
                                'XBMC.ActivateWindow(%s)' % 'Videos,plugin://plugin.video.torrenter/?action=%s&url=%s'
                % ('torrentPlayer', url))
                return
        if url:
            if self.searchwindowmode > 1:
                self.openTorrent(params)
            else:
                import searchwindow
                params = {'mode': 'open_torrent', 'link': url}
                searchwindow.main(params)

    def userStorage(self, params):
        save=False
        if self.__settings__.getSetting("keep_files")=='2':
            dialog = xbmcgui.Dialog()
            save = dialog.yesno(self.localize('Ask to save'), self.localize('Would you like to save this file?'))
            if save:
                self.userStorageDirectory = os.path.join(self.userStorageDirectory, 'Saved Files')
        if self.__settings__.getSetting("keep_files")=='1' and\
                        self.__settings__.getSetting("ask_dir")=='true' or\
                                self.__settings__.getSetting("keep_files")=='2' and\
                        self.__settings__.getSetting("ask_dir")=='true' and save:
            save_folder = unquote(params.get('save_folder'), '')
            if len(save_folder)>0:
                default = os.path.join(self.userStorageDirectory, save_folder)
            else:
                default = self.userStorageDirectory
            keyboard = xbmc.Keyboard(default, self.localize('Save to path') + ':')
            keyboard.doModal()
            dirname = keyboard.getText()
            if not keyboard.isConfirmed():
                return
            if len(dirname)>0:
                self.userStorageDirectory=dirname

    def playTorrent(self, params={}):
        if params.get('filename'):
            torrentUrl = unquote(params.get('filename'))
        else:
            torrentUrl = self.__settings__.getSetting("lastTorrent")
        #xbmc.executebuiltin('Action(Stop)')
        if self.torrent_player != '1' and params.get('external') == '1' and not params.get('seek'):
            params['seek'] = watched_seek(torrentUrl, params['url'])

        self.userStorage(params)
        if self.torrent_player == '0':
            from Player import TorrentPlayer
            if 0 != len(torrentUrl):
                self.Player = TorrentPlayer(userStorageDirectory=self.userStorageDirectory, torrentUrl=torrentUrl, params=params)
            else:
                log(self.__plugin__ + " Unexpected access to method playTorrent() without torrent content")
        elif self.torrent_player == '2':
            from Anteoloader import AnteoPlayer
            if 0 != len(torrentUrl):
                self.Player = AnteoPlayer(userStorageDirectory=self.userStorageDirectory, torrentUrl=torrentUrl, params=params)
            else:
                log(self.__plugin__ + " Unexpected access to method playTorrent() without torrent content")
        elif self.torrent_player == '3':
            from Inposloader import InposPlayer
            if 0 != len(torrentUrl):
                self.Player = InposPlayer(userStorageDirectory=self.userStorageDirectory, torrentUrl=torrentUrl, params=params)
            else:
                log(self.__plugin__ + " Unexpected access to method playTorrent() without torrent content")
        elif self.torrent_player == '4':
            xbmc.executebuiltin('XBMC.ActivateWindow(%s)' % 'Videos,plugin://plugin.video.yatp/?action=play&torrent=%s&file_index=%s' % (urllib.quote_plus(torrentUrl), params['url']))
            #xbmc.executebuiltin('xbmc.RunPlugin("plugin://plugin.video.yatp/?action=play&torrent=%s&file_index=%s")' % (urllib.quote_plus(torrentUrl), params['url']))
        elif self.torrent_player == '1':
            __ASsettings__ = xbmcaddon.Addon(id='script.module.torrent.ts')
            folder=__ASsettings__.getSetting("path")
            save=__ASsettings__.getSetting("save")
            __ASsettings__.setSetting("path", xbmc.translatePath(self.__settings__.getSetting("storage")))
            __ASsettings__.setSetting("save", self.__settings__.getSetting("keep_files"))
            xbmc.sleep(1000)
            torrent = Downloader.Torrent(self.userStorageDirectory, torrentUrl, self.torrentFilesDirectory)
            get = params.get
            ind = get("url")
            icon = get("thumbnail") if get("thumbnail") else ''
            path = torrent.getFilePath(int(ind))
            label = unquote(get("label"), os.path.basename(path))
            torrent.play_url_ind(int(ind), label, icon)
            torrent.__exit__()
            __ASsettings__.setSetting("path", folder)
            __ASsettings__.setSetting("save", save)

    def saveUrlTorrent(self, url):
        torrentFile = self.userStorageDirectory + os.sep + self.torrentFilesDirectory + os.sep + md5(url) + '.torrent'
        try:
            request = urllib2.Request(url)
            request.add_header('Referer', url)
            request.add_header('Accept-encoding', 'gzip')
            result = urllib2.urlopen(request)
            if result.info().get('Content-Encoding') == 'gzip':
                from StringIO import StringIO
                import zlib
                buf = StringIO(result.read())
                decomp = zlib.decompressobj(16 + zlib.MAX_WBITS)
                content = decomp.decompress(buf.getvalue())
            else:
                content = result.read()
            localFile = xbmcvfs.File(torrentFile, "wb+")
            localFile.write(content)
            localFile.close()
            return torrentFile
        except:
            log('Unable to save torrent file from "' + url + '" to "' + torrentFile + '" in Torrent::saveTorrent')
            return

    def playSTRM(self, params={}):
        get = params.get
        xbmc.executebuiltin('xbmc.Playlist.Clear')
        url = unquote(get("url"), None)
        url2 = unquote(get("url2"), None)
        index = unquote(get("index"), None)
        if url:
            self.__settings__.setSetting("lastTorrentUrl", url)
            classMatch = re.search('(\w+)::(.+)', url)
            if classMatch:
                searcher = classMatch.group(1)
                url = Searchers().downloadWithSearcher(classMatch.group(2), searcher)
            torrent = Downloader.Torrent(self.userStorageDirectory, torrentFilesDirectory=self.torrentFilesDirectory)
            filename = torrent.saveTorrent(url)
            self.__settings__.setSetting("lastTorrent", filename)
            if index == None: index = chooseFile(torrent.getContentList())
            if index:
                #params = {'url': index, 'filename': filename}
                #if url2: params['url2'] = url2
                #self.playTorrent(params)

                url = 'plugin://plugin.video.torrenter/?action=playTorrent'
                url += '&url=%s' % (str(index))
                if url2: url += '&url2=%s' % (url2)
                if filename: url += '&filename=%s' % (urllib.quote_plus(ensure_str(filename)))

                xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))

    def openTorrent(self, params={}):
        get = params.get
        tdir = unquote(get("url2"),None)
        thumbnail = unquote(get("thumbnail"), False) or 'DefaultVideo.png'
        save_folder = unquote(get("save_folder"),'')
        url = urllib.unquote_plus(get("url"))

        self.__settings__.setSetting("lastTorrentUrl", url)
        classMatch = re.search('(\w+)::(.+)', url)
        if classMatch:
            searcher = classMatch.group(1)
            url = Searchers().downloadWithSearcher(classMatch.group(2), searcher)
            self.__settings__.setSetting("lastTorrent", url)

        torrent = Downloader.Torrent(self.userStorageDirectory,
                                     torrentFilesDirectory=self.torrentFilesDirectory)
        if not torrent: torrent = Downloader.Torrent(self.userStorageDirectory,
                                                     torrentFilesDirectory=self.torrentFilesDirectory)
        filename = torrent.saveTorrent(url)
        self.__settings__.setSetting("lastTorrent", filename)
    
        append_filesize = self.__settings__.getSetting("append_filesize") == 'true'
        hasSize = False
        contentList = []
        for filedict in torrent.getContentList():
            fileTitle = filedict.get('title')
            size = filedict.get('size')
            if size:
                if append_filesize:
                    fileTitle += ' [%d MB]' % (size / 1024 / 1024)
                hasSize = True
            contentList.append([unescape(fileTitle), str(filedict.get('ind')), size])
        #contentList = sorted(contentList, key=lambda x: x[0])

        dirList, contentListNew = cutFolder(contentList, tdir)

        for title in dirList:
            self.drawItem(title, 'openTorrent', url, isFolder=True, action2=title)

        ids_video_result = get_ids_video(contentListNew)
        ids_video=''

        if len(ids_video_result)>0:
            for identifier in ids_video_result:
                ids_video = ids_video + str(identifier) + ','

        for title, identifier, filesize in contentListNew:
            contextMenu = [
                (self.localize('Download via T-client'),
                 'XBMC.RunPlugin(%s)' % ('%s?action=%s&ind=%s') % (
                 sys.argv[0], 'downloadFilesList', str(identifier))),
                (self.localize('Download via Libtorrent'),
                 'XBMC.RunPlugin(%s)' % ('%s?action=%s&ind=%s') % (
                 sys.argv[0], 'downloadLibtorrent', str(identifier))),
            ]
            link = {'url': identifier, 'thumbnail': thumbnail, 'save_folder':save_folder,
                    'filename':ensure_str(filename)}
            self.drawItem(title, 'playTorrent', link, image=thumbnail, isFolder=False,
                          action2=ids_video.rstrip(','), contextMenu=contextMenu,
                          replaceMenu=False, fileSize=filesize)
        view_style('openTorrent')
        p_handle = int(sys.argv[1])
        try:
            xbmcplugin.addSortMethod(p_handle, xbmcplugin.SORT_METHOD_LABEL)
            if hasSize:
                xbmcplugin.addSortMethod(p_handle, xbmcplugin.SORT_METHOD_SIZE)
            xbmc.executebuiltin("Container.SetSortMethod(%s)" % str(1))
            #xbmc.executebuiltin("Container.SetSortDirection()")
        except:
            log(' !!!! >>>> Faild to set sorting method to ' + str(xbmcplugin.SORT_METHOD_SIZE))
            pass

        xbmcplugin.endOfDirectory(p_handle, succeeded=True)

    def openSection(self, params={}):
        get = params.get
        url = urllib.unquote_plus(get("url"))
        addtime=get("addtime")
        if self.__settings__.getSetting('history')=='true':
            HistoryDB().add(url)
        external = unquote(get("external"))
        searchersList = []
        if not external or external == 'torrenterall':
            if addtime:
                providers=HistoryDB().get_providers(addtime)
                if providers:
                    for searcher in providers:
                        searchersList.append(searcher)
            if not addtime or not searchersList:
                searchersList = Searchers().get_active()
        elif external == 'torrenterone':
            slist = Searchers().list().keys()
            ret = xbmcgui.Dialog().select(self.localize('Choose searcher')+':', slist)
            if ret > -1 and ret < len(slist):
                external = slist[ret]
                searchersList.append(external)
        else:
            searchersList.append(external)

        filesList=search(url, searchersList, get('isApi'))
        if self.__settings__.getSetting('sort_search')=='true':
            self.__settings__.setSetting('sort_search','1')
        if int(self.__settings__.getSetting('sort_search'))==0:
            filesList = sorted(filesList, key=lambda x: x[0], reverse=True)
        elif int(self.__settings__.getSetting('sort_search'))==2:
            filesList = sorted(filesList, key=lambda x: x[4], reverse=False)

        if not external or get('from_searcher'):
            self.showFilesList(filesList, params)
        else:
            self.showFilesListExternal(filesList, params)

    def controlCenter(self, params={}):
        xbmc.executebuiltin(
            'xbmc.RunScript(%s,)' % os.path.join(ROOT, 'controlcenter.py'))

    def searchWindow(self, params={}):
        import searchwindow
        searchwindow.main(params)

    def showFilesList(self, filesList, params={}):
        get = params.get
        thumbnail = unquote(get("thumbnail"),'')
        save_folder = unquote(get("save_folder"),'')
        for (order, seeds, leechers, size, title, link, image) in filesList:
            link_dict = {'url': link, 'thumbnail': thumbnail, 'save_folder':save_folder}
            link_url=''
            for key in link_dict.keys():
                if link_dict.get(key):
                    link_url = '%s&%s=%s' % (link_url, key, urllib.quote_plus(link_dict.get(key)))
            contextMenu = [
                (self.localize('Download via T-client'),
                 'XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s') % (
                 sys.argv[0], 'downloadFilesList', urllib.quote_plus(link))),
                (self.localize('Download via Libtorrent'),
                 'XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s') % (
                 sys.argv[0], 'downloadLibtorrent', urllib.quote_plus(link))),
                (self.localize('Open'),
                 'XBMC.Container.Update(%s)' % ('%s?action=%s%s') % (
                 sys.argv[0], 'openTorrent', link_url)),
            ]
            title = self.titleMake(seeds, leechers, size, title)

            if self.open_option==0:
                self.drawItem(title, 'openTorrent', link_dict, image, contextMenu=contextMenu, replaceMenu=False)
            elif self.open_option==1:
                self.drawItem(title, 'context', link, image, contextMenu=contextMenu, replaceMenu=False)
            elif self.open_option==2:
                self.drawItem(title, 'downloadFilesList', link_dict, image, contextMenu=contextMenu, replaceMenu=False)
            elif self.open_option==3:
                self.drawItem(title, 'downloadLibtorrent', link_dict, image, contextMenu=contextMenu, replaceMenu=False)

        view_style('showFilesList')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def showFilesListExternal(self, filesList, params={}):
        get = params.get
        silent = get("silent")
        thumbnail = unquote(get("thumbnail"),'')
        save_folder = unquote(get("save_folder"),'')
        back_url = unquote(get("back_url"),'')
        return_url = unquote(get("return_url"),'')
        return_name = unquote(get("return_name"),'')
        sdata = unquote(get("sdata"),'{}')

        try:
        #if 1==1:
            try:
                sdata = json.loads(sdata)
            except:
                sdata = json.loads(urllib.unquote_plus(sdata))
            if len(filesList) < 1:
                xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)
                if not silent:
                    xbmc.executebuiltin(
                        'XBMC.ActivateWindow(%s)' % 'Videos,%s' % return_url)
                else:
                    showMessage(self.localize('Information'), self.localize('Torrent list is empty.'))
                return
            if silent:
                order, seeds, leechers, size, title, link, image = filesList[0]
                sdata['filename'] = link
                xbmc.executebuiltin('XBMC.RunPlugin(%s)' % (
                back_url+'silent&stringdata=' + urllib.quote_plus(
                    json.dumps(sdata))))
                return
            else:
                for order, seeds, leechers, size, title, link, image in filesList:
                    link_dict = {'url': link, 'thumbnail': thumbnail, 'save_folder':save_folder}
                    link_url=''
                    for key in link_dict.keys():
                        if link_dict.get(key):
                            link_url = '%s&%s=%s' % (link_url, key, urllib.quote_plus(link_dict.get(key)))
                    sdata['filename'] = link
                    contextMenu = [
                        (self.localize('Add to %s') % return_name,
                         'XBMC.RunPlugin(%s)' % (back_url+'&stringdata=' + urllib.quote_plus(
                             json.dumps(sdata)))),
                        (self.localize('Open'),
                         'XBMC.Container.Update(%s)' % ('%s?action=%s%s') % (
                         sys.argv[0], 'openTorrent', link_url)),
                        (self.localize('Return to %s') % return_name,
                         'XBMC.ActivateWindow(%s)' % ('Videos,%s' % return_url)),
                    ]
                    title = self.titleMake(seeds, leechers, size, title)
                    self.drawItem(title, 'context', link, image, contextMenu=contextMenu)
        except:
            showMessage(self.localize('Information'), self.localize('Torrent list is empty.'))
            if not silent: xbmc.executebuiltin('XBMC.RunPlugin(%s)' % return_url)
            return

        view_style('showFilesList')
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    def context(self, params={}):
        if not self.version_check():
            xbmc.executebuiltin("Action(ContextMenu)")
            sys.exit()
        else:
            fixed = xbmcgui.Dialog().contextmenu(list=[(self.localize('Open')),
                                                    (self.localize('Download via Libtorrent')),
                                                    (self.localize('Download via T-client'))])
            if fixed == 0:
                xbmc.executebuiltin('XBMC.Container.Update(%s)' %
                                    ('%s?action=%s&url=%s') %
                                    (sys.argv[0], 'openTorrent', params['url']))
            elif fixed == 1:
                xbmc.executebuiltin('XBMC.RunPlugin(%s)' %
                                    ('%s?action=%s&url=%s') %
                                    (sys.argv[0], 'downloadLibtorrent', params['url']))
            elif fixed == 2:
                xbmc.executebuiltin('XBMC.RunPlugin(%s)' %
                                    ('%s?action=%s&url=%s') %
                                    (sys.argv[0], 'downloadFilesList', params['url']))

    def version_check(self):
        return False if int(xbmc.getInfoLabel( "System.BuildVersion" )[:2]) < 17 else True

    def downloadFilesList(self, params={}):
        from resources.utorrent.net import Download
        dirname = None
        dat = Download().listdirs()
        if dat == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
            return
        items, clean = dat

        if self.__settings__.getSetting("torrent_save") == '0':
            if items and clean:
                if self.__settings__.getSetting("torrent") in ['0','3']:
                    if len(items) > 1:
                        dialog = xbmcgui.Dialog()
                        dirid = dialog.select(self.localize('Choose directory:'), items)
                    else:
                        dirid = 0
                    if dirid == -1: return
                    dirname = clean[dirid]
            if self.__settings__.getSetting("torrent") in ['1','2','4']:
                default = self.__settings__.getSetting("torrent_dir")
                keyboard = xbmc.Keyboard(default, self.localize('Save to path') + ':')
                keyboard.doModal()
                dirname = keyboard.getText()
                if not keyboard.isConfirmed():
                    return
                if dirname in ['',None,0] and len(clean)>0:
                    dirname = clean[0]
        else:
            dirname = self.__settings__.getSetting("torrent_dir")

        if dirname=='':
            log('[downloadFilesList] dirname: \'\'')
        else:
            log('[downloadFilesList] dirname:'+str(dirname))

        get = params.get
        url = unquote(get("url"), self.__settings__.getSetting("lastTorrent").decode('utf-8'))
        ind = get("ind")
        if not ind:
            self.__settings__.setSetting("lastTorrentUrl", url)
            classMatch = re.search('(\w+)::(.+)', url)
            if classMatch:
                debug('[downloadFilesList] classMatch:'+str(classMatch.group(1))+' '+str(classMatch.group(2)))
                if re.match("^magnet\:.+$", classMatch.group(2)) and dirname:
                    url=classMatch.group(2)
                else:
                    searcher = classMatch.group(1)
                    url = Searchers().downloadWithSearcher(classMatch.group(2), searcher)

        torrent = Downloader.Torrent(self.userStorageDirectory,
                                     torrentFilesDirectory=self.torrentFilesDirectory)

        if re.match("^magnet\:.+$", url):
            if dirname in [None,0]:
                torrent.magnetToTorrent(url)
                url = torrent.torrentFile
            else:
                success = Download().add_url(url, dirname)
                if success:
                    showMessage(self.localize('Torrent-client Browser'), self.localize('Added!'), forced=True)
                return
        else:
            url = torrent.saveTorrent(url)

        if url:
            f = open(url, 'rb')
            torrent = f.read()
            f.close()
            try:
                from python_libtorrent import get_libtorrent
                libtorrent = get_libtorrent()
                info = libtorrent.torrent_info(libtorrent.bdecode(torrent))
                name = info.name()
            except:
                log('get_libtorrent import error, name = None')
                name = None
            success = Download().add(torrent, dirname)
            if success:
                showMessage(self.localize('Torrent-client Browser'), self.localize('Added!'), forced=True)
                if ind:
                    id = self.chooseHASH(Download().list(), name)[0]
                    Download().setprio(id, ind)

    def downloadLibtorrent(self, params={}):
        import SkorbaLoader
        get = params.get
        storage=get('storage')
        if not storage: self.userStorage(params)
        else: self.userStorageDirectory=urllib.unquote_plus(storage)
        try:
            url = urllib.unquote_plus(get("url"))
        except:
            url = self.__settings__.getSetting("lastTorrent").decode('utf-8')
        ind = get("ind")
        if not ind:
            self.__settings__.setSetting("lastTorrentUrl", url)
            classMatch = re.search('(\w+)::(.+)', url)
            if classMatch:
                searcher = classMatch.group(1)
                url = Searchers().downloadWithSearcher(classMatch.group(2), searcher)
        torrent = SkorbaLoader.SkorbaLoader(self.userStorageDirectory, torrentFilesDirectory=self.torrentFilesDirectory)
        torrent.initSession()
        encryption = self.__settings__.getSetting('encryption') == 'true'
        if encryption:
            torrent.encryptSession()
        url=torrent.saveTorrent(url)
        self.__settings__.setSetting("lastTorrent", url)
        if 0 < int(self.__settings__.getSetting("upload_limit")):
            torrent.setUploadLimit(int(self.__settings__.getSetting("upload_limit")) * 1000000 / 8)  #MBits/second
        if 0 < int(self.__settings__.getSetting("download_limit")):
            torrent.setDownloadLimit(
                int(self.__settings__.getSetting("download_limit")) * 1000000 / 8)  #MBits/second
        torrent.downloadProcess(ind, encryption)
        showMessage(self.localize('Download Status'), self.localize('Added!'))

    def titleMake(self, seeds, leechers, size, title):

        #AARRGGBB
        clGreen = '[COLOR FF008000]%s[/COLOR]'
        clDodgerblue = '[COLOR FF1E90FF]%s[/COLOR]'
        clDimgray = '[COLOR FF696969]%s[/COLOR]'
        clWhite = '[COLOR FFFFFFFF]%s[/COLOR]'
        clAliceblue = '[COLOR FFF0F8FF]%s[/COLOR]'
        clRed = '[COLOR FFFF0000]%s[/COLOR]'

        title = title.replace('720p', '[B]720p[/B]').replace('1080p', '[B]1080p[/B]')

        if self.torrent_info_style == 0:
            title = clWhite % title
            second = '[I](%s) [S/L: %d/%d] [/I]' % (size, seeds, leechers)
            title += '  ' + second
        elif self.torrent_info_style == 1:
            title = clWhite % title
            second = '[I](%s) [S/L: %d/%d] [/I]' % (size, seeds, leechers)
            title = second + '  ' + title
        elif self.torrent_info_style == 2:
            title = clWhite % title
            second = '[I](%s) [S/L: %d/%d] [/I]' % (size, seeds, leechers)
            title += '\r\n' + clDimgray % second

        return title

    def search(self, params={}):
        if len(Searchers().get_active())<1:
            noActiveSerachers()
            return

        defaultKeyword = params.get('url')
        showKey=params.get('showKey')
        external = unquote(params.get("external"), None)
        if external and not params.get('from_searcher'):
            searcher = '[%s] ' % str(external)
        else:
            searcher = ''

        if showKey == "true" or defaultKeyword == '' or not defaultKeyword:
            if not defaultKeyword:
                defaultKeyword = ''
            defaultKeyword=unquote(defaultKeyword)
            keyboard = xbmc.Keyboard(defaultKeyword, '%s%s:' % (searcher, self.localize('Search Phrase')))
            keyboard.doModal()
            query = keyboard.getText()
            if not query:
                return
            elif keyboard.isConfirmed():
                params["url"] = urllib.quote_plus(query)
                self.openSection(params)
        else:
            self.openSection(params)

    def chooseHASH(self, list, name = None):
        dialog_items, dialog_items_clean = [], []
        dialog_files = []
        dat = list
        if dat == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
            return
        for data in dat:
            dialog_files.append((data['id'], data['dir'].encode('utf-8')))
            dialog_items.append('[' + str(data['progress']) + '%] ' + data['name'])
            dialog_items_clean.append(data['name'])

        log('[chooseHASH]: name %s ' % str(name))
        for data in dat:
            # Debug('[chooseHASH]: '+str((data['name'], data['id'], data['dir'].encode('utf-8'))))
            dialog_files.append((data['id'], data['dir'].encode('utf-8')))
            dialog_items.append('[' + str(data['progress']) + '%] ' + data['name'])
            dialog_items_clean.append(data['name'])

        if name:
            if decode_str(name) in dialog_items_clean:
                return dialog_files[dialog_items_clean.index(decode_str(name))]
            elif name in dialog_items_clean:
                return dialog_files[dialog_items_clean.index(name)]
        else:
            if len(dialog_items) > 1:
                ret = xbmcgui.Dialog().select(self.localize('Choose in torrent-client:'), dialog_items)
                if ret > -1 and ret < len(dialog_files):
                    hash = dialog_files[ret]
                    return hash
            elif len(dialog_items) == 1:
                hash = dialog_files[0]
                return hash

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string

    def returnRussian(self, params={}):
        i=delete_russian(ok=True, action='return')
        showMessage(self.localize('Return Russian stuff'),self.localize('%d files have been returned')%i)

    def callback(self, params={}):
        get = params.get

        subaction = unquote(get("subaction"), None)
        url = unquote(get("url"),'')
        sdata = unquote(get("sdata"),'{}')
        back_url = unquote(get("back_url"),'')

        try:
            sdata = json.loads(sdata)
        except:
            sdata = json.loads(urllib.unquote_plus(sdata))

        self.__settings__.setSetting("lastTorrentUrl", url)

        classMatch = re.search('(\w+)::(.+)', url)
        if classMatch:
            searcher = classMatch.group(1)
            url = Searchers().downloadWithSearcher(classMatch.group(2), searcher)


        torrent = Downloader.Torrent(self.userStorageDirectory, torrentFilesDirectory=self.torrentFilesDirectory)
        if not torrent: torrent = Downloader.Torrent(self.userStorageDirectory,
                                                     torrentFilesDirectory=self.torrentFilesDirectory)
        torrentFile =  torrent.saveTorrent(url)
        if torrentFile: url = torrentFile
        self.__settings__.setSetting("lastTorrent", url)

        if subaction == 'download':
            if re.match("^http.+$", url):
                torrentFile = self.saveUrlTorrent(url)
                if torrentFile: url = torrentFile
                self.__settings__.setSetting("lastTorrent", url)

        elif subaction == 'play':
            fileIndex = chooseFile(torrent.getContentList())
            if fileIndex:
                xbmc.executebuiltin('xbmc.RunPlugin("plugin://plugin.video.torrenter/?action=playTorrent&url=' + fileIndex + '")')
                return

        sdata['filename'] = ensure_str(url)
        #log('[call]: '+sdata['filename']+json.loads(json.dumps(sdata))['filename'])
        xbmc.executebuiltin('xbmc.RunPlugin(%s&stringdata=%s)' % (back_url, urllib.quote_plus(json.dumps(sdata))))
