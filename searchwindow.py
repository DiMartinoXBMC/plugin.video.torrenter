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
import xbmc

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
    right_buttons_count = 7
    right_label_count = 7
    last_right_buttons_count = 0
    last_top_button = None
    last_right_button = None
    last_listing_mode = None
    route = {}
    count = 0
    navi_right_menu = []
    navi_top_menu = []

    icon = __root__ + '/icons/searchwindow/%s.png'
    icon_tc = __root__ + '/icons/searchwindow/%s' + getTorrentClientIcon()

    def __init__(self, params = None):
        log('SearchWindow init params: '+str(params))
        super(SearchWindow, self).__init__(self.localize('Torrenter Search Window'))
        __settings__.setSetting('loadsw_onstop', 'false')
        self.setGeometry(1280, 720, 9, 16)
        self.set_navi()
        self.set_controls()
        self.set_focus()
        self.connect_controls()
        if params and params.get('mode'):
            if params.get('mode') == 'load':
                self.navi_load()
            elif params.get('mode') == 'search':
                self.search(params)
            elif params.get('mode') == 'externalsearch':
                self.externalsearch(params)
            elif params.get('mode') == 'history':
                self.history()
            elif params.get('mode') == 'downloadstatus':
                self.downloadstatus()
            elif params.get('mode') == 'browser':
                self.browser()
            elif params.get('mode') == 'watched':
                self.watched()
            elif params.get('mode') == 'open_torrent':
                self.open_torrent(params)
            elif params.get('mode') == 'file_browser':
                self.file_browser(params)
        else:
            self.navi_load()

    def set_navi(self):
        self.navi = {
            'last_top_button': 4,
            'last_right_button': 1,
            'contentList': [],
            'searchersList': [],
            'filesList': [],
            'last_addtime': None,
            'last_query': None,
            'last_link': None,
            'last_filename': None,
            'route': [{'mode': 'close', 'params': {}, 'last_listing_item': 0}]
        }

    def set_controls(self):
        if not __settings__.getSetting('sw_transparent_back') == 'true':
            self.background.setImage('%s/icons/%s.png' % (__root__, 'ContentPanel'))

        # Top menu
        self.button_downloadstatus = pyxbmct.Button("",
                                                    focusTexture=self.icon % 'fdownloadstatus',
                                                    noFocusTexture=self.icon % 'nfdownloadstatus')
        self.placeControl(self.button_downloadstatus, 0, 1, 1, 1)

        self.button_browser = pyxbmct.Button("",
                                                   focusTexture=self.icon_tc % 'f',
                                                   noFocusTexture=self.icon_tc % 'nf')
        self.placeControl(self.button_browser, 0, 2, 1, 1)
        self.button_controlcenter = pyxbmct.Button("", focusTexture=self.icon % 'fcontrolcenter',
                                                   noFocusTexture=self.icon % 'nfcontrolcenter')
        self.placeControl(self.button_controlcenter, 0, 3, 1, 1)
        self.button_filter = pyxbmct.Button("", focusTexture=self.icon % 'fkeyboard',
                                              noFocusTexture=self.icon % 'nfkeyboard')
        self.placeControl(self.button_filter, 0, 4, 1, 1)
        self.input_search = pyxbmct.Edit("", _alignment=pyxbmct.ALIGN_CENTER_X | pyxbmct.ALIGN_CENTER_Y)
        self.placeControl(self.input_search, 0, 5, 1, 6)
        self.button_search = pyxbmct.Button("", focusTexture=self.icon % 'fsearch',
                                            noFocusTexture=self.icon % 'nfsearch')
        self.placeControl(self.button_search, 0, 11, 1, 1)
        self.button_history = pyxbmct.Button("", focusTexture=self.icon % 'fhistory',
                                             noFocusTexture=self.icon % 'nfhistory')
        self.placeControl(self.button_history, 0, 12, 1, 1)
        self.button_watched = pyxbmct.Button("", focusTexture=self.icon % 'fwatched',
                                             noFocusTexture=self.icon % 'nfwatched')
        self.placeControl(self.button_watched, 0, 13, 1, 1)

        # Main
        self.listing = pyxbmct.List(_imageWidth=60, _imageHeight=60, _itemTextXOffset=1,
                                    _itemTextYOffset=0, _itemHeight=60, _space=0, _alignmentY=4)
        self.placeControl(self.listing, 1, 0, 8, 14)

        self.navi_top_menu = [self.button_downloadstatus, self.button_browser, self.button_controlcenter,
                                 self.input_search, self.button_search, self.button_history, self.button_watched]

        # Right menu
        self.right_menu()

    def connect_controls(self):
        self.connect(self.listing, self.right_press1)
        self.connect(self.button_history, self.history)
        self.connect(self.button_search, self.search)
        self.connect(self.button_controlcenter, self.controlcenter)
        self.connect(self.button_browser, self.browser)
        self.connect(self.button_downloadstatus, self.downloadstatus)
        self.connect(self.button_watched, self.watched)
        self.connect(self.button_filter, self.filter)

        self.connect(pyxbmct.ACTION_NAV_BACK, self.navi_back)
        self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.navi_back)
        self.connect(xbmcgui.ACTION_BACKSPACE, self.navi_back)
        self.connect(xbmcgui.KEY_BUTTON_BACK, self.navi_back)

        self.connect(ACTION_MOUSE_RIGHT_CLICK, self.context)
        self.connect(ACTION_CONTEXT_MENU, self.context)
        self.connect(ACTION_SHOW_OSD, self.context)

        self.connect(pyxbmct.ACTION_MOVE_LEFT, self.navi_update)
        self.connect(pyxbmct.ACTION_MOVE_RIGHT, self.navi_update)
        self.connect(pyxbmct.ACTION_MOVE_UP, self.navi_update)
        self.connect(pyxbmct.ACTION_MOVE_DOWN, self.navi_update)

    def set_navigation(self):
        # Top menu
        self.button_browser.setNavigation(self.window_close_button, self.listing, self.button_downloadstatus,
                                          self.button_controlcenter)
        self.button_controlcenter.setNavigation(self.window_close_button, self.listing, self.button_browser, self.button_filter)
        self.button_filter.setNavigation(self.window_close_button, self.listing, self.button_controlcenter, self.input_search)
        self.input_search.setNavigation(self.window_close_button, self.listing, self.button_filter, self.button_search)
        self.button_search.setNavigation(self.window_close_button, self.listing, self.input_search, self.button_history)
        self.button_history.setNavigation(self.window_close_button, self.listing, self.button_search, self.button_watched)
        self.update_navigation()

    def update_navigation(self):
        self.last_top_button = self.navi_top_menu[self.navi['last_top_button'] - 1]
        if self.navi['last_right_button'] > self.right_label_count:
            self.navi['last_right_button'] = self.right_label_count
        self.last_right_button = self.navi_right_menu[self.navi['last_right_button'] - 1]

        # Top menu
        self.button_downloadstatus.setNavigation(self.window_close_button, self.listing, self.last_right_button,
                                                 self.button_browser)
        self.button_watched.setNavigation(self.window_close_button, self.listing, self.button_history, self.last_right_button)
        self.window_close_button.setNavigation(self.listing, self.last_top_button, self.button_watched,
                                               self.button_downloadstatus)
        # Main
        self.listing.setNavigation(self.last_top_button, self.input_search, self.button_downloadstatus,
                                   self.last_right_button)

    def setAnimation(self, control):
        # Set fade animation for all add-on window controls
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
                               ('WindowClose', 'effect=fade start=100 end=0 time=500',)])

    def navi_back(self):
        debug('navi_back init')
        self.navi['route'].pop(-1)
        self.navi_restore()

    def navi_route_reset(self):
        debug('navi_route_reset init')
        self.navi['route'] = [self.navi['route'][0]]

    def navi_route_pop(self):
        debug('navi_route_pop init')
        self.navi['route'].pop(-1)

    def navi_restore(self):
        debug('navi_restore init')
        self.route = self.navi['route'].pop(-1)
        action = getattr(self, self.route['mode'])
        try:
            if self.route['params']:
                action(self.route['params'])
            else:
                action()

            self.set_focus(self.route['mode'])

            debug('self.route[last_listing_item]: ' + str(self.route['last_listing_item']))
            if self.route['last_listing_item'] > 0:
                self.listing.selectItem(self.route['last_listing_item'])
        except:
            import traceback
            debug('navi_restore ERROR '+traceback.format_exc())
            self.set_navi()
            self.history()

    def navi_load(self):
        debug('navi_load init')
        __tmppath__ = os.path.join(xbmc.translatePath('special://temp'), 'xbmcup', 'plugin.video.torrenter')
        if not xbmcvfs.exists(__tmppath__):
            xbmcvfs.mkdirs(__tmppath__)
        navi_file = os.path.join(__tmppath__, 'navi.txt')
        if not xbmcvfs.exists(navi_file):
            self.set_navi()
            self.navi['route'].append({"last_listing_item": 0, "params": {}, "mode": "history"})
            with open(navi_file, 'w') as f: f.write(json.dumps(self.navi))

        with open(navi_file, 'r') as read: navi = read.read()

        try:
            debug('navi_load navi: '+str(navi))
            log('navi_load navi: ' + str(navi['route']))
        except:
            log('navi_load load error')

        if navi and len(navi) > 0:
            self.navi = json.loads(navi)
            self.navi_restore()

    def navi_save(self, mode = None):
        debug('navi_save init')

        self.set_focus(mode)

        navi = json.dumps(self.navi)

        __tmppath__ = os.path.join(xbmc.translatePath('special://temp'), 'xbmcup', 'plugin.video.torrenter')
        if not xbmcvfs.exists(__tmppath__):
            xbmcvfs.mkdirs(__tmppath__)
        navi_file = os.path.join(__tmppath__, 'navi.txt')
        write = xbmcvfs.File(navi_file, 'w')
        write.write(navi)
        write.close()

    def navi_update(self):
        debug('navi_update init')
        try:
            focused_control = self.getFocus()
        except:
            focused_control = None
        debug('start navi_update' + str(focused_control))
        debug(str(self.navi['route']))

        if focused_control == self.listing:
            item_index = self.listing.getSelectedPosition()
            self.navi['route'][-1]['last_listing_item'] = item_index
            debug('self.listing getSelectedPosition ' + str(item_index))

            item = self.listing.getSelectedItem()
            params = json.loads(item.getfilename())
            mode = params.get('mode')
            debug('navi_update:' + str(mode))
            if self.last_listing_mode != mode:
                self.last_listing_mode = mode
                debug('set_menulist navi_update:' + str(mode))
                self.set_menulist(mode)
                self.update_navigation()

        elif focused_control in self.navi_top_menu:
            self.navi['last_top_button'] = self.navi_top_menu.index(focused_control) + 1
            self.update_navigation()

        elif focused_control in self.navi_right_menu:
            self.navi['last_right_button'] = self.navi_right_menu.index(focused_control) + 1
            self.update_navigation()

    def navi_route(self, mode, params = {}, right_menu = None):
        debug('navi_route init')
        try:
            focused_control = self.getFocus()
        except:
            focused_control = None

        if focused_control in self.navi_top_menu:
            debug('focused_control in self.navi[\'top_menu\']')
            self.navi_route_reset()

        debug('***** self.navi[\'route\'].append *****' + str(mode) + str(params))

        self.navi['route'].append({'mode': mode,
                                   'params': params,
                                   'last_listing_item': 0})

        self.right_menu(mode if not right_menu else right_menu)
        self.listing.reset()

    def set_focus(self, mode = None):
        if not self.listing.size():
            if mode and hasattr(self, "button_" + mode):
                self.setFocus(getattr(self, "button_" + mode))
            else:
                self.setFocus(self.input_search)
        else:
            self.setFocus(self.listing)

    def search(self, params = {}):
        log('search init params: ' + str(params))
        self.navi_route('search', params)

        get = params.get
        addtime = get('addtime')
        query = get('query')
        self.route = self.navi['route'][-1]

        if query:
            self.input_search.setText(query)
        else:
            if self.input_search.getText() not in ['', None]:
                query = self.input_search.getText()
            elif self.navi['last_query'] not in ['', None]:
                query = self.navi['last_query']
                self.input_search.setText(self.navi['last_query'])
            
        log('Search query: ' + str(query))

        if not addtime and query == self.navi['last_query']:
            addtime = self.navi['last_addtime']

        searchersList = get_searchersList(addtime)

        # cache
        self.route['params']['query'] = query
        if (query != self.navi['last_query'] or self.navi['searchersList'] != searchersList) and len(query) > 0:
            self.navi['filesList'] = get_filesList(query, searchersList, addtime)
            self.route['params']['addtime'] = addtime
            self.navi['last_addtime'] = addtime
            self.navi['searchersList'] = searchersList
            self.navi['last_query'] = query
        elif len(query) == 0:
            self.navi['filesList'] = []

        if self.navi['filesList']:
            for (order, seeds, leechers, size, title, link, image) in self.navi['filesList']:
                title = titleMake(seeds, leechers, size, title)
                self.drawItem(title, {'mode': 'search_item', 'filename': link}, image)
            self.setFocus(self.listing)

    def externalsearch(self, params={}):
        log('search init params: ' + str(params))

        if hasattr(self, 'params'):
            params = self.params

        self.params = params
        get = params.get
        query = unquote(get('query'),'')
        external = unquote(params.get("external"), 'torrenterall')
        back_url = unquote(get("back_url"),'')
        self.return_name = unquote(get("return_name"),'')
        sdata = unquote(get("sdata"),'{}')

        self.reconnect(self.button_search, self.externalsearch)
        self.navi_route('externalsearch', params)

        try:
            sdata = json.loads(sdata)
        except:
            sdata = json.loads(urllib.unquote_plus(sdata))


        if self.input_search.getText() not in ['', None]:
            query = self.input_search.getText()
        else:
            self.input_search.setText(query)

        #contextMenu = [
        #    (self.localize('Add to %s') % return_name,
        #     'XBMC.RunPlugin(%s)' % (back_url + '&stringdata=' + urllib.quote_plus(
        #         json.dumps(sdata)))),


        # url = 'plugin://plugin.video.torrenter/?action=searchWindow&mode=externalsearch&query=%s' \
        #          '&sdata=%s&external=%s&back_url=%s&return_name=%s' % \
        #          (urllib.quote_plus(query), urllib.quote_plus(json.dumps(sdata)),
        #           self.externals[self.stype], urllib.quote_plus(back_self.url),
        #           urllib.quote_plus(return_name))

        log('Search query: ' + str(query))

        searchersList = []

        if not external or external == 'torrenterall':
                searchersList = get_searchersList()
        elif external == 'torrenterone':
            slist = Searchers().list().keys()
            ret = xbmcgui.Dialog().select(self.localize('Choose searcher')+':', slist)
            if ret > -1 and ret < len(slist):
                external = slist[ret]
                searchersList.append(external)
        else:
            searchersList.append(external)

        if len(query) > 0:
            self.navi['filesList'] = get_filesList(query, searchersList)
        else:
            self.navi['filesList'] = []

        if self.navi['filesList']:
            for (order, seeds, leechers, size, title, link, image) in self.navi['filesList']:
                title = titleMake(seeds, leechers, size, title)
                sdata['filename'] = link
                stringdata = json.dumps(sdata)
                self.drawItem(title, {'mode': 'externalsearch_item', 'filename': link,
                                      'stringdata': stringdata, 'back_url': back_url}, image)
            self.setFocus(self.listing)

    def history(self, params = {}):
        self.navi_route('history', params)

        db = HistoryDB()
        items = db.get_all()
        favlist = [(1, '[B]%s[/B]'), (0, '%s')]
        last_listing_item = 0
        last_addtime_fav = False
        if items:
            for favbool, bbstring in favlist:
                for addtime, string, fav in items:
                    if favbool == int(fav):
                        title = string.encode('utf-8')

                        if int(fav) == 1:
                            img = __root__ + '/icons/fav.png'
                            if str(self.navi['last_addtime']) == str(addtime):
                                last_addtime_fav = True
                            if not last_addtime_fav:
                                last_listing_item += 1
                        else:
                            img = __root__ + '/icons/unfav.png'

                        link = {'mode': 'history_item', 'query': title, 'addtime': str(addtime),
                                'fav': str(fav)}
                        self.drawItem(bbstring % title, link, img)
            self.route['last_listing_item'] = last_listing_item
        self.navi_save('history')

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

        self.navi_restore()

    def watched(self, params = {}):
        self.navi_route('watched', params)

        db = WatchedHistoryDB()

        items = db.get_all()
        log('[WatchedHistory]: items - '+str(items))
        if items:
            for addtime, filename, foldername, path, url, seek, length, ind, size in items:
                seek = int(seek) if int(seek) > 3*60 else 0
                watchedPercent = int((float(seek) / float(length if length else 1)) * 100)
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
        self.navi_save('watched')

    def watched_action(self, action, addtime):
        db = WatchedHistoryDB()

        if action == 'delete':
            db.delete(addtime)
            showMessage(self.localize('Watched History'), self.localize('Deleted!'))
            self.navi_restore()

        if action == 'open':
            filename, foldername, path, url, seek, length, ind = db.get('filename, foldername, path, url, seek, length, ind', 'addtime', str(addtime))
            params = {'link': path.encode('utf-8')}
            self.open_torrent(params)

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
            __settings__.setSetting('loadsw_onstop', 'true')
            self.close()

        if action == 'clear':
            db.clear()
            showMessage(self.localize('Watched History'), self.localize('Clear!'))
            self.navi_restore()

    def browser(self, params = {}):
        from resources.utorrent.net import Download
        menu, dirs = [], []

        get = params.get
        hash = get('hash')
        tdir = get('tdir')

        DownloadList = Download().list()
        if DownloadList == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
            return

        if not hash:
            self.navi_route('browser')
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
                menu.append(
                    {"title": title, "image": img, "argv": {'mode': 'browser_item', 'hash': str(data['id'])}})
        elif not tdir:
            self.navi_route('browser', params, 'browser_subfolder')
            self.drawItem('..', {'mode': 'browser_moveup'}, image = 'DefaultFolderBack.png', isFolder = True)
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
            self.navi_route('browser', params, 'browser_subfolder')
            self.drawItem('..', {'mode': 'browser_moveup'}, isFolder=True)
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

        self.navi_save('browser')

    def browser_action(self, hash, action, tdir = None, ind = None):
        from resources.utorrent.net import Download
        menu = []

        DownloadList = Download().list()
        if DownloadList == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
            return False

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
                self.file_play(filename)
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
            return True
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
            return True
        return True

    def downloadstatus(self, params = {}):
        self.navi_route('downloadstatus', params)

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

        self.navi_save('downloadstatus')

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

    def file_browser(self, params):
        self.navi_route('file_browser', params)

        get = params.get
        mode = get('mode')
        path = get('path')
        tdir = get('tdir')

        path = encode_msg(path)
        tdir = encode_msg(tdir)

        if mode == 'moveup' and tdir == os.path.dirname(path):
            self.downloadstatus()
        elif mode == 'file':
            swPlayer().play(localize_path(tdir))
        else:
            self.drawItem('..', {'mode': 'moveup', 'path': path,
                                 'tdir': os.path.dirname(tdir)}, image = 'DefaultFolderBack.png', isFolder=True)

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

        self.navi_save('file_browser')

    def file_play(self, file):
        self.close()
        swPlayer().play(item = file)

    def open_torrent(self, params):
        self.navi_route('open_torrent', params)

        get = params.get
        link = get('link')
        tdir = get('tdir')

        # cache
        if link != self.navi['last_link']:
            self.navi['contentList'], filename = get_contentList(link)
        else:
            filename = self.navi['last_filename']
        self.navi['last_link'] = link
        self.navi['last_filename'] = filename

        dirList, contentListNew = cutFolder(self.navi['contentList'], tdir)

        self.drawItem('..', {'mode': 'torrent_moveup', 'filename': link},
                      image = 'DefaultFolderBack.png', isFolder=True)

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
            params = {'mode': 'torrent_play', 'index': identifier, 'url2': ids_video.rstrip(','), 'url': link,
                      'filename': filename}
            self.drawItem(title, params)

        self.navi_save('open_torrent')

    def get_menulist(self, mode):

        label_list = ["Empty", "Empty", "Empty", "Empty", "Empty", "Empty", "Empty"]

        if mode in ['search', 'search_item', 'torrent_play', 'open_torrent']:
            label_list = [self.localize('Open'),
                          self.localize('Download via T-client'),
                          self.localize('Download via Libtorrent'),
                          self.localize('Info'),]
        if mode in ['externalsearch', 'externalsearch_item']:
            label_list = [self.localize('Add to %s') % self.return_name,
                          self.localize('Open'),
                          self.localize('Download via T-client'),
                          self.localize('Download via Libtorrent'),
                          self.localize('Info'),]
        elif mode in ['torrent_subfolder', 'file_browser', 'subfolder']:
            label_list = [self.localize('Open'),]
        elif mode in ['torrent_moveup', 'browser_moveup']:
            label_list = [self.localize('Move Up'),]
        elif mode in ['file']:
            label_list = [self.localize('Play'), ]
        elif mode in ['history', 'history_item']:
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
        self.right_label_count = len(label_list)
        return label_list

    def context(self):
        try:
            focused_control = self.getFocus()
        except:
            focused_control = None
        if focused_control == self.listing:
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
        elif focused_control == self.input_search:
            self.input_search.setText('')

    def right_menu(self, mode='place'):
        if not mode == 'place':
            self.last_right_buttons_count = self.right_buttons_count
            remove_list = [getattr(self, "button_right" + str(index)) for index
                           in range(1, self.last_right_buttons_count + 1)]
            self.disconnectEventList(remove_list)
            self.removeControls(remove_list)

        label_list = self.get_menulist(mode)
        self.navi_right_menu = []

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
            self.navi_right_menu.append(button)

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

        button_num_list = range(1, self.right_label_count + 1)
        debug('set_menulist button_num_list: ' + str(button_num_list))

        for index in button_num_list:
            button = getattr(self, "button_right" + str(index))
            self.setlabel(button, (label_list[index - 1]))
            button.setEnabled(True)

        if self.right_buttons_count > self.right_label_count:
            disable_button_num_list = range(self.right_label_count + 1, self.right_buttons_count + 1)
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
        self.right_press(1)

    def right_press2(self):
        self.right_press(2)

    def right_press3(self):
        self.right_press(3)

    def right_press4(self):
        self.right_press(4)

    def right_press5(self):
        self.right_press(5)

    def right_press6(self):
        self.right_press(6)

    def right_press7(self):
        self.right_press(7)

    def right_press(self, index):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        log('right_press %d params %s' % (index, str(params)))
        mode = params.get('mode')
        filename = params.get('filename')
        hash = params.get('hash')
        ind = params.get('ind')
        tdir = params.get('tdir')
        action = None

        if mode in ['search_item', 'torrent_subfolder', 'externalsearch', 'externalsearch_item']:
            if mode in ['externalsearch', 'externalsearch_item']:
                index = index - 1

            if index == 0:
                url = params.get('back_url') + '&stringdata=' + urllib.quote_plus(params.get('stringdata'))
                xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            elif index == 1:
                params = {'link': filename, 'tdir': tdir}
                self.open_torrent(params)
            elif index == 2:
                action = 'downloadFilesList'
                link = {'url': filename}
                url = self.form_link(action, link)
                xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            elif index == 3:
                action = 'downloadLibtorrent'
                link = {'url': filename}
                url = self.form_link(action, link)
                xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            elif index == 4: #search_item
                cleanlabel = re.sub('\[[^\]]*\]', '', item.getLabel())
                ttl, yr = xbmc.getCleanMovieTitle(cleanlabel)
                infoW = InfoWindow(ttl, yr)
                infoW.doModal()
                del infoW
        elif mode in ['torrent_moveup', 'browser_moveup', 'moveup']:
            self.navi_back()
        elif mode == 'torrent_play':
            if index == 1:
                if filename and xbmcvfs.exists(filename):
                    params['url'] = ensure_str(filename)
                url = self.form_link('playSTRM', params)
                xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
                __settings__.setSetting('loadsw_onstop', 'true')
                self.close()
            elif index == 2:
                action = 'downloadFilesList'
                link = {'ind': str(params.get('url'))}
                url = self.form_link(action, link)
                xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            elif index == 3:
                action = 'downloadLibtorrent'
                link = {'ind': str(params.get('url'))}
                url = self.form_link(action, link)
                xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
        elif mode == 'history_item':
            addtime = params.get('addtime')
            fav = params.get('fav')
            query = params.get('query')
            if index == 1:
                self.input_search.setText(query)
                self.search({'addtime': addtime})
            elif index == 2:
                self.input_search.setText(query)
                self.setFocus(self.input_search)
            elif index == 3:
                params['title'] = params.get('query')
                self.controlCenter(params)
            else:
                if index == 4: action = 'fav'
                elif index == 5: action = 'delete'
                self.history_action(action, addtime, fav)
        elif mode in ['browser_item', 'browser_subfolder']:
            if index == 1:
                self.browser(params)
            elif index in [2, 3, 4] and mode =='browser_subfolder':
                if index == 2: action = '3'
                elif index == 3: action = '0'
                elif index == 4: action = 'copy'

                self.browser_action(hash, action, tdir=tdir, ind=ind)
            else:
                if index == 2: action = 'start'
                elif index == 3: action = 'stop'
                elif index == 4: action = 'remove'
                elif index == 5: action = '3'
                elif index == 6: action = '0'
                elif index == 7: action = 'removedata'

                if self.browser_action(hash, action):
                    self.navi_restore()
        elif mode == 'browser_file':
            if index == 1: action = 'play'
            elif index == 2: action = '3'
            elif index == 3: action = '0'

            self.browser_action(hash, action, tdir = tdir, ind = ind)
        elif mode in ['downloadstatus', 'downloadstatus_subfolder', 'downloadstatus_file']:
            if index == 1: action = 'play'
            elif index == 2: action = 'start'
            elif index == 3: action = 'pause'
            elif index == 4: action = 'stop'
            elif index == 5: action = 'delete'
            elif index == 6: action = 'masscontrol'
            self.downloadstatus_action(action, params.get('addtime'), params.get('path'),
                                       params.get('type'), params.get('progress'), params.get('storage'))
        elif mode in ['subfolder', 'file']:
            self.file_browser(params)
        elif mode == 'watched_item':
            if index == 1: action = 'open'
            elif index == 2: action = 'playnoseek'
            elif index == 3: action = 'playwithseek'
            elif index == 4: action = 'delete'
            elif index == 5: action = 'clear'
            self.watched_action(action, params.get('addtime'))

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
                    link_url = '%s&%s=%s' % (link_url, key, urllib.quote_plus(ensure_str(link.get(key))))
            url = '%s?action=%s' % ('plugin://plugin.video.torrenter/', action) + link_url
        else:
            url = '%s?action=%s&url=%s' % ('plugin://plugin.video.torrenter/', action, urllib.quote_plus(link))

        return url

    def controlcenter(self, params={}):
        import controlcenter
        controlcenter.main()

    def reconnect(self, event, callable):
        self.disconnect(event)
        self.connect(event, callable)

    def version_check(self):
        return False if int(xbmc.getInfoLabel("System.BuildVersion")[:2]) < 17 else True

    def filter(self):
        list = self.listing
        self.listing.setPageControlVisible(True)
        size = self.listing.size()
        if size > 0:
            for index in range(0, size):
                listitem = self.listing.getListItem(index)

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
        xbmc.log("#SW# [%s]: %s" % (__plugin__, msg,), level=xbmc.LOGNOTICE)
    except UnicodeEncodeError:
        xbmc.log("#SW# [%s]: %s" % (__plugin__, msg.encode("utf-8", "ignore"),), level=xbmc.LOGNOTICE)
    except:
        xbmc.log("#SW# [%s]: %s" % (__plugin__, 'ERROR LOG',), level=xbmc.LOGNOTICE)

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

class swPlayer(xbmc.Player):
    def play(self, item):
        xbmc.Player().play(item = item)
        i = 0
        while not self.isPlaying() and i < 100:
            i += 1
            xbmc.sleep(500)
            log('swPlayer not started '+str(i))

        if i > 99:
            return False
        else:
            while not xbmc.abortRequested and self.isPlaying():
                xbmc.sleep(500)
                log('swPlayer playing')

            params = {'mode': 'load'}
            main(params)

if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        import xbmc
        import traceback

        map(xbmc.log, traceback.format_exc().split("\n"))
        raise
