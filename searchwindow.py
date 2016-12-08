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
import xbmcaddon
import xbmc
import xbmcgui
from functions import *
import pyxbmct.addonwindow as pyxbmct
import Localization
import re

__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__language__ = __settings__.getLocalizedString
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__
__root__ = __settings__.getAddonInfo('path')

log('SYS ARGV: ' + str(sys.argv))

#https://github.com/xbmc/xbmc/blob/8d4a5bba55638dfd0bdc5e7de34f3e5293f99933/xbmc/input/Key.h
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
    right_buttons_count = 6
    last_right_buttons_count = 0
    last_link = None
    last_query = None
    last_action = None
    last_top_button = None
    last_right_button = None

    icon = __root__ + '/icons/searchwindow/%s.png'

    def __init__(self, title="", s_param={}):
        super(SearchWindow, self).__init__(title)
        self.setGeometry(1280, 720, 9, 16)
        self.set_controls()
        self.connect_controls()
        if s_param:
            self.search(s_param=s_param)
        else:
            self.history()

    def set_controls(self):
        self.background.setImage('%s/icons/%s.png' %(__root__, 'ContentPanel'))

        #Top menu
        self.button_downloadstatus = pyxbmct.Button("OFF", textColor = '0xFF0000FF', focusTexture = self.icon % 'fdownloadstatus', noFocusTexture = self.icon % 'nfdownloadstatus')
        self.placeControl(self.button_downloadstatus, 0, 2, 1, 1)
        self.button_torrentclient = pyxbmct.Button("OFF", textColor = '0xFF0000FF', focusTexture = self.icon % 'ftorrentclient', noFocusTexture = self.icon % 'nftorrentclient')
        self.placeControl(self.button_torrentclient, 0, 3, 1, 1)
        self.button_keyboard = pyxbmct.Button("", focusTexture = self.icon % 'fkeyboard', noFocusTexture = self.icon % 'nfkeyboard')
        self.placeControl(self.button_keyboard, 0, 4, 1, 1)
        self.input_search = pyxbmct.Edit("", _alignment=pyxbmct.ALIGN_CENTER_X | pyxbmct.ALIGN_CENTER_Y)
        self.placeControl(self.input_search, 0, 5, 1, 5)
        self.button_search = pyxbmct.Button("", focusTexture = self.icon % 'fsearch', noFocusTexture = self.icon % 'nfsearch')
        self.placeControl(self.button_search, 0, 10, 1, 1)
        self.button_history = pyxbmct.Button("", focusTexture = self.icon % 'fhistory', noFocusTexture = self.icon % 'nfhistory')
        self.placeControl(self.button_history, 0, 11, 1, 1)
        self.button_controlcenter = pyxbmct.Button("", focusTexture = self.icon % 'fcontrolcenter', noFocusTexture = self.icon % 'nfcontrolcenter')
        self.placeControl(self.button_controlcenter, 0, 12, 1, 1)

        #Main
        self.listing = pyxbmct.List(_imageWidth=60, _imageHeight=60, _itemTextXOffset=1,
                                    _itemTextYOffset=0, _itemHeight=60, _space=0, _alignmentY=4)
        self.placeControl(self.listing, 1, 0, 8, 14)

        #Right menu
        self.right_menu()

    def connect_controls(self):
        self.connect(self.listing, self.right_press1)
        self.connect(self.button_history, self.history)
        self.connect(self.button_search, self.search)
        self.connect(self.button_controlcenter, self.controlCenter)

        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.close)
        self.connect(ACTION_MOUSE_RIGHT_CLICK, self.context)
        self.connect(ACTION_CONTEXT_MENU, self.context)
        self.connect(ACTION_SHOW_OSD, self.context)

    def set_navigation(self):
        #Top menu
        self.button_downloadstatus.setNavigation(self.listing, self.listing, self.last_right_button, self.button_torrentclient)
        self.button_torrentclient.setNavigation(self.listing, self.listing, self.button_downloadstatus, self.button_keyboard)
        self.button_keyboard.setNavigation(self.listing, self.listing, self.button_torrentclient, self.input_search)
        self.input_search.setNavigation(self.listing, self.listing, self.button_keyboard, self.button_search)
        self.button_search.setNavigation(self.listing, self.listing, self.input_search, self.button_history)
        self.button_history.setNavigation(self.listing, self.listing, self.button_search, self.button_controlcenter)
        self.button_controlcenter.setNavigation(self.listing, self.listing, self.button_history, self.last_right_button)

        #Main
        self.listing.setNavigation(self.input_search, self.input_search, self.button_downloadstatus, self.last_right_button)

        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.input_search)

    def setAnimation(self, control):
        # Set fade animation for all add-on window controls
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
                               ('WindowClose', 'effect=fade start=100 end=0 time=500',)])

    def search(self, addtime=None, s_param={}):
        self.reconnect(pyxbmct.ACTION_NAV_BACK, self.history)
        self.right_menu('search')
        self.listing.reset()
        if s_param:
            if s_param.get('url'):
                search = urllib.unquote_plus(s_param.get('url'))
                external = s_param.get("return_name")
                if external:
                    searcher = 'landing from : %s ' % str(external)
                else:
                    searcher = ''
                self.setWindowTitle(title='%s %s' % ('Torrenter Search Window', searcher))
                if s_param.get('showKey') == 'true':
                    self.input_search.setText(search)
                    query = self.input_search.getText()
                else:
                    self.input_search.setText(search)
                    query = search
                #self.setFocus(self.listing)
            else:
                query = self.input_search.getText()
                self.history()
        else:
            query = self.input_search.getText()
        log('Search query: '+str(query))

        if not addtime and query == self.last_query:
            addtime = self.addtime

        searchersList = get_searchersList(addtime)

        #cache
        if (query != self.last_query or self.searchersList != searchersList) and len(query)>0:
            self.filesList = get_filesList(query, searchersList, addtime)
            self.addtime = addtime
            self.searchersList = searchersList
            self.last_query = query
        elif len(query)==0:
            self.filesList = []
        if 1==1:
            if self.filesList:
                for (order, seeds, leechers, size, title, link, image) in self.filesList:
                    title = titleMake(seeds, leechers, size, title)
                    self.drawItem(title, {'mode':'search_item', 'filename': link}, image)
                    self.setFocus(self.listing)

    def history(self):
        self.right_menu('history')
        self.listing.reset()
        self.reconnect(pyxbmct.ACTION_NAV_BACK, self.close)

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

                        link = {'mode': 'history_search_item', 'filename': title, 'addtime': str(addtime), 'fav':str(fav)}
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

    def browser(self, params={}):
        from resources.utorrent.net import Download
        self.right_menu('browser')
        self.listing.reset()
        menu, dirs = [], []
        contextMenustring = 'XBMC.RunPlugin(%s)' % ('%s?action=%s&url=%s') % (sys.argv[0], 'uTorrentBrowser', '%s')

        get = params.get

        action = get('action')
        hash = get('hash')
        ind = get('ind')
        tdir = get('tdir')


        DownloadList = Download().list()
        if DownloadList == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
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
            self.drawItem(i, 'uTorrentBrowser', link, isFolder=folder)

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

            self.drawItem(i['title'], 'uTorrentBrowser', link, image=img, isFolder=folder)

        return

    def browser_action(self, params={}):
        from resources.utorrent.net import Download

        get = params.get

        action = get('action')
        hash = get('hash')
        ind = get('ind')
        tdir = get('tdir')

        DownloadList = Download().list()
        if DownloadList == False:
            showMessage(self.localize('Error'), self.localize('No connection! Check settings!'), forced=True)
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

                folder = folder.replace(t_dir, torrent_replacement)
            if (ind or ind == 0) and action == 'play':
                for data in dllist:
                    if data[2] == int(ind):
                        filename = data[0]
                        break
                filename = os.path.join(folder, filename)
                xbmc.executebuiltin('xbmc.PlayMedia("' + filename.encode('utf-8') + '")')
            elif tdir and action == 'copy':
                path=os.path.join(folder, tdir)
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
                    if not xbmcvfs.exists(os.path.join(path,file)):
                        xbmcvfs.delete(os.path.join(path,file))
                    xbmcvfs.copy(os.path.join(path,file),os.path.join(folder,file))
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

    def open_torrent(self, link, tdir = None):
        #cache
        if link != self.last_link:
            self.contentList = get_contentList(link)
        self.last_link = link
        self.reconnect(pyxbmct.ACTION_NAV_BACK, self.search)

        dirList, contentListNew = cutFolder(self.contentList, tdir)

        if not tdir:
            self.drawItem('..', {'mode': 'torrent_moveup', 'filename': link}, isFolder=True)
        else:
            params = {'mode': 'torrent_subfolder', 'filename': link}
            self.drawItem('..', params, isFolder=True)

        dirList = sorted(dirList, key=lambda x: x[0], reverse=False)
        for title in dirList:
            self.drawItem(title, {'mode':'torrent_subfolder', 'tdir': title, 'filename': link}, isFolder=True)

        ids_video_result = get_ids_video(contentListNew)
        ids_video=''

        if len(ids_video_result)>0:
            for identifier in ids_video_result:
                ids_video = ids_video + str(identifier) + ','

        contentListNew = sorted(contentListNew, key=lambda x: x[0], reverse=False)
        for title, identifier, filesize in contentListNew:
            params = {'mode': 'torrent_play', 'url': identifier, 'url2': ids_video.rstrip(','), 'filename': link}
            self.drawItem(title, params)

    def get_menulist(self, mode):

        label_list = ["Empty","Empty","Empty","Empty","Empty","Empty"]

        if mode in ['search', 'search_item', 'torrent_play']:
            label_list = ["Open",
                          self.localize('Download via T-client'),
                          self.localize('Download via Libtorrent'),
                          'Info']
        elif mode in ['torrent_subfolder', 'torrent_moveup']:
            label_list = ["Open"]
        elif mode in ['history', 'history_search_item']:
            label_list = [self.localize('Open'),
                          self.localize('Edit'),
                          self.localize('Individual Tracker Options'),
                          'Fav/Unfav',
                          self.localize('Delete')]

        elif mode in ['browser', 'browser_item']:
            label_list = [self.localize('Start'), self.localize('Stop'),
                          self.localize('Remove'), self.localize('High Priority Files'),
                          self.localize('Skip All Files'), self.localize('Remove with files')]
        elif mode in ['browser_file']:
            label_list = [self.localize('High Priority'), self.localize('Skip File'),
                          self.localize('Play File')]
        elif mode in ['browser_folder']:
            label_list = [self.localize('High Priority Files'),
                          self.localize('Copy Files in Root'),
                          self.localize('Skip All Files')]

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
                           in range(1, self.last_right_buttons_count+1)]
            self.disconnectEventList(remove_list)
            self.removeControls(remove_list)

        label_list = self.get_menulist(mode)

        self.right_buttons_count = len(label_list)
        button_num_list = range(1, self.right_buttons_count+1)

        for index in button_num_list:
            setattr(self, "button_right" + str(index), pyxbmct.Button(label_list[index - 1]))
            button = getattr(self, "button_right" + str(index))
            self.connect(button, getattr(self, "right_press"+str(index)))
            self.placeControl(button, index, 14, 1, 2)

        #Navigation
        self.last_right_button = self.button_right1
        for index in button_num_list:
            button = getattr(self, "button_right" + str(index))

            if self.right_buttons_count == 1:
                button.setNavigation(self.button_controlcenter, self.button_right1, self.listing, self.input_search)
            else:
                if index == button_num_list[0]:
                    button.setNavigation(self.button_controlcenter, self.button_right2, self.listing, self.input_search)
                elif index == button_num_list[-1]:
                    button.setNavigation(getattr(self, "button_right" + str(index-1)), self.button_right1, self.listing,
                                                     self.input_search)
                else:
                    button.setNavigation(getattr(self, "button_right" + str(index - 1)),
                                         getattr(self, "button_right" + str(index + 1)),
                                         self.listing,
                                         self.input_search)

        self.set_navigation()

    def right_press1(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        tdir = params.get('tdir')
        self.listing.reset()
        if mode == 'search_item':
            self.open_torrent(filename)
        elif mode == 'torrent_subfolder':
            self.open_torrent(filename, tdir)
        elif mode == 'torrent_moveup':
            self.search()
            self.setFocus(self.listing)
        elif mode == 'torrent_play':
            action = 'playTorrent'
            url = self.form_link(action, params)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            self.close()
        elif mode == 'history_search_item':
            addtime = params.get('addtime')
            self.input_search.setText(filename)
            self.search(addtime)

    def right_press2(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
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

    def right_press3(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
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

    def right_press4(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        if mode == 'history_search_item':
            addtime = params.get('addtime')
            fav = params.get('fav')
            self.history_action('fav', addtime, fav)
        else:
            cleanlabel = re.sub('\[[^\]]*\]', '', item.getLabel())
            ttl, yr = xbmc.getCleanMovieTitle(cleanlabel)
            infoW = InfoWindow(ttl, yr)
            infoW.doModal()
            del infoW

    def right_press5(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getfilename())
        mode = params.get('mode')
        filename = params.get('filename')
        if mode == 'history_search_item':
            addtime = params.get('addtime')
            fav = params.get('fav')
            self.history_action('delete', addtime, fav)

    def right_press6(self):
        pass

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string

    def drawItem(self, title, params, image = None, isFolder = False):
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
        return False if int(xbmc.getInfoLabel( "System.BuildVersion" )[:2]) < 17 else True

    def onFocus(self):
        log(str(self.getFocusId()))


class InfoWindow(pyxbmct.AddonDialogWindow):


    def __init__(self, title="", year=""):
        super(InfoWindow, self).__init__(title)
        self.title = title
        self.year = year
        self.setGeometry(600, 600, 3, 3)
        self.set_controls()
        self.connect_controls()
        #self.set_navigation()


    def set_controls(self):
        #pyxbmct.AddonWindow().setImage(__root__ + '/resources/skins/Default/media/ConfluenceDialogBack.png')
        #self.placeControl(self.background, 0, 0, rowspan=3, columnspan=2)
        self.listing = pyxbmct.List(_imageWidth=30, _imageHeight=30, _itemTextXOffset=1,
                                    _itemTextYOffset=0, _itemHeight=30, _space=0, _alignmentY=0)
        self.placeControl(self.listing, 0, 1, 2, 2)
        self.logoimg = pyxbmct.Image('', aspectRatio=0)
        self.placeControl(self.logoimg, 0, 0, rowspan=2)
        self.plot = pyxbmct.TextBox()
        self.placeControl(self.plot, 2, 0, 1, columnspan=3)
        self.plot.autoScroll(1000, 1000, 1000)
        #self.button_search = pyxbmct.Button("Search")
        #self.placeControl(self.button_search, 0, 5, 1, 2)


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
        self.listing.addItem ("Title: %s" % meta.get('title'))
        self.listing.addItem ("genre: %s" % meta.get('genre'))
        self.listing.addItem ("rating: %s" % meta.get('rating'))
        self.listing.addItem ("year: %s" % meta.get('year'))
        self.listing.addItem ("runtime: %sm" % meta.get('runtime'))
        if meta.get('thumbnail'):
            self.logoimg.setImage (meta.get('thumbnail'))
        self.plot.setText(meta.get('plot'))
    
def log(msg):
    try:
        xbmc.log("### [%s]: %s" % (__plugin__,msg,), level=xbmc.LOGNOTICE )
    except UnicodeEncodeError:
        xbmc.log("### [%s]: %s" % (__plugin__,msg.encode("utf-8", "ignore"),), level=xbmc.LOGNOTICE )
    except:
        xbmc.log("### [%s]: %s" % (__plugin__,'ERROR LOG',), level=xbmc.LOGNOTICE )

def titleMake(seeds, leechers, size, title):

    #AARRGGBB
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


def main(params={}):
    dialog = SearchWindow("Torrenter Search Window", params)
    dialog.doModal()
    del dialog #You need to delete your instance when it is no longer needed
    #because underlying xbmcgui classes are not grabage-collected.


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        import xbmc
        import traceback

        map(xbmc.log, traceback.format_exc().split("\n"))
        raise
