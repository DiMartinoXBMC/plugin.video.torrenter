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

import sys

import xbmcaddon
import xbmc
import xbmcgui
from functions import getParameters, HistoryDB, Searchers, log
import pyxbmct

__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__language__ = __settings__.getLocalizedString
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__
__root__ = __settings__.getAddonInfo('path')

log('SYS ARGV: ' + str(sys.argv))

if len(sys.argv) > 1:
    params = getParameters(sys.argv[1])
else:
    params = {}

class ControlCenter(pyxbmct.AddonDialogWindow):
    def __init__(self, title, addtime=None):
        super(ControlCenter, self).__init__(title)

        self.dic = Searchers().dic()
        self.db = None
        self.addtime = None
        self.has_searchers=len(self.dic)>0
        self.more_one_searcher=len(self.dic)>1
        self.more_two_searcher=len(self.dic)>2
        if self.has_searchers:
            if addtime:
                self.addtime = addtime
                self.db = HistoryDB()
                providers = self.db.get_providers(addtime)
                if not providers:
                    self.db.set_providers(addtime, self.dic)
                else:
                    for searcher in self.dic.keys():
                        self.dic[searcher] = False
                    for searcher in providers:
                        try:
                            if searcher in self.dic.keys():
                                self.dic[searcher] = True
                        except:
                            log('self.dic[searcher] except')

            self.keys = self.dic.keys()
            self.placed, self.button_columns, self.last_column_row = self.place()
        else:
            self.button_columns=0


        self.setGeometry(850, 200 + 50 * self.button_columns, 4 + self.button_columns, 3)
        self.set_info_controls()
        self.set_active_controls()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def place(self):
        placed = {}
        i, j = -1, 0
        for item in self.keys:
            if i == 2:
                i = 0
                j += 1
            else:
                i += 1
            placed[item] = (j, i)
        return placed, j, i

    def set_info_controls(self):
        pass

    def set_active_controls(self):
        # RadioButton
        if self.has_searchers:
            self.radiobutton = {}
            self.radiobutton_top, self.radiobutton_bottom = [None, None, None], [None, None, None]
            for searcher in self.keys:
                place = self.placed[searcher]
                self.radiobutton[searcher] = pyxbmct.RadioButton(searcher)
                self.placeControl(self.radiobutton[searcher], place[0], place[1])
                self.radiobutton[searcher].setSelected(self.dic[searcher])
                self.connect(self.radiobutton[searcher], self.radio_update)
                if place[0] == 0:
                    self.radiobutton_top[place[1]] = self.radiobutton[searcher]
                self.radiobutton_bottom[place[1]] = self.radiobutton[searcher]

        # Button
        self.button_install = pyxbmct.Button(__language__(30415))
        self.placeControl(self.button_install, 2 + self.button_columns, 0)
        self.connect(self.button_install, self.installSearcher)

        # Button
        self.button_openserchset = pyxbmct.Button(__language__(30416))
        self.placeControl(self.button_openserchset, 2 + self.button_columns, 1)
        self.connect(self.button_openserchset, self.openSearcherSettings)

        # Button
        self.button_clearstor = pyxbmct.Button(__language__(30417))
        self.placeControl(self.button_clearstor, 2 + self.button_columns, 2)
        self.connect(self.button_clearstor, self.clearStorage)

        # Button
        self.button_openset = pyxbmct.Button(__language__(30413))
        self.placeControl(self.button_openset, 3 + self.button_columns, 0)
        self.connect(self.button_openset, self.openSettings)

        # Button
        self.button_utorrent = pyxbmct.Button(__language__(30414))
        self.placeControl(self.button_utorrent, 3 + self.button_columns, 1)
        self.connect(self.button_utorrent, self.openUtorrent)

        # Button
        self.button_close = pyxbmct.Button(__language__(30412))
        self.placeControl(self.button_close, 3 + self.button_columns, 2)
        self.connect(self.button_close, self.close)

    def set_navigation(self):
        if self.has_searchers:
            # Set navigation between controls
            placed_values = self.placed.values()
            placed_keys = self.placed.keys()
            for searcher in placed_keys:

                buttons_upper = [self.button_install, self.button_openserchset, self.button_clearstor]
                buttons_lower = [self.button_openset, self.button_utorrent, self.button_close]
                place = self.placed[searcher]

                if place[0] == 0:
                    self.radiobutton[searcher].controlUp(buttons_lower[place[1]])
                else:
                    ser = placed_keys[placed_values.index((place[0] - 1, place[1]))]
                    self.radiobutton[searcher].controlUp(self.radiobutton[ser])

                # self.button_columns, self.last_column_row
                if self.more_one_searcher:
                    if place[1] == 0 and place[0] == self.button_columns:
                        if self.last_column_row > 0:
                            ser = placed_keys[placed_values.index((place[0], self.last_column_row))]
                        else:
                            ser = placed_keys[placed_values.index((place[0] - 1, 2))]
                    elif place[1] == 0:
                        ser = placed_keys[placed_values.index((place[0], 2))]
                    else:
                        ser = placed_keys[placed_values.index((place[0], place[1] - 1))]
                    self.radiobutton[searcher].controlLeft(self.radiobutton[ser])

                    if self.more_two_searcher:
                        if place == (self.button_columns, self.last_column_row) and self.last_column_row < 2:
                            ser = placed_keys[placed_values.index((place[0] - 1, place[1] + 1))]
                        elif place[1] == 2:
                            ser = placed_keys[placed_values.index((place[0], 0))]
                        else:
                            ser = placed_keys[placed_values.index((place[0], place[1] + 1))]
                        self.radiobutton[searcher].controlRight(self.radiobutton[ser])

                if place[0] == self.button_columns - 1 and place[1] > self.last_column_row or \
                                place[0] == self.button_columns:
                    self.radiobutton[searcher].controlDown(buttons_upper[place[1]])
                else:
                    ser = placed_keys[placed_values.index((place[0] + 1, place[1]))]
                    self.radiobutton[searcher].controlDown(self.radiobutton[ser])

            self.button_install.controlUp(self.radiobutton_bottom[0])
            self.button_openset.controlDown(self.radiobutton_top[0])
            if self.more_one_searcher:
                self.button_openserchset.controlUp(self.radiobutton_bottom[1])
                self.button_utorrent.controlDown(self.radiobutton_top[1])
            else:
                self.button_openserchset.controlUp(self.radiobutton_bottom[0])
                self.button_utorrent.controlDown(self.radiobutton_top[0])
            if self.more_two_searcher:
                self.button_clearstor.controlUp(self.radiobutton_bottom[2])
                self.button_close.controlDown(self.radiobutton_top[2])
            elif self.more_one_searcher:
                self.button_clearstor.controlUp(self.radiobutton_bottom[1])
                self.button_close.controlDown(self.radiobutton_top[1])
            else:
                self.button_clearstor.controlUp(self.radiobutton_bottom[0])
                self.button_close.controlDown(self.radiobutton_top[0])
        else:
            self.button_install.controlUp(self.button_openset)
            self.button_openserchset.controlUp(self.button_utorrent)
            self.button_clearstor.controlUp(self.button_close)
            self.button_openset.controlDown(self.button_install)
            self.button_utorrent.controlDown(self.button_openserchset)
            self.button_close.controlDown(self.button_clearstor)

        self.button_install.controlDown(self.button_openset)
        self.button_install.controlLeft(self.button_clearstor)
        self.button_install.controlRight(self.button_openserchset)

        self.button_openserchset.controlDown(self.button_utorrent)
        self.button_openserchset.controlLeft(self.button_install)
        self.button_openserchset.controlRight(self.button_clearstor)

        self.button_clearstor.controlDown(self.button_close)
        self.button_clearstor.controlLeft(self.button_openserchset)
        self.button_clearstor.controlRight(self.button_install)

        self.button_openset.controlUp(self.button_install)
        self.button_openset.controlLeft(self.button_close)
        self.button_openset.controlRight(self.button_utorrent)

        self.button_utorrent.controlUp(self.button_openserchset)
        self.button_utorrent.controlLeft(self.button_openset)
        self.button_utorrent.controlRight(self.button_close)

        self.button_close.controlUp(self.button_clearstor)
        self.button_close.controlLeft(self.button_utorrent)
        self.button_close.controlRight(self.button_openset)

        # Set initial focus
        self.setFocus(self.button_close)

    def openSettings(self):
        __settings__.openSettings()

    def openSearcherSettings(self):
        slist=Searchers().activeExternal()
        if len(slist)>0:
            if len(slist) == 1:
                ret = 0
            else:
                ret = xbmcgui.Dialog().select(__language__(30418), slist)
            if ret > -1 and ret < len(slist):
                sid = slist[ret]
                Searcher=xbmcaddon.Addon(id='torrenter.searcher.'+sid)
                Searcher.openSettings()
                self.close()
        else:
            xbmcgui.Dialog().ok(__language__(30415), slist)

    def installSearcher(self):
        xbmc.executebuiltin('Dialog.Close(all,true)')
        xbmc.executebuiltin('XBMC.ActivateWindow(Addonbrowser,addons://search/%s)' % ('Torrenter Searcher'))
        self.close()

    def openUtorrent(self):
        xbmc.executebuiltin('Dialog.Close(all,true)')
        xbmc.executebuiltin('ActivateWindow(Videos,plugin://plugin.video.torrenter/?action=uTorrentBrowser)')
        self.close()

    def clearStorage(self):
        xbmc.executebuiltin('XBMC.RunPlugin(%s)' % ('plugin://plugin.video.torrenter/?action=%s') % 'clearStorage')

    def slider_update(self):
        # Update slider value label when the slider nib moves
        try:
            if self.getFocus() == self.slider:
                self.slider_value.setLabel('%.1f' % self.slider.getPercent())
        except (RuntimeError, SystemError):
            pass

    def radio_update(self):
        # Update radiobutton caption on toggle
        index = self.radiobutton.values().index(self.getFocus())
        dic = Searchers().dic()
        searcher = self.radiobutton.keys()[index]
        if self.addtime:
            self.db.change_providers(self.addtime, searcher)
        else:
            Searchers().setBoolSetting(searcher, not dic[searcher])

    def list_update(self):
        # Update list_item label when navigating through the list.
        try:
            if self.getFocus() == self.list:
                self.list_item_label.setLabel(self.list.getListItem(self.list.getSelectedPosition()).getLabel())
            else:
                self.list_item_label.setLabel('')
        except (RuntimeError, SystemError):
            pass

    def setAnimation(self, control):
        # Set fade animation for all add-on window controls
        control.setAnimations([('WindowOpen', 'effect=fade start=0 end=100 time=500',),
                               ('WindowClose', 'effect=fade start=100 end=0 time=500',)])


def main():
    title = 'Torrenter Global Control Center'
    addtime = None
    if params.get('title'):
        title = str(params.get('title'))
        addtime = str(params.get('addtime'))

    window = ControlCenter(title, addtime)
    window.doModal()


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        import xbmc
        import traceback

        map(xbmc.log, traceback.format_exc().split("\n"))
        raise
