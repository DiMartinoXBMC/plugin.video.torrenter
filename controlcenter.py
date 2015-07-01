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

import sys

import xbmcaddon
import xbmc
import xbmcgui
from functions import getParameters, HistoryDB
from resources.pyxbmct.addonwindow import *
from functions import Searchers

__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__language__ = __settings__.getLocalizedString
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__
__root__ = __settings__.getAddonInfo('path')

print 'SYS ARGV: ' + str(sys.argv)

if len(sys.argv) > 1:
    params = getParameters(sys.argv[1])
else:
    params = {}


class MyAddon(AddonDialogWindow):
    def __init__(self, title=''):
        super(MyAddon, self).__init__(title)
        self.setGeometry(700, 450, 9, 4)
        self.set_info_controls()
        self.set_active_controls()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(ACTION_NAV_BACK, self.close)

    def set_info_controls(self):
        # Demo for PyXBMCt UI controls.
        no_int_label = Label('Information output', alignment=ALIGN_CENTER)
        self.placeControl(no_int_label, 0, 0, 1, 2)
        #
        label_label = Label('Label')
        self.placeControl(label_label, 1, 0)
        # Label
        self.label = Label('Simple label')
        self.placeControl(self.label, 1, 1)
        #
        fadelabel_label = Label('FadeLabel')
        self.placeControl(fadelabel_label, 2, 0)
        # FadeLabel
        self.fade_label = FadeLabel()
        self.placeControl(self.fade_label, 2, 1)
        self.fade_label.addLabel('Very long string can be here.')
        #
        textbox_label = Label('TextBox')
        self.placeControl(textbox_label, 3, 0)
        # TextBox
        self.textbox = TextBox()
        self.placeControl(self.textbox, 3, 1, 2, 1)
        self.textbox.setText('Text box.\nIt can contain several lines.')
        #
        image_label = Label('Image')
        self.placeControl(image_label, 5, 0)

    def set_active_controls(self):
        int_label = Label('Interactive Controls', alignment=ALIGN_CENTER)
        self.placeControl(int_label, 0, 2, 1, 2)
        #
        radiobutton_label = Label('RadioButton')
        self.placeControl(radiobutton_label, 1, 2)
        # RadioButton
        self.radiobutton = RadioButton('Off')
        self.placeControl(self.radiobutton, 1, 3)
        self.connect(self.radiobutton, self.radio_update)
        #
        edit_label = Label('Edit')
        self.placeControl(edit_label, 2, 2)
        # Edit
        self.edit = Edit('Edit')
        self.placeControl(self.edit, 2, 3)
        # Additional properties must be changed after (!) displaying a control.
        self.edit.setText('Enter text here')
        #
        list_label = Label('List')
        self.placeControl(list_label, 3, 2)
        #
        self.list_item_label = Label('', textColor='0xFF808080')
        self.placeControl(self.list_item_label, 4, 2)
        # List
        self.list = List()
        self.placeControl(self.list, 3, 3, 3, 1)
        # Add items to the list
        items = ['Item %s' % i for i in range(1, 8)]
        self.list.addItems(items)
        # Connect the list to a function to display which list item is selected.
        self.connect(self.list, lambda: xbmc.executebuiltin('Notification(Note!,%s selected.)' %
                                                            self.list.getListItem(
                                                                self.list.getSelectedPosition()).getLabel()))
        # Connect key and mouse events for list navigation feedback.
        self.connectEventList(
            [ACTION_MOVE_DOWN, ACTION_MOVE_UP, ACTION_MOUSE_WHEEL_DOWN, ACTION_MOUSE_WHEEL_UP, ACTION_MOUSE_MOVE],
            self.list_update)
        # Slider value label
        SLIDER_INIT_VALUE = 25.0
        self.slider_value = Label(str(SLIDER_INIT_VALUE), alignment=ALIGN_CENTER)
        self.placeControl(self.slider_value, 6, 3)
        #
        slider_caption = Label('Slider')
        self.placeControl(slider_caption, 7, 2)
        # Slider
        self.slider = Slider()
        self.placeControl(self.slider, 7, 3, pad_y=10)
        self.slider.setPercent(SLIDER_INIT_VALUE)
        # Connect key and mouse events for slider update feedback.
        self.connectEventList([ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOUSE_DRAG], self.slider_update)
        #
        button_label = Label('Button')
        self.placeControl(button_label, 8, 2)
        # Button
        self.button = Button('Close')
        self.placeControl(self.button, 8, 3)
        # Connect control to close the window.
        self.connect(self.button, self.close)

    def set_navigation(self):
        # Set navigation between controls
        self.button.controlUp(self.slider)
        self.button.controlDown(self.radiobutton)
        self.radiobutton.controlUp(self.button)
        self.radiobutton.controlDown(self.edit)
        self.edit.controlUp(self.radiobutton)
        self.edit.controlDown(self.list)
        self.list.controlUp(self.edit)
        self.list.controlDown(self.slider)
        self.slider.controlUp(self.list)
        self.slider.controlDown(self.button)
        # Set initial focus
        self.setFocus(self.radiobutton)

    def slider_update(self):
        # Update slider value label when the slider nib moves
        try:
            if self.getFocus() == self.slider:
                self.slider_value.setLabel('%.1f' % self.slider.getPercent())
        except (RuntimeError, SystemError):
            pass

    def radio_update(self):
        # Update radiobutton caption on toggle
        if self.radiobutton.isSelected():
            self.radiobutton.setLabel('On')
        else:
            self.radiobutton.setLabel('Off')

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


