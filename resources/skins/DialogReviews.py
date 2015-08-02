# -*- coding: utf-8 -*-

import re
import htmlentitydefs

import xbmcgui

pattern = re.compile("&(\w+?);")

def html_entity_decode_char(m, defs=htmlentitydefs.entitydefs):
    try:
        return defs[m.group(1)]
    except KeyError:
        return m.group(0)

def html_entity_decode(string):
    return pattern.sub(html_entity_decode_char, string)

KEY_BUTTON_BACK = 275
KEY_KEYBOARD_ESC = 61467
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
class DialogReviews(xbmcgui.WindowXMLDialog):
    def onInit(self):
        print "DialogReviews(): Window Initialized"
        self.reviews_box = self.getControl(32)
        self.reviews_box.setText(self.get_reviews())

        self.setFocus(self.getControl(22))

    def onAction(self, action):
        buttonCode =  action.getButtonCode()
        if (action == ACTION_NAV_BACK or action == ACTION_PREVIOUS_MENU):
            self.close()
        if (buttonCode == KEY_BUTTON_BACK or buttonCode == KEY_KEYBOARD_ESC):
            self.close()

    def onClick(self, controlID):
        if (controlID == 2 or controlID == 22):
            self.close()


    def onFocus(self, controlID):
        #print "onFocus(): control %i" % controlID
        pass


    def doModal(self, movieHtml):
        self.movieHtml = movieHtml
        xbmcgui.WindowXMLDialog.doModal(self)


    def get_reviews(self):
        reviews_texts = re.compile('<div class="comment" id="[^"]+">([^<]+)</div>',re.S).findall(self.movieHtml)
        reviews_autors = re.compile('<div class="member"><a href="[^"]+"><strong>([^<]+)</strong></a></div>',re.S).findall(self.movieHtml)
        reviews_dates = re.compile('<div class="date">([^<]+)</div>',re.S).findall(self.movieHtml)
        texts = ''
        i = 0
        for text in reviews_texts:
            texts = texts+"\n[B][COLOR purple]"+reviews_autors[i]+"[/COLOR][/B] [I]"+reviews_dates[i]+"[/I]\n"
            texts = texts+html_entity_decode(text)+"\n"
            i = i + 1
        return texts
