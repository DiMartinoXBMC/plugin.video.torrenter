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
import gc
import xbmcaddon
from functions import log


__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__
__root__ = __settings__.getAddonInfo('path')

if (__name__ == "__main__" ):
    log(__plugin__)
    import Core

    core = Core.Core()
    if (not sys.argv[2]):
        core.sectionMenu()
    else:
        params = core.getParameters(sys.argv[2])
        core.executeAction(params)
    del core

collected = gc.collect()
log("Garbage collector: collected %d objects." % (collected))