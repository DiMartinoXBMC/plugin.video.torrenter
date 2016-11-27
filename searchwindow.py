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
from functions import get_filesList, HistoryDB, get_contentList, log, cutFolder, get_ids_video
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

class MultiChoiceDialog(pyxbmct.AddonDialogWindow):
    __settings__ = sys.modules["__main__"].__settings__
    fileList = []
    contentList = []
    right_buttons_count = 6
    last_right_buttons_count = 0
    last_link = None
    last_query = None
    last_action = None

    def __init__(self, title=""):
        super(MultiChoiceDialog, self).__init__(title)
        self.setGeometry(1280, 720, 9, 16)
        self.set_controls()
        self.connect_controls()
        self.set_navigation()

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
        self.right_menu()

        self.listing = pyxbmct.List(_imageWidth=40, _imageHeight=40, _itemTextXOffset=10, _itemTextYOffset=2, _itemHeight=40, _space=2, _alignmentY=4)
        self.placeControl(self.listing, 1, 0, 8, 14)

    def connect_controls(self):
        self.connect(self.listing, self.right_press1)
        self.connect(self.button_history, self.history)
        self.connect(self.button_search, self.search)
        self.connect(self.button_controlcenter, self.controlCenter)
        #self.connectEventList([ACTION_ENTER], self.search)

    def set_navigation(self):
        #Top menu
        self.input_search.setNavigation(self.listing, self.listing, self.button_right1, self.button_search)
        self.button_search.setNavigation(self.listing, self.listing, self.input_search, self.button_history)
        self.button_history.setNavigation(self.listing, self.listing, self.button_search, self.button_controlcenter)
        self.button_controlcenter.setNavigation(self.listing, self.listing, self.button_history, self.button_right1)
        #Listing
        self.listing.setNavigation(self.input_search, self.input_search, self.input_search, self.button_right1)
        #Right menu
        self.button_right1.setNavigation(self.button_controlcenter, self.button_right2, self.listing, self.input_search)
        self.button_right2.setNavigation(self.button_right1, self.button_right3, self.listing, self.input_search)
        self.button_right3.setNavigation(self.button_right2, self.button_right4, self.listing, self.input_search)
        self.button_right4.setNavigation(self.button_right3, self.button_right5, self.listing, self.input_search)
        self.button_right5.setNavigation(self.button_right4, self.button_right6, self.listing, self.input_search)
        self.button_right6.setNavigation(self.button_right5, self.button_right1, self.listing, self.input_search)

        if self.listing.size():
            self.setFocus(self.listing)
        else:
            self.setFocus(self.input_search)

    def setAnimation(self, control):
        # Set fade animation for all add-on window controls
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
                               ('WindowClose', 'effect=fade start=100 end=0 time=500',)])

    def search(self, addtime=None):
        self.last_action = self.search
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

    def right_press1(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getLabel2())
        log('right_press1 params: ' + str(params))
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
            log('url: '+url)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))
            self.close()

    def right_press2(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getLabel2())
        log('right_press2 params: ' + str(params))
        mode = params.get('mode')
        if mode == 'torrent_play':
            action = 'downloadFilesList'
            link = {'ind': str(params.get('url'))}
            url = self.form_link(action, link)
            log('url: ' + url)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))

    def right_press3(self):
        item = self.listing.getSelectedItem()
        params = json.loads(item.getLabel2())
        log('right_press3 params: ' + str(params))
        mode = params.get('mode')
        if mode == 'torrent_play':
            action = 'downloadLibtorrent'
            link = {'ind': str(params.get('url'))}
            url = self.form_link(action, link)
            log('url: ' + url)
            xbmc.executebuiltin('xbmc.RunPlugin("%s")' % (url))

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

    def history(self):
        self.right_menu('history')

    def history_search(self):
        xbmcgui.Dialog().ok('xxx','xxx')
        log('history_search: '+self.listing.getSelectedItem().getLabel())

    def right_menu(self, mode='place'):
        if not mode == 'place':
            self.last_right_buttons_count = self.right_buttons_count

        if mode == 'place':
            self.button_right1 = pyxbmct.Button("Empty")
            self.button_right2 = pyxbmct.Button("Empty")
            self.button_right3 = pyxbmct.Button("Empty")
            self.button_right4 = pyxbmct.Button("Empty")
            self.button_right5 = pyxbmct.Button("Empty")
            self.button_right6 = pyxbmct.Button("Empty")
            self.connect(self.button_right1, self.right_press1)
            self.connect(self.button_right2, self.right_press2)
            self.connect(self.button_right3, self.right_press3)
            #self.connect(self.button_right4, self.right_press2)
            #self.connect(self.button_right5, self.right_press2)
            #self.connect(self.button_right6, self.right_press2)

        elif mode == 'search':
            self.right_buttons_count = 3
            self.button_right1.setLabel("Open")
            self.connect(self.button_right1, self.right_press1)
            self.button_right2.setLabel(self.localize('Download via T-client'))
            self.connect(self.button_right2, self.right_press2)
            self.button_right3.setLabel(self.localize('Download via Libtorrent'))
            self.connect(self.button_right3, self.right_press3)

        elif mode == 'history':
            self.right_buttons_count = 5
            self.button_right1.setLabel("Search")
            self.button_right2.setLabel("Open2")
            self.button_right3.setLabel("Open3")
            self.button_right4.setLabel("Open2")
            self.button_right5.setLabel("Open3")

        control_list = [self.button_right1, self.button_right2, self.button_right3, self.button_right4, self.button_right5, self.button_right6]
        if self.last_right_buttons_count > self.right_buttons_count:
            self.removeControls(control_list[self.right_buttons_count:self.last_right_buttons_count])
        elif self.last_right_buttons_count < self.right_buttons_count:
            for button in control_list[self.last_right_buttons_count:self.right_buttons_count]:
                self.placeControl(button, control_list.index(button)+1, 14, 1, 2)

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

    dialog = MultiChoiceDialog("Torrenter Search Window")
    dialog.doModal()
    del dialog #You need to delete your instance when it is no longer needed
    #because underlying xbmcgui classes are not grabage-collected.