class ControlCenter(AddonDialogWindow):
    def __init__(self, title, addtime=None):
        super(ControlCenter, self).__init__(title)

        self.dic = Searchers().dic()
        self.db = None
        self.addtime = None
        self.keys = self.dic.keys()
        if addtime:
            self.addtime = addtime
            self.db = HistoryDB()
            providers = self.db.get_providers(addtime)
            if not providers:
                self.db.set_providers(addtime, self.dic)
            else:
                for searcher in self.keys:
                    self.dic[searcher] = False
                for searcher in providers:
                    try:
                        if searcher in self.keys:
                            self.dic[searcher] = True
                    except:
                        pass

        self.keys = self.dic.keys()
        self.placed, self.button_columns, self.last_column_row = self.place()

        self.setGeometry(850, 200 + 50 * self.button_columns, 4 + self.button_columns, 3)
        self.set_info_controls()
        self.set_active_controls()
        self.set_navigation()
        # Connect a key action (Backspace) to close the window.
        self.connect(ACTION_NAV_BACK, self.close)

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
            # print item+str((j, i))
        return placed, j, i

    def set_info_controls(self):
        # Demo for PyXBMCt UI controls.
        # no_int_label = Label(__language__(30146), alignment=ALIGN_CENTER)
        # self.placeControl(no_int_label, 0, 0, 1, 3)
        #
        # label_timeout = Label(__language__(30410))
        # self.placeControl(label_timeout, 1, 0)
        # Label
        # self.label = Label(__language__(30545) % TimeOut().timeout())
        # self.placeControl(self.label, 1, 1)
        #
        # label_watched = Label(__language__(30414) % (WatchedDB().count()))
        # self.placeControl(label_watched, 2, 0)
        pass

    def set_active_controls(self):
        # RadioButton
        self.radiobutton = {}
        self.radiobutton_top, self.radiobutton_bottom = [None, None, None], [None, None, None]
        for searcher in self.keys:
            place = self.placed[searcher]
            self.radiobutton[searcher] = RadioButton(searcher)
            self.placeControl(self.radiobutton[searcher], place[0], place[1])
            self.radiobutton[searcher].setSelected(self.dic[searcher])
            self.connect(self.radiobutton[searcher], self.radio_update)
            if place[0] == 0:
                self.radiobutton_top[place[1]] = self.radiobutton[searcher]
            self.radiobutton_bottom[place[1]] = self.radiobutton[searcher]

        # Button
        self.button_install = Button(__language__(30415))
        self.placeControl(self.button_install, 2 + self.button_columns, 0)
        self.connect(self.button_install, self.installSearcher)

        # Button
        self.button_openserchset = Button(__language__(30416))
        self.placeControl(self.button_openserchset, 2 + self.button_columns, 1)
        self.connect(self.button_openserchset, self.openSearcherSettings)

        # Button
        self.button_clearstor = Button(__language__(30417))
        self.placeControl(self.button_clearstor, 2 + self.button_columns, 2)
        self.connect(self.button_clearstor, self.clearStorage)

        # Button
        self.button_openset = Button(__language__(30413))
        self.placeControl(self.button_openset, 3 + self.button_columns, 0)
        self.connect(self.button_openset, self.openSettings)

        # Button
        self.button_utorrent = Button(__language__(30414))
        self.placeControl(self.button_utorrent, 3 + self.button_columns, 1)
        self.connect(self.button_utorrent, self.openUtorrent)

        # Button
        self.button_close = Button(__language__(30412))
        self.placeControl(self.button_close, 3 + self.button_columns, 2)
        self.connect(self.button_close, self.close)

    def set_navigation(self):
        # Set navigation between controls
        placed_values = self.placed.values()
        placed_keys = self.placed.keys()
        for searcher in placed_keys:

            buttons = [self.button_install, self.button_openserchset, self.button_clearstor]
            place = self.placed[searcher]

            if place[0] == 0:
                self.radiobutton[searcher].controlUp(buttons[place[1]])
            else:
                ser = placed_keys[placed_values.index((place[0] - 1, place[1]))]
                self.radiobutton[searcher].controlUp(self.radiobutton[ser])

            # self.button_columns, self.last_column_row
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

            # print str((self.button_columns, self.last_column_row))
            # print searcher

            if place == (self.button_columns, self.last_column_row) and self.last_column_row < 2:
                ser = placed_keys[placed_values.index((place[0] - 1, place[1] + 1))]
            elif place[1] == 2:
                ser = placed_keys[placed_values.index((place[0], 0))]
            else:
                ser = placed_keys[placed_values.index((place[0], place[1] + 1))]
            self.radiobutton[searcher].controlRight(self.radiobutton[ser])

            if place[0] == self.button_columns - 1 and place[1] > self.last_column_row or \
                            place[0] == self.button_columns:
                self.radiobutton[searcher].controlDown(buttons[place[1]])
            else:
                ser = placed_keys[placed_values.index((place[0] + 1, place[1]))]
                self.radiobutton[searcher].controlDown(self.radiobutton[ser])

        self.button_install.controlUp(self.radiobutton_bottom[0])
        self.button_install.controlDown(self.button_openset)
        self.button_install.controlLeft(self.button_clearstor)
        self.button_install.controlRight(self.button_openserchset)

        self.button_openserchset.controlUp(self.radiobutton_bottom[1])
        self.button_openserchset.controlDown(self.button_utorrent)
        self.button_openserchset.controlLeft(self.button_install)
        self.button_openserchset.controlRight(self.button_clearstor)

        self.button_clearstor.controlUp(self.radiobutton_bottom[2])
        self.button_clearstor.controlDown(self.button_close)
        self.button_clearstor.controlLeft(self.button_openserchset)
        self.button_clearstor.controlRight(self.button_install)

        self.button_openset.controlUp(self.button_install)
        self.button_openset.controlDown(self.radiobutton_top[0])
        self.button_openset.controlLeft(self.button_close)
        self.button_openset.controlRight(self.button_utorrent)

        self.button_utorrent.controlUp(self.button_openserchset)
        self.button_utorrent.controlDown(self.radiobutton_top[1])
        self.button_utorrent.controlLeft(self.button_openset)
        self.button_utorrent.controlRight(self.button_close)

        self.button_close.controlUp(self.button_clearstor)
        self.button_close.controlDown(self.radiobutton_top[2])
        self.button_close.controlLeft(self.button_utorrent)
        self.button_close.controlRight(self.button_openset)

        # Set initial focus
        self.setFocus(self.button_close)

    def openSettings(self):
        __settings__.openSettings()

    def openSearcherSettings(self):
        slist = Searchers().list('external').keys()
        if len(slist)>0:
            ret = xbmcgui.Dialog().select(__language__(30418), slist)
            if ret > -1 and ret < len(slist):
                sid = slist[ret]
                Searcher=xbmcaddon.Addon(id='torrenter.searcher.'+sid)
                Searcher.openSettings()
                self.close()
        else:
            xbmcgui.Dialog().ok(__language__(30415), slist)

    def installSearcher(self):
        xbmc.executebuiltin('XBMC.ActivateWindow(Addonbrowser,addons://search/%s)' % ('Torrenter Searcher'))
        self.close()

    def openUtorrent(self):
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
