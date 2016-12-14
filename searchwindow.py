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
import pyxbmct.addonwindow as pyxbmct
import xbmcaddon
import xbmcgui
import xbmcvfs

from functions import *

__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__language__ = __settings__.getLocalizedString
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__
__root__ = __settings__.getAddonInfo('path')

log('SYS ARGV: ' + str(sys.argv))

# https://github.com/xbmc/xbmc/blob/8d4a5bba55638dfd0bdc5e7de34f3e5293f99933/xbmc/input/Key.h
ACTION_STOP = 13
ACTION_PLAYER_PLAY = 79
ACTION_MOUSE_RIGHT_CLICK = 101
ACTION_CONTEXT_MENU = 117
ACTION_SHOW_OSD = 24


class SearchWindow(pyxbmct.AddonDialogWindow):
    __settings__ = sys.modules["__main__"].__settings__
    fileList = []
    contentList = []
    searchersList = []
    addtime = None
    right_buttons_count = 7
    last_right_buttons_count = 0
    last_link = None
    last_query = None
    last_top_button = None
    last_right_button = None
    last_listing_mode = None
    count = 0
    navi = {
        'last_top_button'   : 4,
        'last_right_button' : 1,
        'right_menu'        : [],
        'top_menu'          : [],
        'route':[{'mode':'close', 'params':{}, 'last_listing_item': 0}]
    }

    icon = __root__ + '/icons/searchwindow/%s.png'
    icon_tc = __root__ + '/icons/searchwindow/%s' + getTorrentClientIcon()

    def __init__(self, params = None):
        super(SearchWindow, self).__init__(self.localize('Torrenter Search Window'))
        self.setGeometry(1280, 720, 9, 16)
        self.set_controls()
        self.connect_controls()
        if params:
            self.search(params)
        else:
            self.history()

        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.input_search)

    def set_controls(self):
        if not __settings__.getSetting('debug') == 'true':
            self.background.setImage('%s/icons/%s.png' % (__root__, 'ContentPanel'))

        #self.background.setImage('%s/icons/%s.png' % (__root__, 'ContentPanel'))

        # Top menu
        self.button_downloadstatus = pyxbmct.Button("",
                                                    focusTexture=self.icon % 'fdownloadstatus',
                                                    noFocusTexture=self.icon % 'nfdownloadstatus')
        self.placeControl(self.button_downloadstatus, 0, 1, 1, 1)

        self.button_torrentclient = pyxbmct.Button("",
                                                   focusTexture=self.icon_tc % 'f',
                                                   noFocusTexture=self.icon_tc % 'nf')
        self.placeControl(self.button_torrentclient, 0, 2, 1, 1)
        self.button_keyboard = pyxbmct.Button("", focusTexture=self.icon % 'fkeyboard',
                                              noFocusTexture=self.icon % 'nfkeyboard')
        self.placeControl(self.button_keyboard, 0, 3, 1, 1)
        self.input_search = pyxbmct.Edit("", _alignment=pyxbmct.ALIGN_CENTER_X | pyxbmct.ALIGN_CENTER_Y)
        self.placeControl(self.input_search, 0, 4, 1, 5)
        self.button_search = pyxbmct.Button("", focusTexture=self.icon % 'fsearch',
                                            noFocusTexture=self.icon % 'nfsearch')
        self.placeControl(self.button_search, 0, 9, 1, 1)
        self.button_history = pyxbmct.Button("", focusTexture=self.icon % 'fhistory',
                                             noFocusTexture=self.icon % 'nfhistory')
        self.placeControl(self.button_history, 0, 10, 1, 1)
        self.button_watched = pyxbmct.Button("", focusTexture=self.icon % 'fwatched',
                                             noFocusTexture=self.icon % 'nfwatched')
        self.placeControl(self.button_watched, 0, 11, 1, 1)
        self.button_controlcenter = pyxbmct.Button("", focusTexture=self.icon % 'fcontrolcenter',
                                                   noFocusTexture=self.icon % 'nfcontrolcenter')
        self.placeControl(self.button_controlcenter, 0, 12, 1, 1)

        # Main
        self.listing = pyxbmct.List(_imageWidth=60, _imageHeight=60, _itemTextXOffset=1,
                                    _itemTextYOffset=0, _itemHeight=60, _space=0, _alignmentY=4)
        self.placeControl(self.listing, 1, 0, 8, 14)

        self.navi['top_menu'] = [self.button_downloadstatus, self.button_torrentclient, self.button_keyboard,
                                 self.input_search, self.button_search, self.button_history, self.button_watched,
                                 self.button_controlcenter]

        # Right menu
        self.right_menu()

    def connect_controls(self):
        self.connect(self.listing, self.right_press1)
        self.connect(self.button_history, self.history)
        self.connect(self.button_search, self.search)
        self.connect(self.button_controlcenter, self.controlCenter)
        self.connect(self.button_torrentclient, self.browser)
        self.connect(self.button_downloadstatus, self.downloadstatus)
        self.connect(self.button_watched, self.watched)

        self.connect(pyxbmct.ACTION_NAV_BACK, self.navi_back)
        self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.navi_back)

        self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.close)
        self.connect(ACTION_MOUSE_RIGHT_CLICK, self.context)
        self.connect(ACTION_CONTEXT_MENU, self.context)
        self.connect(ACTION_SHOW_OSD, self.context)

        self.connect(pyxbmct.ACTION_MOVE_LEFT, self.navi_update)
        self.connect(pyxbmct.ACTION_MOVE_RIGHT, self.navi_update)
        self.connect(pyxbmct.ACTION_MOVE_UP, self.navi_update)
        self.connect(pyxbmct.ACTION_MOVE_DOWN, self.navi_update)

    def set_navigation(self):
        # Top menu
        self.button_torrentclient.setNavigation(self.listing, self.listing, self.button_downloadstatus,
                                                self.button_keyboard)
        self.button_keyboard.setNavigation(self.listing, self.listing, self.button_torrentclient, self.input_search)
        self.input_search.setNavigation(self.listing, self.listing, self.button_keyboard, self.button_search)
        self.button_search.setNavigation(self.listing, self.listing, self.input_search, self.button_history)
        self.button_history.setNavigation(self.listing, self.listing, self.button_search, self.button_watched)
        self.button_watched.setNavigation(self.listing, self.listing, self.button_history, self.button_controlcenter)

        self.update_navigation()

    def update_navigation(self):
        self.last_top_button = self.navi['top_menu'][self.navi['last_top_button'] - 1]
        self.last_right_button = self.navi['right_menu'][self.navi['last_right_button'] - 1]

        # Top menu
        self.button_downloadstatus.setNavigation(self.listing, self.listing, self.last_right_button,
                                                 self.button_torrentclient)
        self.button_controlcenter.setNavigation(self.listing, self.listing, self.button_watched, self.last_right_button)

        # Main
        self.listing.setNavigation(self.last_top_button, self.input_search, self.button_downloadstatus,
                                   self.last_right_button)

    def setAnimation(self, control):
        # Set fade animation for all add-on window controls
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
                               ('WindowClose', 'effect=fade start=100 end=0 time=500',)])

    def navi_back(self):
        log('navi_back init')
        self.navi['route'].pop(-1)
        route = self.navi['route'][-1]
        action = getattr(self, route['mode'])
        if route['params']:
            action(route['params'])
        else:
            action()
        self.setFocus(self.listing)
        log('route[last_listing_item]: '+str(route['last_listing_item']))
        if route['last_listing_item'] > 0:
            self.listing.selectItem(route['last_listing_item'])

    def navi_update(self):
        log('navi_update init')
        focused_control = self.getFocus()
        debug('start navi_update' + str(focused_control))
        log(str(self.navi['route']))

        if focused_control == self.listing:
            item_index = self.listing.getSelectedPosition()
            self.navi['route'][-1]['last_listing_item'] = item_index
            debug('self.listing getSelectedPosition ' + str(item_index))

            item = self.listing.getSelectedItem()
            params = json.loads(item.getfilename())
            mode = params.get('mode')
            log('navi_update:' + str(mode))
            if self.last_listing_mode != mode:
                self.last_listing_mode = mode
                debug('set_menulist navi_update:' + str(mode))
                self.set_menulist(mode)

        elif self.getFocus() in self.navi['top_menu']:
            self.navi['last_top_button'] = self.navi['top_menu'].index(focused_control) + 1
            self.update_navigation()

        elif self.getFocus() in self.navi['right_menu']:
            self.navi['last_right_button'] = self.navi['right_menu'].index(focused_control) + 1
            self.update_navigation()

    def navi_route(self, mode, params = None, last_listing_item = 0):
        self.navi['route'].append({'mode': mode,
                                   'params': {} if not params else params,
                                   'last_listing_item': last_listing_item})
        self.right_menu(mode)
        self.listing.reset()

    def search(self, params = None):
        self.navi_route('search', params)

        get = params.get
        addtime = get('addtime')
        query = None

        if params:
            if get('url'):
                search = urllib.unquote_plus(get('url'))
                external = get("return_name")
                if external:
                    searcher = 'landing from : %s ' % str(external)
                else:
                    searcher = ''
                self.setWindowTitle(title='%s %s' % ('Torrenter Search Window', searcher))
                if get('showKey') == 'true':
                    self.input_search.setText(search)
                    self.setFocus(self.input_search)
                    return
                else:
                    self.input_search.setText(search)
                    query = search
                    # self.setFocus(self.listing)
            else:
                query = self.input_search.getText()
        log('Search query: ' + str(query))

        if not addtime and query == self.last_query:
            addtime = self.addtime

        searchersList = get_searchersList(addtime)

        # cache
        if (query != self.last_query or self.searchersList != searchersList) and len(query) > 0:
            self.filesList = get_filesList(query, searchersList, addtime)
            self.addtime = addtime
            self.searchersList = searchersList
            self.last_query = query
        elif len(query) == 0:
            self.filesList = []
        if 1 == 1:
            if self.filesList:
                for (order, seeds, leechers, size, title, link, image) in self.filesList:
                    title = titleMake(seeds, leechers, size, title)
                    self.drawItem(title, {'mode': 'search_item', 'filename': link}, image)
                self.setFocus(self.listing)

    def history(self, params = None):
        self.navi_route('history')

        db = HistoryDB()
        items = db.get_all()
        favlist = [(1, '[B]%s[/B]'), (0, '%s')]
        if items:
            for favbool, bbstring in favlist:
                for addtime, string, fav in items:
                    if favbool == int(fav):
                        title = string.encode('utf-8')

                        if int(fav) == 1:
                            img = __root__ + '/icons/fav.png'
                        else:
                            img = __root__ + '/icons/unfav.png'

                        link = {'mode': 'history_search_item', 'filename': title, 'addtime': str(addtime),
                                'fav': str(fav)}
                        self.drawItem(bbstring % title, link, img)

    def history_action(self, action, addtime, fav):
        db = HistoryDB()

        if action == 'delete':
            db.delete(addtime)
            showMessage(self.localize('Search History'), self.localize('Deleted!'))

        if action == 'fav' and fav == '0':
            db.fav(addtime)
            showMessage(self.localize('Favourites'), self.localize('Added!'))
        elif action == 'fav':
            db.unfav(addtime)
            showMessage(self.localize('Favourites'), self.localize('Deleted!'))

        self.history()

    def watched(self):
        self.right_menu('watched')
        self.listing.reset()

        db = WatchedHistoryDB()

        items = db.get_all()
        log('[WatchedHistory]: items - '+str(items))
        if items:
            for addtime, filename, foldername, path, url, seek, length, ind, size in items:
                seek = int(seek) if int(seek) > 3*60 else 0
                watchedPercent = int((float(seek) / float(length)) * 100)
                duration = '%02d:%02d:%02d' % ((length / (60*60)), (length / 60) % 60, length % 60)
                title = '[%d%%][%s] %s [%d MB]' %\
                        (watchedPercent, duration, filename.encode('utf-8'), int(size))
                clDimgray = '[COLOR FF696969]%s[/COLOR]'
                clWhite = '[COLOR FFFFFFFF]%s[/COLOR]'

                title = clWhite % title + chr(10) + clDimgray % '(%s)' % foldername.encode('utf-8')

                if watchedPercent >= 85:
                    img = __root__ + '/icons/stop-icon.png'
                else:
                    img = __root__ + '/icons/pause-icon.png'


                link = {'mode': 'watched_item', 'addtime': str(addtime)}
                self.drawItem(title, link, image=img)

    def watched_action(self, action, addtime):
        db = WatchedHistoryDB()

        if action == 'delete':
            db.delete(addtime)
            showMessage(self.localize('Watched History'), self.localize('Deleted!'))
            self.watched()

        if action == 'open':
            filename, foldername, path, url, seek, length, ind = db.get('filename, foldername, path, url, seek, length, ind', 'addtime', str(addtime))
            #self.reconnect(pyxbmct.ACTION_NAV_BACK, self.watched)
            self.open_torrent(path.encode('utf-8'))

        if action == 'playnoseek' or action == 'playwithseek':
            filename, path, url, seek, length, ind = db.get('filename, path, url, seek, length, ind', 'addtime', str(addtime))

            if action == 'playwithseek':
                seek = int(seek)
            else:
                seek = 0

            if os.path.exists(path):
                __settings__.setSetting("lastTorrent", path)
            else:
                from Downloader import Downloader
                torrent = Downloader.Torrent(self.userStorageDirectory, torrentFilesDirectory=self.torrentFilesDirectory)
                __settings__.setSetting("lastTorrent", torrent.saveTorrent(url))
            xbmc.executebuiltin('xbmc.RunPlugin("plugin://plugin.video.torrenter/?action=playTorrent&url='+str(ind)+'&seek='+str(seek)+'")')
            self.close()

        if action == 'clear':
            db.clear()
            showMessage(self.localize('Watched History'), self.localize('Clear!'))
            self.watched()

    def browser(self, hash = None, tdir = None):
        from resources.utorrent.net import Download
        self.listing.reset()
        menu, dirs = [], []

        DownloadList = Download().list()
        if DownloadList == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
            return

        if not hash:
            self.right_menu('browser')
            #self.reconnect(pyxbmct.ACTION_NAV_BACK, self.history)
            for data in DownloadList:
                status = " "
                img = ''
                if data['status'] in ('seed_pending', 'stopped'):
                    status = TextBB(' [||] ', 'b')
                elif data['status'] in ('seeding', 'downloading'):
                    status = TextBB(' [>] ', 'b')
                if data['status'] == 'seed_pending':
                    img = os.path.join(__root__, 'icons', 'pause-icon.png')
                elif data['status'] == 'stopped':
                    img = os.path.join(__root__, 'icons', 'stop-icon.png')
                elif data['status'] == 'seeding':
                    img = os.path.join(__root__, 'icons', 'upload-icon.png')
                elif data['status'] == 'downloading':
                    img = os.path.join(__root__, 'icons', 'download-icon.png')

                title = '[%s%%]%s%s [%s]' % (str(data['progress']), status, data['name'], str(data['ratio']))
                # title = '[' + str(data['progress']) + '%]' + status + data['name'] + ' [' + str(data['ratio']) + ']'
                menu.append(
                    {"title": title, "image": img, "argv": {'mode': 'browser_item', 'hash': str(data['id'])}})
        elif not tdir:
            self.right_menu('browser_subfolder')
            #self.reconnect(pyxbmct.ACTION_NAV_BACK, self.browser)
            self.drawItem('..', {'mode': 'browser_moveup'}, isFolder=True)
            dllist = sorted(Download().listfiles(hash), key=lambda x: x[0])
            for name, percent, ind, size in dllist:
                if '/' not in name:
                    title = '[%s%%][%s]%s' % (str(percent), str(size), name)
                    menu.append({"title": title, "image": '',
                                 "argv": {'mode': 'browser_file', 'hash': hash, 'ind': str(ind)}})
                else:
                    newtdir = name.split('/')[0]
                    if newtdir not in dirs: dirs.append(newtdir)
        elif tdir:
            self.right_menu('browser_subfolder')
            tdir_up = tdir[:len(tdir)-len(tdir.split('/')[-1])-1] if '/' in tdir else None
            self.drawItem('..', {'mode': 'browser_subfolder', 'hash': hash, 'tdir': tdir_up}, isFolder=True)
            dllist = sorted(Download().listfiles(hash), key=lambda x: x[0])
            for name, percent, ind, size in dllist:

                if name[:len(tdir)] == tdir:
                    name = name[len(tdir) + 1:]
                    if '/' not in name:
                        title = '[%s%%][%s]%s' % (str(percent), str(size), name)
                        menu.append({"title": title, "image": '',
                                     "argv": {'mode': 'browser_file', 'hash': hash, 'ind': str(ind)}})
                    else:
                        newtdir = tdir+'/'+name.split('/')[0]
                        if newtdir not in dirs: dirs.append(newtdir)

        for tdir in dirs:
            params = {'mode': 'browser_subfolder', 'hash': hash, 'tdir': tdir}
            title = tdir.split('/')[-1] if '/' in tdir else tdir
            self.drawItem(title, params, isFolder = True)

        for i in menu:
            params = i['argv']
            img = i['image']
            popup = []
            if not hash:
                folder = True
            else:
                folder = False

            self.drawItem(i['title'], params, image = img, isFolder = folder)
            # def drawItem(self, title, params, image = None, isFolder = False):
        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.button_torrentclient)
        return

    def browser_action(self, hash, action, tdir = None, ind = None):
        from resources.utorrent.net import Download
        menu = []

        DownloadList = Download().list()
        if DownloadList == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
            return

        if (ind or ind == 0) and action in ('0', '3'):
            Download().setprio_simple(hash, action, ind)
        elif action in ['play', 'copy']:
            p, dllist, i, folder, filename = DownloadList, Download().listfiles(hash), 0, None, None
            for data in p:
                if data['id'] == hash:
                    folder = data['dir']
                    break
            if isRemoteTorr():
                torrent_dir = __settings__.getSetting("torrent_dir")
                torrent_replacement = __settings__.getSetting("torrent_replacement")
                empty = [None, '']
                if torrent_dir in empty or torrent_replacement in empty:
                    if xbmcgui.Dialog().yesno(
                            self.localize('Remote Torrent-client'),
                            self.localize('You didn\'t set up replacement path in setting.'),
                            self.localize('For example /media/dl_torr/ to smb://SERVER/dl_torr/. Setup now?')):
                        if torrent_dir in empty:
                            torrent_dir()
                        __settings__.openSettings()
                    return

                folder = folder.replace(torrent_dir, torrent_replacement)
            if (ind or ind == 0) and action == 'play':
                for data in dllist:
                    if data[2] == int(ind):
                        filename = data[0]
                        break
                filename = os.path.join(folder, filename)
                xbmc.executebuiltin('xbmc.PlayMedia("' + filename.encode('utf-8') + '")')
            elif tdir and action == 'copy':
                path = os.path.join(folder, tdir)
                dirs, files = xbmcvfs.listdir(path)
                if len(dirs) > 0:
                    dirs.insert(0, self.localize('./ (Root folder)'))
                    for dd in dirs:
                        dd = file_decode(dd)
                        dds = xbmcvfs.listdir(os.path.join(path, dd))[0]
                        if len(dds) > 0:
                            for d in dds:
                                dirs.append(dd + os.sep + d)
                    ret = xbmcgui.Dialog().select(self.localize('Choose directory:'), dirs)
                    if ret > 0:
                        path = os.path.join(path, dirs[ret])
                        dirs, files = xbmcvfs.listdir(path)
                for file in files:
                    if not xbmcvfs.exists(os.path.join(path, file)):
                        xbmcvfs.delete(os.path.join(path, file))
                    xbmcvfs.copy(os.path.join(path, file), os.path.join(folder, file))
                    i = i + 1
                showMessage(self.localize('Torrent-client Browser'), self.localize('Copied %d files!') % i, forced=True)
            return
        elif not tdir and action not in ('0', '3'):
            if action == 'removedata':
                ok = xbmcgui.Dialog().yesno(self.localize('Torrent-client Browser'),
                                            self.localize('Delete torrent with files?'))
                if not ok: sys.exit(1)
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
        return

    def downloadstatus(self):
        self.listing.reset()
        self.right_menu('downloadstatus')
        #self.reconnect(pyxbmct.ACTION_NAV_BACK, self.history)

        db = DownloadDB()
        items = db.get_all()

        if items:
            for addtime, title, path, type, info, status, torrent, ind, lastupdate, storage in items:
                jsoninfo = json.loads(urllib.unquote_plus(info))

                if status != 'stopped' and int(lastupdate) < int(time.time()) - 10:
                    status = 'stopped'
                    db.update_status(addtime, status)

                progress = int(jsoninfo.get('progress'))
                if status == 'pause':
                    status_sign = '[||]'
                    img = os.path.join(__root__, 'icons', 'pause-icon.png')
                elif status == 'stopped':
                    status_sign = '[X]'
                    img = os.path.join(__root__, 'icons', 'stop-icon.png')
                else:
                    status_sign = '[>]'
                    if progress == 100:
                        img = os.path.join(__root__, 'icons', 'upload-icon.png')
                    else:
                        img = os.path.join(__root__, 'icons', 'download-icon.png')

                title = '[%d%%]%s %s' % (progress, status_sign, title)
                if jsoninfo.get('seeds') != None and jsoninfo.get('peers') != None and \
                                jsoninfo.get('download') != None and jsoninfo.get('upload') != None:
                    d, u = float(jsoninfo['download']) / 1000000, float(jsoninfo['upload']) / 1000000
                    s, p = str(jsoninfo['seeds']), str(jsoninfo['peers'])
                    second = '[D/U %.2f/%.2f (MB/s)][S/L %s/%s]' % (d, u, s, p)
                    title = dlstat_titleMake('[B]%s[/B]' % title if type == 'folder' else title, second)

                params = {'addtime': addtime, 'type': type, 'path': path,
                          'status': status, 'progress': progress, 'storage': storage}
                params['mode'] = 'downloadstatus_subfolder' if type == 'folder' else 'downloadstatus_file'

                self.drawItem(title, params, image=img, isFolder=type == 'folder')

            # def drawItem(self, title, params, image = None, isFolder = False):
        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.button_downloadstatus)
        return

    def downloadstatus_action(self, action, addtime, path, type, progress, storage):

        db = DownloadDB()

        if action == 'play':
            if type == 'file' and progress > 30 or progress == 100:
                self.file_browser(type, path, path)
            else:
                showMessage(self.localize('Download Status'), self.localize('Download has not finished yet'))

        elif action == 'delete':
            db.delete(addtime)
            showMessage(self.localize('Download Status'), self.localize('Stopped and Deleted!'))

        elif action == 'pause':
            db.update_status(addtime, 'pause')
            showMessage(self.localize('Download Status'), self.localize('Paused!'))

        elif action == 'stop':
            db.update_status(addtime, 'stopped')
            showMessage(self.localize('Download Status'), self.localize('Stopped!'))

        elif action == 'start':
            start = db.get_byaddtime(addtime)
            if start[5] == 'pause':
                db.update_status(addtime, 'downloading')
                showMessage(self.localize('Download Status'), self.localize('Unpaused!'))
            else:
                torrent, ind = start[6], start[7]

                del db

                import SkorbaLoader
                __settings__.setSetting("lastTorrent", torrent.encode('utf-8'))
                torrent = SkorbaLoader.SkorbaLoader(storage.encode('utf-8'), torrent)
                encryption = __settings__.getSetting('encryption') == 'true'
                torrent.downloadProcess(ind, encryption)
                showMessage(self.localize('Download Status'), self.localize('Started!'))
                xbmc.sleep(1000)

        elif action == 'masscontrol':
            dialog_items = [self.localize('Start All'), self.localize('Stop All'),
                            self.localize('Clear %s') % self.localize('Download Status'), self.localize('Cancel')]
            ret = xbmcgui.Dialog().select(self.localize('Mass Control'), dialog_items)
            if ret == 0:
                items = db.get_all()
                del db
                if items:
                    import SkorbaLoader
                    for addtime, title, path, type, info, status, torrent, ind, lastupdate, storage in items:
                        __settings__.setSetting("lastTorrent", torrent.encode('utf-8'))
                        torrent = SkorbaLoader.SkorbaLoader(storage.encode('utf-8'), torrent)
                        encryption = __settings__.getSetting('encryption') == 'true'
                        torrent.downloadProcess(ind, encryption)
                        xbmc.sleep(1000)

                    xbmc.sleep(2000)
                    showMessage(self.localize('Download Status'), self.localize('Started All!'))
            elif ret == 1:
                items = db.get_all()
                if items:
                    for addtime, title, path, type, info, status, torrent, ind, lastupdate, storage in items:
                        db.update_status(addtime, 'stopped')
                        xbmc.sleep(1000)
                    showMessage(self.localize('Download Status'), self.localize('Stopped All!'))
            elif ret == 2:
                db.clear()
                showMessage(self.localize('Download Status'), self.localize('Clear!'))

        xbmc.sleep(1000)
        self.downloadstatus()

    def file_browser(self, mode, path, tdir):

        path = encode_msg(path)
        tdir = encode_msg(tdir)

        self.listing.reset()
        if tdir == os.path.dirname(path):
            self.downloadstatus()
        elif mode == 'file':
            xbmc.Player().play(localize_path(tdir))
            self.close()
        else:
            self.right_menu('file_browser')
            #self.reconnect(pyxbmct.ACTION_NAV_BACK, self.downloadstatus)

            self.drawItem('..', {'mode': 'moveup', 'path': path,
                                 'tdir': os.path.dirname(tdir)}, isFolder=True)

            dirs, files = xbmcvfs.listdir(tdir + os.sep)
            if len(dirs) > 0:
                for dir in dirs:
                    link = {'mode': 'subfolder', 'path': path, 'type': 'folder',
                            'tdir': os.path.join(tdir, dir)}
                    self.drawItem(dir, link, isFolder=True)
            for file in files:
                link = {'mode': 'file', 'path': path, 'type': 'file',
                        'tdir': os.path.join(tdir, file)}
                self.drawItem(file, link, isFolder=False)
            if self.listing.size():
                self.setFocus(self.listing)
            else:
                self.setFocus(self.button_downloadstatus)

    def open_torrent(self, link, tdir=None):
        # cache
        if link != self.last_link:
            self.contentList = get_contentList(link)
        self.last_link = link

        dirList, contentListNew = cutFolder(self.contentList, tdir)

        if not tdir:
            params = {'mode': 'torrent_moveup', 'filename': link}
        else:
            params = {'mode': 'torrent_subfolder', 'filename': link}
        self.drawItem('..', params, isFolder=True)

        dirList = sorted(dirList, key=lambda x: x[0], reverse=False)
        for title in dirList:
            self.drawItem(title, {'mode': 'torrent_subfolder', 'tdir': title, 'filename': link}, isFolder=True)

        ids_video_result = get_ids_video(contentListNew)
        ids_video = ''

        if len(ids_video_result) > 0:
            for identifier in ids_video_result:
                ids_video = ids_video + str(identifier) + ','

        contentListNew = sorted(contentListNew, key=lambda x: x[0], reverse=False)
        for title, identifier, filesize in contentListNew:
            params = {'mode': 'torrent_play', 'url': identifier, 'url2': ids_video.rstrip(','), 'filename': link}
            self.drawItem(title, params)

    def get_menulist(self, mode):

        label_list = ["Empty", "Empty", "Empty", "Empty", "Empty", "Empty", "Empty"]

        if mode in ['search', 'search_item', 'torrent_play']:
            label_list = [self.localize('Open'),
                          self.localize('Download via T-client'),
                          self.localize('Download via Libtorrent'),
                          self.localize('Info'),]
        elif mode in ['torrent_subfolder', 'torrent_moveup',
                      'browser_moveup', 'file_browser', 'subfolder']:
            label_list = [self.localize('Open'),]
        elif mode in ['file']:
            label_list = [self.localize('Play'), ]
        elif mode in ['history', 'history_search_item']:
            label_list = [self.localize('Open'),
                          self.localize('Edit'),
                          self.localize('Individual Tracker Options'),
                          self.localize('Fav. / Unfav.'),
                          self.localize('Delete')]
        elif mode in ['browser', 'browser_item']:
            label_list = [self.localize('Open'), self.localize('Start'), self.localize('Stop'),
                          self.localize('Remove'), self.localize('High Priority'),
                          self.localize('Skip All Files'), self.localize('Remove with files')]
        elif mode in ['browser_file']:
            label_list = [self.localize('Play File'),
                          self.localize('High Priority'), self.localize('Skip File')]
        elif mode in ['browser_subfolder']:
            label_list = [self.localize('Open'),
                          self.localize('High Priority'),
                          self.localize('Skip All Files'),
                          self.localize('Copy in Root'), ]
        elif mode in ['downloadstatus', 'downloadstatus_subfolder']:
            label_list = [self.localize('Open'), self.localize('Start'), self.localize('Pause'),
                          self.localize('Stop'), self.localize('Delete'), self.localize('Mass Control'),]
        elif mode in ['downloadstatus_file']:
            label_list = [self.localize('Play'), self.localize('Start'), self.localize('Pause'),
                          self.localize('Stop'), self.localize('Delete'), self.localize('Mass Control'),]
        elif mode in ['watched', 'watched_item']:
            label_list = [self.localize('Open Torrent'), self.localize('Play (from start)'),
                          self.localize('Play (with seek)'), self.localize('Delete'), self.localize('Clear History'), ]
        return label_list

    def context(self):
        if self.getFocus() == self.listing:
            item = self.listing.getSelectedItem()
            params = json.loads(item.getfilename())
            mode = params.get('mode')
            filename = params.get('filename')
            label_list = self.get_menulist(mode)

            if not self.version_check():
                ret = xbmcgui.Dialog().select(self.localize('Context menu'), label_list)
            else:
                ret = xbmcgui.Dialog().contextmenu(list=[(x) for x in label_list])

            if ret > -1 and ret < len(label_list):
                getattr(self, "right_press" + str(ret + 1))()

    def right_menu(self, mode='place'):
        if not mode == 'place':
            self.last_right_buttons_count = self.right_buttons_count
            remove_list = [getattr(self, "button_right" + str(index)) for index
                           in range(1, self.last_right_buttons_count + 1)]
            self.disconnectEventList(remove_list)
            self.removeControls(remove_list)

        label_list = self.get_menulist(mode)
        self.navi['right_menu'] = []

        self.right_buttons_count = len(label_list)
        button_num_list = range(1, self.right_buttons_count + 1)

        for index in button_num_list:
            setattr(self, "button_right" + str(index), pyxbmct.Button(label_list[index - 1]))
            button = getattr(self, "button_right" + str(index))
            self.connect(button, getattr(self, "right_press" + str(index)))
            self.placeControl(button, index, 14, 1, 2)

        # Navigation
        self.navi['last_right_button'] = 1
        for index in button_num_list:
            button = getattr(self, "button_right" + str(index))
            self.navi['right_menu'].append(button)

            if self.right_buttons_count == 1:
                button.setNavigation(self.button_controlcenter,
                                     self.button_right1, self.listing, self.input_search)
            else:
                if index == button_num_list[0]:
                    button.setNavigation(getattr(self, "button_right" + str(self.right_buttons_count)),
                                         self.button_right2, self.listing, self.input_search)
                elif index == button_num_list[-1]:
                    button.setNavigation(getattr(self, "button_right" + str(index - 1)), self.button_right1,
                                         self.listing,
                                         self.input_search)
                else:
                    button.setNavigation(getattr(self, "button_right" + str(index - 1)),
                                         getattr(self, "button_right" + str(index + 1)),
                                         self.listing,
                                         self.input_search)

        self.set_menulist(mode)
        self.set_navigation()

    def set_menulist(self, mode):
        self.count += 1
        label_list = self.get_menulist(mode)
        debug('set_menulist; ' + str(label_list))

        right_buttons_count = len(label_list)
        button_num_list = range(1, right_buttons_count + 1)
        debug('set_menulist button_num_list: ' + str(button_num_list))

        for index in button_num_list:
            button = getattr(self, "button_right" + str(index))
            self.setlabel(button, (label_list[index - 1]))
            button.setEnabled(True)

        debug('set_menulist self.right_buttons_count: ' + str(right_buttons_count))
        debug('set_menulist right_buttons_count: ' + str(right_buttons_count))
        if self.right_buttons_count > right_buttons_count:
            disable_button_num_list = range(right_buttons_count + 1, self.right_buttons_count + 1)
            debug('set_menulist disable_button_num_list: ' + str(disable_button_num_list))
            for index in disable_button_num_list:
                button = getattr(self, "button_right" + str(index))
                button.setLabel(' ')
                button.setEnabled(False)

    def setlabel(self, button, label):
        label = label.decode('utf-8')

        debug('setlabel: ' + label + ' ' + str(len(label)))

        if len(label) > 10:
            spaces = label.count(' ')
            debug('setlabel spaces=' + str(spaces))
            if spaces == 0:
                words = [label[:10], label[10:]]
                label = '%s-\r\n%s' % (words[0], words[1])
            elif spaces == 1:
                words = label.split(' ')
                label = '%s\r\n%s' % (words[0], words[1])
            elif spaces == 2:
                words = label.split(' ')
                if len(words[0]) <= len(words[2]):
                    words[0] = words[0] + ' ' + words[1]
                    words[1] = words[2]
                else:
                    words[1] = words[1] + ' ' + words[2]
                label = '%s\r\n%s' % (words[0], words[1])

        button.setLabel(label)

    def right_press1(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        log('params ' + str(params))
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        ind = params.get('ind')
        tdir = params.get('tdir')
        self.listing.reset()
        if mode in ['search_item', 'torrent_subfolder']:
            #self.reconnect(pyxbmct.ACTION_NAV_BACK, self.search)
            self.open_torrent(filename, tdir)
        elif mode == 'torrent_moveup':
            self.search()
            self.setFocus(self.listing)
        elif mode == 'torrent_play':
            url = self.form_link('playTorrent', params)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            self.close()
        elif mode == 'history_search_item':
            addtime = params.get('addtime')
            self.input_search.setText(filename)
            params = {'addtime': addtime}
            self.search(params)
        elif mode in ['browser_item', 'browser_subfolder', 'browser_moveup']:
            self.browser(hash, tdir)
        elif mode == 'browser_file':
            self.browser_action(hash, 'play', tdir = tdir, ind = ind)
            self.close()
        elif mode in ['downloadstatus', 'downloadstatus_subfolder', 'downloadstatus_file']:
            self.downloadstatus_action('play', params.get('addtime'), params.get('path'),
                                       params.get('type'), params.get('progress'), params.get('storage'))
        elif mode in ['moveup', 'subfolder', 'file']:
            self.file_browser(params.get('type'), params.get('path'), tdir)
        elif mode == 'watched_item':
            self.watched_action('open', params.get('addtime'))

    def right_press2(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        ind = params.get('ind')
        tdir = params.get('tdir')
        if mode == 'torrent_play':
            action = 'downloadFilesList'
            link = {'ind': str(params.get('url'))}
            url = self.form_link(action, link)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
        elif mode == 'search_item':
            action = 'downloadFilesList'
            link = {'url': filename}
            url = self.form_link(action, link)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
        elif mode == 'history_search_item':
            self.input_search.setText(filename)
            self.setFocus(self.input_search)
        elif mode == 'browser_item':
            self.browser_action(hash, 'start')
        elif mode == 'browser_subfolder':
            self.browser_action(hash, '3', tdir=tdir, ind=ind)
        elif mode == 'browser_file':
            self.browser_action(hash, '3', tdir=tdir, ind=ind)
        elif mode in ['downloadstatus', 'downloadstatus_subfolder', 'downloadstatus_file']:
            self.downloadstatus_action('start', params.get('addtime'), params.get('path'),
                                       params.get('type'), params.get('progress'), params.get('storage'))
        elif mode == 'watched_item':
            self.watched_action('playnoseek', params.get('addtime'))

    def right_press3(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        ind = params.get('ind')
        tdir = params.get('tdir')
        if mode == 'torrent_play':
            action = 'downloadLibtorrent'
            link = {'ind': str(params.get('url'))}
            url = self.form_link(action, link)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
        elif mode == 'search_item':
            action = 'downloadLibtorrent'
            link = {'url': filename}
            url = self.form_link(action, link)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
        elif mode == 'history_search_item':
            params['title'] = params.get('filename')
            self.controlCenter(params)
        elif mode == 'browser_item':
            self.browser_action(hash, 'stop')
        elif mode == 'browser_subfolder':
            self.browser_action(hash, '0', tdir=tdir, ind=ind)
        elif mode == 'browser_file':
            self.browser_action(hash, '0', tdir=tdir, ind=ind)
        elif mode in ['downloadstatus', 'downloadstatus_subfolder', 'downloadstatus_file']:
            self.downloadstatus_action('pause', params.get('addtime'), params.get('path'),
                                       params.get('type'), params.get('progress'), params.get('storage'))
        elif mode == 'watched_item':
            self.watched_action('playwithseek', params.get('addtime'))

    def right_press4(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        ind = params.get('ind')
        tdir = params.get('tdir')
        if mode == 'history_search_item':
            addtime = params.get('addtime')
            fav = params.get('fav')
            self.history_action('fav', addtime, fav)
        elif mode == 'search_item':
            cleanlabel = re.sub('\[[^\]]*\]', '', item.getLabel())
            ttl, yr = xbmc.getCleanMovieTitle(cleanlabel)
            infoW = InfoWindow(ttl, yr)
            infoW.doModal()
            del infoW
        elif mode == 'browser_item':
            self.browser_action(hash, 'remove')
            self.browser()
        elif mode == 'browser_subfolder':
            self.browser_action(hash, 'copy', tdir=tdir, ind=ind)
        elif mode in ['downloadstatus', 'downloadstatus_subfolder', 'downloadstatus_file']:
            self.downloadstatus_action('stop', params.get('addtime'), params.get('path'),
                                       params.get('type'), params.get('progress'), params.get('storage'))
        elif mode == 'watched_item':
            self.watched_action('delete', params.get('addtime'))

    def right_press5(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        if mode == 'history_search_item':
            addtime = params.get('addtime')
            fav = params.get('fav')
            self.history_action('delete', addtime, fav)
        elif mode == 'browser_item':
            self.browser_action(hash, '3')
        elif mode in ['downloadstatus', 'downloadstatus_subfolder', 'downloadstatus_file']:
            self.downloadstatus_action('delete', params.get('addtime'), params.get('path'),
                                       params.get('type'), params.get('progress'), params.get('storage'))
        elif mode == 'watched_item':
            self.watched_action('clear', params.get('addtime'))

    def right_press6(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        if mode == 'browser_item':
            self.browser_action(hash, '0')
        elif mode in ['downloadstatus', 'downloadstatus_subfolder', 'downloadstatus_file']:
            self.downloadstatus_action('masscontrol', params.get('addtime'), params.get('path'),
                                       params.get('type'), params.get('progress'), params.get('storage'))

    def right_press7(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        if mode == 'browser_item':
            self.browser_action(hash, 'removedata')
            self.browser()

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string

    def drawItem(self, title, params, image=None, isFolder=False):
        if isinstance(params, str):
            params = {'mode': params}

        if not image and isFolder:
            image = 'DefaultFolder.png'
        elif not image:
            image = 'DefaultVideo.png'
        listitem = xbmcgui.ListItem(title, '', image, image, json.dumps(params))
        self.listing.addItem(listitem)

    def form_link(self, action, link):
        if isinstance(link, dict):
            link_url = ''
            for key in link.keys():
                if link.get(key) and key != 'mode':
                    link_url = '%s&%s=%s' % (link_url, key, urllib.quote_plus(link.get(key)))
            url = '%s?action=%s' % ('plugin://plugin.video.torrenter/', action) + link_url
        else:
            url = '%s?action=%s&url=%s' % ('plugin://plugin.video.torrenter/', action, urllib.quote_plus(link))

        return url

    def controlCenter(self, params={}):
        import controlcenter
        controlcenter.main()

    def reconnect(self, event, callable):
        self.disconnect(event)
        self.connect(event, callable)

    def version_check(self):
        return False if int(xbmc.getInfoLabel("System.BuildVersion")[:2]) < 17 else True

class InfoWindow(pyxbmct.AddonDialogWindow):
    def __init__(self, title="", year=""):
        super(InfoWindow, self).__init__(title)
        self.title = title
        self.year = year
        self.setGeometry(600, 600, 3, 3)
        self.set_controls()
        self.connect_controls()
        # self.set_navigation()

    def set_controls(self):
        # pyxbmct.AddonWindow().setImage(__root__ + '/resources/skins/Default/media/ConfluenceDialogBack.png')
        # self.placeControl(self.background, 0, 0, rowspan=3, columnspan=2)
        self.listing = pyxbmct.List(_imageWidth=30, _imageHeight=30, _itemTextXOffset=1,
                                    _itemTextYOffset=0, _itemHeight=30, _space=0, _alignmentY=0)
        self.placeControl(self.listing, 0, 1, 2, 2)
        self.logoimg = pyxbmct.Image('', aspectRatio=0)
        self.placeControl(self.logoimg, 0, 0, rowspan=2)
        self.plot = pyxbmct.TextBox()
        self.placeControl(self.plot, 2, 0, 1, columnspan=3)
        self.plot.autoScroll(1000, 1000, 1000)
        # self.button_search = pyxbmct.Button("Search")
        # self.placeControl(self.button_search, 0, 5, 1, 2)

    def connect_controls(self):
        from resources.scrapers.scrapers import Scrapers
        self.Scraper = Scrapers()
        meta = self.Scraper.scraper('tmdb', {'label': 'tmdb', 'search': self.title, 'year': ''}, 'en')
        meta = meta.get('info')

        """
        meta results for xXx
        {'info': {'count': 7451, 'plot': u'Xander Cage is your standard adrenaline junkie with no fear and a lousy attitude. When the US Government "recruits" him to go on a mission, he\'s not exactly thrilled. His mission: to gather information on an organization that may just be planning the destruction of the world, led by the nihilistic Yorgi.', 'votes': u'809', 'code': u'tt0295701', 'rating': 5.7000000000000002, 'title': u'xXx', 'tagline': u'A New Breed Of Secret Agent.', 'director': u'Rob Cohen', 'premiered': u'2002-08-09', 'originaltitle': u'xXx', 'cast': [u'Vin Diesel', u'Asia Argento', u'Marton Csokas', u'Samuel L. Jackson', u'Michael Roof', u'Petr J\xe1kl Jr.', u'Richy M\xfcller', u'Joe Bucaro III', u'Eve', u'Leila Arcieri', u'William Hope', u'Ted Maynard', u'Martin Hub'], 'castandrole': [u'Vin Diesel|Xander Cage', u'Asia Argento|Yelena', u'Marton Csokas|Yorgi', u'Samuel L. Jackson|Agent Gibbons', u'Michael Roof|Agent Toby Lee Shavers', u'Petr J\xe1kl Jr.|Kolya', u'Richy M\xfcller|Milan Sova', u'Joe Bucaro III|Virg', u'Eve|J.J.', u'Leila Arcieri|Jordan King', u'William Hope|Agent Roger Donnan', u'Ted Maynard|James Tannick', u'Martin Hub|Ivan Podrov'], 'studio': u'Columbia Pictures, Original Film, Revolution Studios', 'year': 2002, 'genre': u'Action', 'runtime': u'124'}, 'thumbnail': u'http://image.tmdb.org/t/p/original/fPHNTG1OXFBQ6aEVO7Lv8tSgfrY.jpg', 'label': 'tmdb', 'properties': {'fanart_image': u'http://image.tmdb.org/t/p/original/oNQIcuvJssiK93TjrXVtbERaKE1.jpg'}, 'icon': u'http://image.tmdb.org/t/p/original/fPHNTG1OXFBQ6aEVO7Lv8tSgfrY.jpg'}
        """
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.close)
        self.listing.addItem("Title: %s" % meta.get('title'))
        self.listing.addItem("genre: %s" % meta.get('genre'))
        self.listing.addItem("rating: %s" % meta.get('rating'))
        self.listing.addItem("year: %s" % meta.get('year'))
        self.listing.addItem("runtime: %sm" % meta.get('runtime'))
        if meta.get('thumbnail'):
            self.logoimg.setImage(meta.get('thumbnail'))
        self.plot.setText(meta.get('plot'))

def log(msg):
    try:
        xbmc.log("### [%s]: %s" % (__plugin__, msg,), level=xbmc.LOGNOTICE)
    except UnicodeEncodeError:
        xbmc.log("### [%s]: %s" % (__plugin__, msg.encode("utf-8", "ignore"),), level=xbmc.LOGNOTICE)
    except:
        xbmc.log("### [%s]: %s" % (__plugin__, 'ERROR LOG',), level=xbmc.LOGNOTICE)

def titleMake(seeds, leechers, size, title):
    # AARRGGBB
    clGreen = '[COLOR FF008000]%s[/COLOR]'
    clDodgerblue = '[COLOR FF1E90FF]%s[/COLOR]'
    clDimgray = '[COLOR FF999999]%s[/COLOR]'
    clWhite = '[COLOR FFFFFFFF]%s[/COLOR]'
    clAliceblue = '[COLOR FFF0F8FF]%s[/COLOR]'
    clRed = '[COLOR FFFF0000]%s[/COLOR]'

    title = title.replace('720p', '[B]720p[/B]').replace('1080p', '[B]1080p[/B]')
    title = clWhite % title
    second = '[I](%s) [S/L: %d/%d] [/I]' % (size, seeds, leechers)
    title += '\r\n' + clDimgray % second
    return title

def dlstat_titleMake(title, second):
    # AARRGGBB
    clDimgray = '[COLOR FF999999]%s[/COLOR]'
    clWhite = '[COLOR FFFFFFFF]%s[/COLOR]'
    title = clWhite % title
    title += '\r\n' + clDimgray % second
    return title


def main(params = None):
    dialog = SearchWindow(params)
    dialog.doModal()
    del dialog  # You need to delete your instance when it is no longer needed
    # because underlying xbmcgui classes are not grabage-collected.


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        import xbmc
        import traceback

        map(xbmc.log, traceback.format_exc().split("\n"))
        raise
