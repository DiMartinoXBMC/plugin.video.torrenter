# -*- coding: utf-8 -*-
#
try:
    import xbmcaddon

    __settings__ = xbmcaddon.Addon("plugin.video.torrenter")
    debug = __settings__.getSetting("debug")
except:
    debug = 'true'


def Log(msg, force=False):
    try:
        print "[torrenter log] " + msg
    except UnicodeEncodeError:
        print "[torrenter log] " + msg.encode("utf-8", "ignore")


def Debug(msg, force=False):
    if debug == 'true' or force:
        try:
            print "[torrenter] " + msg
        except UnicodeEncodeError:
            print "[torrenter] " + msg.encode("utf-8", "ignore")


def Info(msg, force=False):
    if debug == 'true' or force:
        try:
            print "[torrenter] " + msg
        except UnicodeEncodeError:
            print "[torrenter] " + msg.encode("utf-8", "ignore")


def Warn(msg, force=False):
    if debug == 'true' or force:
        try:
            print "[torrenter] " + msg
        except UnicodeEncodeError:
            print "[torrenter] " + msg.encode("utf-8", "ignore")