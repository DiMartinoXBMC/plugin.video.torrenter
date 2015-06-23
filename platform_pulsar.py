import sys
import os

import xbmc


def get_platform():
    ret = {
        "arch": sys.maxsize > 2 ** 32 and "x64" or "x86",
    }
    if xbmc.getCondVisibility("system.platform.android"):
        ret["os"] = "android"
        if "arm" in os.uname()[4]:
            ret["arch"] = "arm"
    elif xbmc.getCondVisibility("system.platform.linux"):
        ret["os"] = "linux"
        if "arm" in os.uname()[4]:
            ret["arch"] = "arm"
    elif xbmc.getCondVisibility("system.platform.xbox"):
        system_platform = "xbox"
        ret["arch"] = ""
    elif xbmc.getCondVisibility("system.platform.windows"):
        ret["os"] = "windows"
    elif xbmc.getCondVisibility("system.platform.osx"):
        ret["os"] = "darwin"
    elif xbmc.getCondVisibility("system.platform.ios"):
        ret["os"] = "ios"
        ret["arch"] = "arm"

    ret["system"] = ''
    ret["message"] = ['', '']

    if ret["os"] == 'windows':
        ret["system"] = 'windows'
        ret["message"] = ['Windows has static compiled python-libtorrent included.',
                          'You should install "script.module.libtorrent" from "MyShows.me Kodi Repo"']
    elif ret["os"] == "linux" and ret["arch"] == "x64":
        ret["system"] = 'linux_x86_64'
        ret["message"] = ['Linux x64 has not static compiled python-libtorrent included.',
                          'You should install it by "sudo apt-get install python-libtorrent"']
    elif ret["os"] == "linux" and ret["arch"] == "x86":
        ret["system"] = 'linux_x86'
        ret["message"] = ['Linux has static compiled python-libtorrent included but it didn\'t work.',
                          'You should install it by "sudo apt-get install python-libtorrent"']
    elif ret["os"] == "linux" and ret["arch"] == "arm":
        ret["system"] = 'linux_arm'
        ret["message"] = ['As far as I know you can compile python-libtorrent for ARMv6-7.',
                          'You should search for "OneEvil\'s OpenELEC libtorrent" or use Ace Stream.']
    elif ret["os"] == "android":
        ret["system"] = 'android'
        ret["message"] = ['Please use install Ace Stream APK and choose it in Settings.',
                          'It is possible to compile python-libtorrent for Android, but I don\'t know how.']
    elif ret["os"] == "darwin":
        ret["system"] = 'darwin'
        ret["message"] = ['It is possible to compile python-libtorrent for OS X.',
                          'But you would have to do it by yourself, there is some info on github.com.']
    elif ret["os"] == "ios":
        ret["system"] = 'ios'
        ret["message"] = ['It is NOT possible to compile python-libtorrent for iOS.',
                          'But you can use torrent-client control functions.']

    return ret


PLATFORM = get_platform()
