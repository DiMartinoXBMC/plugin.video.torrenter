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
import sys, os, urllib, json

import xbmcaddon
import xbmc
import xbmcgui
from functions import get_filesList, HistoryDB, get_contentList, log, cutFolder, get_ids_video, showMessage
import pyxbmct.addonwindow as pyxbmct
import Localization

__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__language__ = __settings__.getLocalizedString
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__
__root__ = __settings__.getAddonInfo('path')

log('SYS ARGV: ' + str(sys.argv))

#https://github.com/xbmc/xbmc/blob/8d4a5bba55638dfd0bdc5e7de34f3e5293f99933/xbmc/input/Key.h
ACTION_STOP = 13
ACTION_PLAYER_PLAY = 79

class SearchWindow(pyxbmct.AddonDialogWindow):
    __settings__ = sys.modules["__main__"].__settings__
    fileList = []
    contentList = []
    right_buttons_count = 6
    last_right_buttons_count = 0
    last_link = None
    last_query = None
    last_action = None
    last_top_button = None
    last_right_button = None

    def __init__(self, title=""):
        super(SearchWindow, self).__init__(title)
        self.setGeometry(1280, 720, 9, 16)
        self.set_controls()
        self.connect_controls()
        #self.set_navigation()
        self.history()

    def icon(self, icon):
        return '%s/icons/%s.png' %(__root__, icon)

    def set_controls(self):
        self.input_search = pyxbmct.Edit("", _alignment=pyxbmct.ALIGN_CENTER_X | pyxbmct.ALIGN_CENTER_Y)
        self.placeControl(self.input_search, 0, 0, 1, 5)
        self.button_search = pyxbmct.Button("Search")
        self.placeControl(self.button_search, 0, 5, 1, 2)
        self.button_history = pyxbmct.Button("History")
        self.placeControl(self.button_history, 0, 7, 1, 2)
        self.button_controlcenter = pyxbmct.Button("Control\r\nCenter")
        self.placeControl(self.button_controlcenter, 0, 9, 1, 2)

        self.listing = self.listing = pyxbmct.List(_imageWidth=60, _imageHeight=60, _itemTextXOffset=10,
                                                   _itemTextYOffset=2, _itemHeight=60, _space=2, _alignmentY=4)
        self.placeControl(self.listing, 1, 0, 8, 14)

        self.right_menu()


    def connect_controls(self):
        self.connect(self.listing, self.right_press1)
        self.connect(self.button_history, self.history)
        self.connect(self.button_search, self.search)
        self.connect(self.button_controlcenter, self.controlCenter)

        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.connect(pyxbmct.ACTION_PREVIOUS_MENU, self.close)

    def set_navigation(self):
        #Top menu
        self.input_search.setNavigation(self.listing, self.listing, self.last_right_button, self.button_search)
        self.button_search.setNavigation(self.listing, self.listing, self.input_search, self.button_history)
        self.button_history.setNavigation(self.listing, self.listing, self.button_search, self.button_controlcenter)
        self.button_controlcenter.setNavigation(self.listing, self.listing, self.button_history, self.last_right_button)
        #Listing
        self.listing.setNavigation(self.input_search, self.input_search, self.input_search, self.last_right_button)

        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.input_search)

    def setAnimation(self, control):
        # Set fade animation for all add-on window controls
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
                               ('WindowClose', 'effect=fade start=100 end=0 time=500',)])

    def search(self, addtime=None):
        self.reconnect(pyxbmct.ACTION_NAV_BACK, self.history)
        self.right_menu('search')
        self.listing.reset()
        query = self.input_search.getText()
        log('Search query: '+str(query))

        #cache
        if query != self.last_query and len(query)>0:
            self.filesList = get_filesList(query, addtime)
            self.last_query = query
        elif len(query)==0:
            self.filesList = [(1919, 1919, 52, u'102.66 MiB', u'South.Park.S20E06.HDTV.x264-FUM[ettv]',
                  u'ThePirateBay::magnet:?xt=urn:btih:0792ea51bc16a19893871197fa927ecec7ca25aa&dn=South.Park.S20E06.HDTV.x264-FUM%5Bettv%5D&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969&tr=udp%3A%2F%2Fzer0day.ch%3A1337&tr=udp%3A%2F%2Fopen.demonii.com%3A1337&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969&tr=udp%3A%2F%2Fexodus.desync.com%3A6969',
                  'C:\\Users\\Admin\\AppData\\Roaming\\Kodi\\addons\\torrenter.searcher.ThePirateBay\\icon.png'),
                    (1919, 1919, 52, u'102.66 MiB', u'Haruhi',
                     u'D:\\htest.torrent',
            'C:\\Users\\Admin\\AppData\\Roaming\\Kodi\\addons\\torrenter.searcher.ThePirateBay\\icon.png')   ]
        if 1==1:
            for (order, seeds, leechers, size, title, link, image) in self.filesList:
                title = titleMake(seeds, leechers, size, title)
                #log(title)
                self.drawItem(title, 'search_item', link, image)

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

                        link = {'mode': 'history_search_item', 'url': title, 'addtime': str(addtime), 'fav':str(fav)}
                        self.drawItem(bbstring % title, link, title, img)

    def right_press1(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getLabel2())
        mode = params.get('mode')
        filename = item.getfilename()
        label = item.getLabel()
        tdir = params.get('tdir')
        self.listing.reset()
        if mode == 'search_item':
            self.open_torrent(filename)
        elif mode == 'torrent_subfolder':
            self.open_torrent(filename, tdir)
        elif mode == 'torrent_moveup':
            self.last_action()
        elif mode == 'torrent_play':
            action = 'playTorrent'
            url = self.form_link(action, params)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            self.close()
        elif mode == 'history_search_item':
            self.input_search.setText(filename)
            self.search()

    def right_press2(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getLabel2())
        mode = params.get('mode')
        filename = item.getfilename()
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
        params = json.loads(item.getLabel2())
        filename = item.getfilename()
        mode = params.get('mode')
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
            addtime = params.get('addtime')
            url = (os.path.join(__root__, 'controlcenter.py,') +
                   'addtime=%s&title=%s' % (str(addtime), filename))
            xbmc.executebuiltin('xbmc.RunPlugin(%s)' % (url))

    def right_press4(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getLabel2())
        mode = params.get('mode')
        if mode == 'history_search_item':
            addtime = params.get('addtime')
            fav = params.get('fav')
            self.history_action('fav', addtime, fav)

    def right_press5(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getLabel2())
        mode = params.get('mode')
        if mode == 'history_search_item':
            addtime = params.get('addtime')
            fav = params.get('fav')
            self.history_action('delete', addtime, fav)

    def right_press6(self):
        pass

    def open_torrent(self, link, tdir = None):
        #cache
        if link != self.last_link:
            self.contentList = get_contentList(link)
        self.last_link = link

        dirList, contentListNew = cutFolder(self.contentList, tdir)

        if not tdir:
            self.drawItem('..', 'torrent_moveup', link, isFolder=True)
        else:
            params = {'mode': 'torrent_subfolder'}
            self.drawItem('..', params, link, isFolder=True)

        for title in dirList:
            self.drawItem(title, {'mode':'torrent_subfolder', 'tdir': title}, link, isFolder=True)

        ids_video_result = get_ids_video(contentListNew)
        ids_video=''

        if len(ids_video_result)>0:
            for identifier in ids_video_result:
                ids_video = ids_video + str(identifier) + ','

        for title, identifier, filesize in contentListNew:
            params = {'mode': 'torrent_play', 'url': identifier, 'url2': ids_video.rstrip(',')}
            self.drawItem(title, params, link)

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

    def right_menu(self, mode='place'):
        if not mode == 'place':
            self.last_right_buttons_count = self.right_buttons_count
            remove_list = [getattr(self, "button_right" + str(index)) for index
                           in range(1, self.last_right_buttons_count+1)]
            self.disconnectEventList(remove_list)
            self.removeControls(remove_list)

        label_list = []
        if mode == 'place':
            label_list = ["Empty","Empty","Empty","Empty","Empty","Empty"]

        elif mode == 'search':
            label_list = ["Open",
                          self.localize('Download via T-client'),
                          self.localize('Download via Libtorrent')]

        elif mode == 'history':
            label_list = [self.localize('Open'),
                          self.localize('Edit'),
                          self.localize('Individual Tracker Options'),
                          'Fav/Unfav',
                          self.localize('Delete')]

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

    def localize(self, string):
        try:
            return Localization.localize(string)
        except:
            return string

    def drawItem(self, title, params, link, image = None, isFolder = False):
        if isinstance(params, str):
            params = {'mode': params}

        if not image and isFolder:
            image = 'DefaultFolder.png'
        elif not image:
            image = 'DefaultVideo.png'
        listitem = xbmcgui.ListItem(title, json.dumps(params), image, image, link)
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

    def controlCenter(self):
        xbmc.executebuiltin(
            'xbmc.RunScript(%s,)' % os.path.join(__root__, 'controlcenter.py'))

    def reconnect(self, event, callable):
        self.disconnect(event)
        self.connect(event, callable)

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

if __name__ == "__main__":

    dialog = SearchWindow("Torrenter Search Window")
    dialog.doModal()
    del dialog #You need to delete your instance when it is no longer needed
    #because underlying xbmcgui classes are not grabage-collected.