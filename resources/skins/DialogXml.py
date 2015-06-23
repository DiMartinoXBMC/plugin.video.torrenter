# -*- coding: utf-8 -*-
import sys

import xbmcgui
import Localization
import xbmc

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92


class DialogXml(xbmcgui.WindowXMLDialog):
    def onInit(self):
        print "onInit(): Window Initialized"
        localize = Localization.localize
        color = '[COLOR %s]%s[/COLOR]'
        self.movie_label = self.getControl(32)
        self.movie_label.setText(self.movieInfo['desc'])

        if self.movieInfo.get('views'):
            self.view_label = self.getControl(34)
            self.view_label.setLabel(color % ('blue', localize('Views:')) + self.movieInfo['views'])

        self.view_label = self.getControl(35)
        self.ratingcolor = 'green'
        self.ratingint = int(self.movieInfo['rating'])
        if (self.ratingint < 70):
            self.ratingcolor = 'red'
        self.view_label.setLabel(
            color % ('blue', localize('Rating:')) + color % (self.ratingcolor, self.movieInfo['rating']))

        self.movie_label = self.getControl(1)
        self.movie_label.setLabel(self.movieInfo['title'])

        self.movie_label = self.getControl(32)
        self.movie_label.setText(self.movieInfo['desc'])

        self.poster = self.getControl(31)
        self.poster.setImage(self.movieInfo['poster'])

        self.poster = self.getControl(36)
        self.poster.setImage(self.movieInfo['kinopoisk'])
        self.getControl(22).setLabel(localize('Close'))
        self.getControl(33).setLabel(localize('Download via T-client'))
        self.getControl(30).setLabel(localize('Download via Libtorrent'))
        self.getControl(131).setLabel(localize('Play'))

        self.setFocus(self.getControl(22))

    def onAction(self, action):
        buttonCode = action.getButtonCode()
        if (action == ACTION_NAV_BACK or action == ACTION_PREVIOUS_MENU):
            self.close()
        if (buttonCode == KEY_BUTTON_BACK or buttonCode == KEY_KEYBOARD_ESC):
            self.close()

    def onClick(self, controlID):
        if (controlID == 2 or controlID == 22):
            self.close()
        if (controlID == 30):
            self.RunPlugin('downloadLibtorrent')
        if (controlID == 33):
            self.RunPlugin('downloadFilesList')
        if (controlID == 131):
            self.RunPlugin('openTorrent&external=1')

    def RunPlugin(self, action):
        if self.link:
            exec_str = 'XBMC.RunPlugin(%s)' % \
                       ('%s?action=%s&url=%s') % \
                       (sys.argv[0], action, self.link)
            xbmc.executebuiltin(exec_str)

    def onFocus(self, controlID):
        # print "onFocus(): control %i" % controlID
        pass

    def doModal(self, movieInfo, url):
        self.movieInfo = movieInfo
        self.link = url
        xbmcgui.WindowXMLDialog.doModal(self)
