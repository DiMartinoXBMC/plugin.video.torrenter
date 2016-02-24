# -*- coding: utf-8 -*-
#
try:
    import xbmcaddon
    from functions import log, debug

    __settings__ = xbmcaddon.Addon("plugin.video.torrenter")
    force_debug = __settings__.getSetting("debug")
except:
    force_debug = 'true'


def Log(msg, force=False):
    log(msg)


def Debug(msg, force=False):
    if force_debug == 'true' or force:
        debug(msg, True)


def Info(msg, force=False):
    if force_debug == 'true' or force:
        debug(msg, True)


def Warn(msg, force=False):
    if force_debug == 'true' or force:
        debug(msg, True)