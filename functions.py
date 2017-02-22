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

import urllib2
import re
import socket
import datetime
import time
import sys
import os
import json
import urllib

import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import xbmcvfs
import Localization

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__language__ = __settings__.getLocalizedString
ROOT = __settings__.getAddonInfo('path')  # .decode('utf-8').encode(sys.getfilesystemencoding())
userStorageDirectory = xbmc.translatePath(__settings__.getSetting("storage"))
torrentFilesDirectory = 'torrents'
USERAGENT = "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0"
__addonpath__ = __settings__.getAddonInfo('path')
icon = os.path.join(__addonpath__, 'icon.png')
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__


def clearStorage(userStorageDirectory, force = False):
    userStorageDirectory = decode(userStorageDirectory)
    #log('[clearStorage]: storage '+str(userStorageDirectory) + os.sep)
    min_storage_size = __settings__.getSetting("min_storage_size")
    storage_size = getDirectorySizeInGB(userStorageDirectory.encode('utf-8'))
    if storage_size >= min_storage_size or force:
        if xbmcvfs.exists(userStorageDirectory + os.sep) or os.path.exists(userStorageDirectory):
            log('[clearStorage]: storage exists')
            import shutil

            temp = userStorageDirectory.rstrip('Torrenter').rstrip('/\\')
            torrents_temp, saved_temp, i = None, None, ''
            while not torrents_temp or os.path.exists(torrents_temp) or os.path.exists(saved_temp):
                torrents_temp = os.path.join(temp, 'torrents' + str(i)) + os.sep
                saved_temp = os.path.join(temp, 'Saved Files' + str(i)) + os.sep
                if i=='':
                    i=0
                else:
                    i += 1

            torrents = os.path.join(userStorageDirectory, 'torrents')
            saved = os.path.join(userStorageDirectory, 'Saved Files')
            torrents_bool, saved_bool = False, False

            if os.path.exists(torrents):
                shutil.move(torrents, torrents_temp)
                torrents_bool = True

            if os.path.exists(saved):
                shutil.move(saved, saved_temp)
                saved_bool = True

            shutil.rmtree(userStorageDirectory, ignore_errors=True)
            #log(str(xbmcvfs.listdir(userStorageDirectory)))
            xbmcvfs.mkdir(userStorageDirectory)

            if torrents_bool:
                shutil.move(torrents_temp, torrents)
            if saved_bool:
                shutil.move(saved_temp, saved)

            showMessage(Localization.localize('Storage'), Localization.localize('Storage has been cleared'))

        else:
            showMessage(Localization.localize('Storage'), Localization.localize('Does not exists'))
            log('[clearStorage]: fail storage '+userStorageDirectory + os.sep)

        try:
            DownloadDB().clear()
        except Exception, e:
            log('[clearStorage]: DownloadDB().clear() failed. '+str(e))


def sortcomma(dict, json):
    for x in dict:
        y = dict[x].split(',')
        dict[x] = ''
        for i in y:
            if i not in json:
                dict[x] = dict[x] + ',' + i
        if len(dict[x]) > 0: dict[x] = dict[x][1:len(dict[x])]
    return dict


def md5(string):
    try:
        from hashlib import md5
    except ImportError:
        from md5 import md5
    hasher = hashlib.md5()
    try:
        hasher.update(string)
    except:
        hasher.update(string.encode('utf-8', 'ignore'))
    return hasher.hexdigest()


def log(msg):
    try:
        xbmc.log("### [%s]: %s" % (__plugin__,msg,), level=xbmc.LOGNOTICE )
    except UnicodeEncodeError:
        xbmc.log("### [%s]: %s" % (__plugin__,msg.encode("utf-8", "ignore"),), level=xbmc.LOGNOTICE )
    except:
        xbmc.log("### [%s]: %s" % (__plugin__,'ERROR LOG',), level=xbmc.LOGNOTICE )


def debug(msg, forced=False):
    if getSettingAsBool('debug') and forced:
        level=xbmc.LOGNOTICE
    else:
        level=xbmc.LOGDEBUG
    try:
        xbmc.log("### [%s]: %s" % (__plugin__,msg,), level=level )
    except UnicodeEncodeError:
        xbmc.log("### [%s]: %s" % (__plugin__,msg.encode("utf-8", "ignore"),), level=level )
    except:
        xbmc.log("### [%s]: %s" % (__plugin__,'ERROR DEBUG',), level=level )


def showMessage(heading, message, times=10000, forced=False):
    if forced or not getSettingAsBool('disable_notifications'):
        xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (
            heading.replace('"', "'"), message.replace('"', "'"), times, icon))
    debug(str((heading.replace('"', "'"), message.replace('"', "'"), times, icon)))


def magnet_alert():
    showMessage('Ace Stream', Localization.localize('Does not support magnet links!'))


def dates_diff(fdate, ldate):
    try:
        if ldate == 'today':
            x = datetime.datetime.now()
        else:
            x = datetime.datetime.strptime(ldate, '%d.%m.%Y')
        y = datetime.datetime.strptime(fdate, '%d.%m.%Y')
        z = x - y
    except TypeError:
        if ldate == 'today':
            x = datetime.datetime.now()
        else:
            x = datetime.datetime(*(time.strptime(ldate, '%d.%m.%Y')[0:6]))
        y = datetime.datetime(*(time.strptime(fdate, '%d.%m.%Y')[0:6]))
        z = x - y
    return str(z.days)


def today_str():
    try:
        x = datetime.datetime.now().strftime('%d.%m.%Y')
    except TypeError:
        x = datetime.datetime(*(time.strptime(datetime.datetime.now().strftime('%d.%m.%Y'), '%d.%m.%Y')[0:6]))
        x = datetime.datetime.strftime(x, '%d.%m.%Y')
    return str(x)


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


def get_apps(paramstring=None):
    if not paramstring: paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        try:
            apps = json.loads(urllib.unquote_plus(paramstring))
        except:
            cleanapps = str(paramstring).replace('?', '', 1)
            apps = json.loads(urllib.unquote_plus(cleanapps))
        return apps


def int_xx(intxx):
    if intxx and intxx != 'None':
        return '%02d' % (int(intxx))
    else:
        return '00'


def StripName(name, list, replace=' '):
    lname = name.lower().split(' ')
    name = ''
    for n in lname:
        if n not in list: name += ' ' + n
    return name.strip()


def tempdir():
    dirname = xbmc.translatePath('special://temp')
    for subdir in ('xbmcup', 'plugin.video.torrenter'):
        dirname = os.path.join(dirname, subdir)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
    return dirname


def makeapp(s):
    return urllib.quote_plus(json.dumps(s))


def get_url(cookie, url):
    headers = {'User-Agent': 'XBMC',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Cookie': cookie}
    try:
        conn = urllib2.urlopen(urllib2.Request(url, urllib.urlencode({}), headers))
        array = conn.read()
        # debug('[get_url]: arr"'+str(array)+'"')
        if array == '':
            # debug('[get_url][2]: arr=""')
            array = True
        return array
    except urllib2.HTTPError as e:
        # debug('[get_url]: HTTPError, e.code='+str(e.code))
        if e.code == 401:
            debug('[get_url]: Denied! Wrong login or api is broken!')
            return
        elif e.code in [503]:
            debug('[get_url]: Denied, HTTP Error, e.code=' + str(e.code))
            return
        else:
            showMessage('HTTP Error', str(e.code))
            debug('[get_url]: HTTP Error, e.code=' + str(e.code))
            xbmc.sleep(2000)
            return
    except:
        return False


def post_url_json(cookie, url, post):
    headers = {'User-Agent': 'XBMC',
               'Connection': 'keep-alive',
               'Cookie': cookie}
    conn = urllib2.urlopen(urllib2.Request(url, post, headers))
    array = conn.read()
    conn.close()
    return array


def creat_db(dbfilename):
    db = sqlite.connect(dbfilename)
    cur = db.cursor()
    cur.execute('pragma auto_vacuum=1')
    cur.execute(
        'create table sources(addtime integer, filename varchar(32) PRIMARY KEY, showId integer, seasonId integer, episodeId integer, id integer, stype varchar(32))')
    cur.execute('create table cache(addtime integer, url varchar(32))')
    cur.execute('create table scan(addtime integer, filename varchar(32) PRIMARY KEY)')
    cur.execute('create table watched(addtime integer, rating integer, id varchar(32) PRIMARY KEY)')
    db.commit()
    cur.close()
    db.close()


def invert_bool(var):
    if bool(var):
        var = False
    else:
        var = True
    return var


def getSettingAsBool(setting):
    return __settings__.getSetting(setting).lower() == "true"


def calculate(full):
    consts = [(100, 20), (300, 15), (500, 10), (2000, 7), (4000, 5)]
    max_const = 150

    repl_const = 0

    for size, const in consts:
        if (size * 1024 * 1024) > full:
            repl_const = int(float(const) / 100 * (full / (1024 * 1024)))  # MB of first
            break

    if repl_const == 0:
        repl_const = max_const

    return repl_const


def getDirList(path, newl=None):
    l = []
    try:
        if not newl: dirs, newl = xbmcvfs.listdir(path)
    except:
        try:
            if not newl: dirs, newl = xbmcvfs.listdir(path.decode('utf-8').encode('cp1251'))
        except:
            showMessage(__language__(30206), __language__(30280), forced=True)
            return l
    for fl in newl:
        match = re.match('.avi|.mp4|.mkV|.flv|.mov|.vob|.wmv|.ogm|.asx|.mpg|mpeg|.avc|.vp3|.fli|.flc|.m4v',
                         fl[int(len(fl)) - 4:len(fl)], re.I)
        if match:
            l.append(fl)
    return l


def cutFileNames(l):
    from difflib import Differ

    d = Differ()

    text = sortext(l)
    newl = []
    for li in l: newl.append(cutStr(li[0:len(li) - 1 - len(li.split('.')[-1])]))
    l = newl

    text1 = cutStr(text[0][0:len(text[0]) - 1 - len(text[0].split('.')[-1])])
    text2 = cutStr(text[1][0:len(text[1]) - 1 - len(text[1].split('.')[-1])])
    sep_file = " "
    result = list(d.compare(text1.split(sep_file), text2.split(sep_file)))
    debug('[cutFileNames] ' + unicode(result))

    start = ''
    end = ''

    for res in result:
        if str(res).startswith('-') or str(res).startswith('+') or str(res).startswith('.?'):
            break
        start = start + str(res).strip() + sep_file
    result.reverse()
    for res in result:
        if str(res).startswith('-') or str(res).startswith('+') or str(res).startswith('?'):
            break
        end = sep_file + str(res).strip() + end

    newl = l
    l = []
    debug('[cutFileNames] [start] ' + start)
    debug('[cutFileNames] [end] ' + end)
    for fl in newl:
        if cutStr(fl[0:len(start)]) == cutStr(start): fl = fl[len(start):]
        if cutStr(fl[len(fl) - len(end):]) == cutStr(end): fl = fl[0:len(fl) - len(end)]
        try:
            isinstance(int(fl.split(sep_file)[0]), int)
            fl = fl.split(sep_file)[0]
        except:
            pass
        l.append(fl)
    debug('[cutFileNames] [sorted l]  ' + unicode(sorted(l, key=lambda x: x)))
    return l


def cutStr(s):
    return s.replace('.', ' ').replace('_', ' ').replace('[', ' ').replace(']', ' ').lower().strip()


def sortext(filelist):
    result = {}
    for name in filelist:
        ext = name.split('.')[-1]
        try:
            result[ext] = result[ext] + 1
        except:
            result[ext] = 1
    lol = result.iteritems()
    lol = sorted(lol, key=lambda x: x[1])
    debug('[sortext]: lol:' + str(lol))
    popext = lol[-1][0]
    result, i = [], 0
    for name in filelist:
        if name.split('.')[-1] == popext:
            result.append(name)
            i = i + 1
    result = sweetpair(result)
    debug('[sortext]: result:' + str(result))
    return result


def cutFolder(contentList, tdir=None):
    dirList, contentListNew = [], []

    if len(contentList) > 1:
        common_folder = contentList[0][0]
        debug('[cutFolder]: common_folder '+common_folder)
        if '\\' in common_folder:
            common_folder = common_folder.split('\\')[0]
        elif '/' in common_folder:
            common_folder = common_folder.split('/')[0]

        common = True
        for item in contentList:
            if common_folder not in item[0]:
                common = False
                break

        for item in contentList:
            dir = None
            if common:
                item[0] = item[0][len(common_folder) + 1:]

            #debug('[cutFolder]: item[0] '+item[0])

            if '\\' in item[0]:
                dir = item[0].split('\\')[0]
            elif '/' in item[0]:
                dir = item[0].split('/')[0]
            elif not tdir:
                contentListNew.append(item)

            if tdir and ensure_str(dir) == ensure_str(tdir):
                tupleContent = list(item)
                tupleContent[0] = item[0][len(dir) + 1:]
                contentListNew.append(list(tupleContent))

            if not tdir and dir and dir not in dirList:
                dirList.append(dir)

        debug('[cutFolder]: dirList, contentListNew '+str(dirList)+str(contentListNew))
        return dirList, contentListNew
    else:
        debug('[cutFolder]: dirList, contentList '+str(dirList)+str(contentList))
        return dirList, contentList


def sweetpair(l):
    from difflib import SequenceMatcher

    s = SequenceMatcher()
    ratio = []
    for i in range(0, len(l)): ratio.append(0)
    for i in range(0, len(l)):
        for p in range(0, len(l)):
            s.set_seqs(l[i], l[p])
            ratio[i] = ratio[i] + s.quick_ratio()
    id1, id2 = 0, 0
    for i in range(0, len(l)):
        if ratio[id1] <= ratio[i] and i != id2 or id2 == id1 and ratio[id1] == ratio[i]:
            id2 = id1
            id1 = i
            # debug('1 - %d %d' % (id1, id2))
        elif (ratio[id2] <= ratio[i] or id1 == id2) and i != id1:
            id2 = i
            # debug('2 - %d %d' % (id1, id2))

    debug('[sweetpair]: id1 ' + l[id1] + ':' + str(ratio[id1]))
    debug('[sweetpair]: id2 ' + l[id2] + ':' + str(ratio[id2]))

    return [l[id1], l[id2]]


def FileNamesPrepare(filename):
    my_season = None
    my_episode = None

    try:
        if int(filename):
            my_episode = int(filename)
            debug('[FileNamesPrepare] ' + str([my_season, my_episode, filename]))
            return [my_season, my_episode, filename]
    except:
        pass

    urls = ['s(\d+)e(\d+)', '(\d+)[x|-](\d+)', 'E(\d+)', 'Ep(\d+)', '\((\d+)\)']
    for file in urls:
        match = re.compile(file, re.DOTALL | re.I | re.IGNORECASE).findall(filename)
        if match:
            try:
                my_episode = int(match[1])
                my_season = int(match[0])
            except:
                try:
                    my_episode = int(match[0])
                except:
                    try:
                        my_episode = int(match[0][1])
                        my_season = int(match[0][0])
                    except:
                        try:
                            my_episode = int(match[0][0])
                        except:
                            break
            if my_season and my_season > 100: my_season = None
            if my_episode and my_episode > 365: my_episode = None
            debug('[FileNamesPrepare] ' + str([my_season, my_episode, filename]))
            return [my_season, my_episode, filename]


def filename2match(filename, no_date=False):
    results = {'label': filename}
    urls = ['(.+|.?)s(\d+)e(\d+)', '(.+|.?)s(\d+)\.e(\d+)', '(.+|.?) [\[|\(](\d+)[x|-](\d+)[\]|\)]',
            '(.+|.?) (\d+)[x|-](\d+)']  # same in service
    for file in urls:
        match = re.compile(file, re.I | re.IGNORECASE).findall(filename)
        # print str(results)
        if match:
            results['showtitle'], results['season'], results['episode'] = match[0]
            results['showtitle'] = results['showtitle'].replace('.', ' ').replace('_', ' ').strip().replace(
                'The Daily Show', 'The Daily Show With Jon Stewart')
            results['season'], results['episode'] = int(results['season']), int(results['episode'])
            # debug('[filename2match] '+str(results))
            return results
    if no_date: return
    urls = ['(.+)(\d{4})\.(\d{2,4})\.(\d{2,4})', '(.+)(\d{4}) (\d{2}) (\d{2})']  # same in service
    for file in urls:
        match = re.compile(file, re.I | re.IGNORECASE).findall(filename)
        if match:
            results['showtitle'] = match[0][0].replace('.', ' ').strip().replace('The Daily Show',
                                                                                 'The Daily Show With Jon Stewart')
            results['date'] = '%s.%s.%s' % (match[0][3], match[0][2], match[0][1])
            debug('[filename2match] ' + str(results))
            return results


def TextBB(string, action=None, color=None):
    if action == 'b':
        string = '[B]' + string + '[/B]'
    return string


def jstr(s):
    if not s:
        s = 'null'
    elif not unicode(s).isnumeric():
        s = '"%s"' % (s)
    return str(s)


def view_style(func):
    styles = {}
    num_skin = 0
    view_style = int(__settings__.getSetting("skin_optimization"))
    if view_style in [3, 2, 6]:
        styles['searchOption'] = styles['History'] = styles['List'] = 'info'
        styles['drawContent'] = styles['drawtrackerList'] = styles['drawcontentList'] = 'info'
        styles['sectionMenu'] = styles['Seasons'] = 'list'
        styles['uTorrentBrowser'] = styles['torrentPlayer'] = styles['openTorrent'] = 'wide'
        styles['showFilesList'] = styles['DownloadStatus'] = 'wide'
    elif view_style in [1, 4, 5, 7]:
        styles['searchOption'] = 'info'
        styles['drawContent'] = styles['torrentPlayer'] = styles['openTorrent'] = styles['drawtrackerList'] = 'info'
        styles['uTorrentBrowser'] = styles['History'] = styles['DownloadStatus'] = 'wide'
        styles['showFilesList'] = styles['sectionMenu'] = 'wide'
        styles['List'] = styles['drawcontentList'] = 'info3'

    if view_style in [1, 7]:
        styles['uTorrentBrowser'] = styles['torrentPlayer'] = 'wide'
        styles['openTorrent'] = styles['History'] = styles['DownloadStatus'] = 'wide'
        styles['sectionMenu'] = 'icons'
    elif view_style == 5:
        styles['uTorrentBrowser'] = styles['torrentPlayer'] = 'wide'
        styles['openTorrent'] = styles['History'] = styles['DownloadStatus'] = 'wide'
        styles['drawtrackerList'] = styles['drawContent'] = styles['List'] = styles['sectionMenu'] = 'list'
        styles['searchOption'] = 'info'

    if view_style == 8:
        styles['sectionMenu'] = 'thumbnails'  #меню
        styles['List'] = 'biglist'
        styles['Seasons'] = 'biglist'
        styles['uTorrentBrowser'] = 'biglist'
        styles['torrentPlayer'] = 'biglist'
        styles['openTorrent'] = 'biglist'
        styles['History'] = 'biglist' #история поиска
        styles['DownloadStatus'] = 'biglist' #статус загрузки
        styles['drawtrackerList'] = 'biglist'
        styles['drawContent'] = 'list' #списки медиа
        styles['drawcontentList'] = 'extrainfo' #списки медиа - лист
        styles['searchOption'] = 'biglist'
        styles['showFilesList'] = 'biglist'


    if view_style in [1, 3, 4, 5]:
        num_skin = 0
    elif view_style == 2:
        num_skin = 1
    elif view_style == 6:
        num_skin = 2
    elif view_style == 7:
        num_skin = 3
    if view_style == 8:
        num_skin = 4

    style = styles.get(func)
    log('[view_style]: lock '+str(style)+' for '+str(func))
    lockView(style, num_skin)


def lockView(viewId='info', num_skin=0):
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    skinOptimizations = (
        {'list': 50, 'info': 50, 'wide': 51, 'icons': 500, 'info3': 515, },  # Confluence
        {'list': 50, 'info': 51, 'wide': 52, 'icons': 53, },  # Transperency!
        {'list': 55, 'info': 55, 'wide': 55, 'icons': 55, 'info3': 55, },  # Aeon Nox
        {'list': 50, 'info': 54, 'wide': 55, 'icons': 54, 'info3': 500, },  # Estuary
        {'list': 50, 'bigwide': 51, 'biglist': 52, 'poster': 53, 'banner': 54, 'wall': 55, 'mediainfo': 56, 'extrainfo': 57, "cards":58, "bannerwall":59, 'thumbnails': 500, 'postersquare': 503, 'wallsquare': 505, },  # Arctic: Zephyr
    )
    try:
        if viewId == 'wide' and num_skin == 3:
            xbmcplugin.setContent(int(sys.argv[1]), 'files')
        xbmc.executebuiltin("Container.SetViewMode(%s)" % str(skinOptimizations[num_skin][viewId]))
    except:
        return

    ''' Estuary
                <include>View_50_List</include>
                <include>View_51_Poster</include>
                <include>View_52_IconWall</include>
                <include>View_53_Shift</include>
                <include>View_54_InfoWall</include>
                <include>View_55_WideList</include>
                <include>View_500_SmallThumb</include>
                <include>View_501_Banner</include>
                <include>View_502_FanArt</include>
    '''
    '''
            <include>PosterWrapView2_Fanart</include> <!-- view id = 508 -->
            <include>MediaListView3</include> <!-- view id = 503 -->
            <include>MediaListView2</include> <!-- view id = 504 -->
            <include>MediaListView4</include> <!-- view id = 515 -->
            <include>WideIconView</include> <!-- view id = 505 -->
            <include>MusicVideoInfoListView</include> <!-- view id = 511 -->
            <include>AddonInfoListView1</include> <!-- view id = 550 -->
            <include>AddonInfoThumbView1</include> <!-- view id = 551 -->
            <include>LiveTVView1</include> <!-- view id = 560 -->
    '''


def torrent_dir():
    from resources.utorrent.net import Download

    socket.setdefaulttimeout(3)
    list = Download().list()
    ret = 0
    if list and len(list) > 0:
        dirs = ["Keyboard"]
        for dl in list:
            if dl['dir'] not in dirs:
                dirs.append(dl['dir'])
            basename = os.path.dirname(dl['dir'])
            if basename not in dirs:
                dirs.append(basename)
            else:
                dirs.remove(basename)
                dirs.insert(1, basename)

        dialog = xbmcgui.Dialog()
        ret = dialog.select(Localization.localize('Manual Torrent-client Path Edit'), dirs)
    else:
        ret = 0

    if ret == 0:
        KB = xbmc.Keyboard()
        KB.setHeading(Localization.localize('Manual Torrent-client Path Edit'))
        KB.setDefault(__settings__.getSetting("torrent_dir"))
        KB.doModal()
        if (KB.isConfirmed()):
            __settings__.setSetting("torrent_dir", KB.getText())
    elif ret > 0:
        __settings__.setSetting("torrent_dir", dirs[ret])


def saveCheckPoint():
    __settings__.setSetting("checkpoint", str(sys.argv[2]))


def gotoCheckPoint():
    xbmc.executebuiltin(
        'XBMC.ActivateWindow(Videos,plugin://plugin.video.myshows/%s)' % (__settings__.getSetting("checkpoint")))


def smbtopath(path):
    x = path.split('@')
    if len(x) > 1:
        path = x[1]
    else:
        path = path.replace('smb://', '')
    debug('[smbtopath]:' + '\\\\' + path.replace('/', '\\'))
    return '\\\\' + path.replace('/', '\\')


def PrepareFilename(filename):
    badsymb = [':', '"', '\\', '/', '\'', '!', ['&', 'and'], '*', '?', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ',
               '  ',
               '  ', '  ']
    for b in badsymb:
        if not isinstance(b, list):
            filename = filename.replace(b, ' ')
        else:
            filename = filename.replace(b[0], b[1])
    return filename.rstrip('. ')


def PrepareSearch(filename):
    titles = [filename]
    rstr = '. -'
    badsymb = [':', '"', r'\\', '/', r'\'', '!', '&', '*', '_', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ', '  ',
               '  ', '  ']
    for b in badsymb:
        filename = filename.replace(b, ' ')

    filename = re.sub("\([^)]*\)([^(]*)", "\\1", filename)
    filename = re.sub("\[[^\]]*\]([^\[]*)", "\\1", filename)
    filename = filename.strip().rstrip(rstr)

    if titles[0] != filename and filename != '': titles.insert(0, filename)

    title_array = [(u'(.+?)(Cезон|cезон|Сезон|сезон|Season|season|СЕЗОН|SEASON)', titles[0], 0),
                   (u'(.+?)[sS](\d{1,2})', titles[0].replace('.', ' '), 0),
                   ]
    for regex, title, i in title_array:
        recomp = re.compile(regex)
        match = recomp.findall(title)
        if match:
            titles.insert(0, match[0][i].rstrip(rstr))

    return titles


def isRemoteTorr():
    localhost = ['127.0.0.1', '0.0.0.0', 'localhost']
    if __settings__.getSetting("torrent") == '0':
        if __settings__.getSetting("torrent_utorrent_host") not in localhost:
            debug('[isRemoteTorr]: uTorrent is Remote!')
            return True
    elif __settings__.getSetting("torrent") == '1':
        if __settings__.getSetting("torrent_transmission_host") not in localhost:
            debug('[isRemoteTorr]: Transmission is Remote!')
            return True


def changeDBTitle(showId):
    from utilities import xbmcJsonRequest

    shows = xbmcJsonRequest(
        {'jsonrpc': '2.0', 'method': 'VideoLibrary.GetTVShows', 'params': {'properties': ['title']}, 'id': 0})

    if not shows:
        debug('[changeDBTitle]: XBMC JSON Result was empty.')
        return

    if 'tvshows' in shows:
        shows = shows['tvshows']
        debug("[changeDBTitle]: XBMC JSON Result: '%s'" % str(shows))
    else:
        debug("[changeDBTitle]: Key 'tvshows' not found")
        return

    if len(shows) > 0:
        newtitle = id2title(showId, None, True)[0].decode('utf-8', 'ignore')
        dialog = xbmcgui.Dialog()
        dialog_items, dialog_ids = [__language__(30205)], [-1]
        shows = sorted(shows, key=lambda x: x['tvshowid'], reverse=True)
        for show in shows:
            dialog_ids.append(show['tvshowid'])
            dialog_items.append(show['title'])

        ret = dialog.select(newtitle, dialog_items)
        if ret > 0:
            ok = dialog.yesno(__language__(30322), __language__(30534),
                              __language__(30535) % (dialog_items[ret], newtitle))
            if ok:
                result = xbmcJsonRequest({'jsonrpc': '2.0', 'method': 'VideoLibrary.SetTVShowDetails',
                                          'params': {'tvshowid': int(dialog_ids[ret]), 'title': unicode(newtitle)},
                                          'id': 1})
                if result in [newtitle, 'OK']:
                    showMessage(__language__(30208), __language__(30536) % (newtitle), forced=True)
                else:
                    debug("[changeDBTitle]: XBMC JSON Result: '%s'" % str(result))
        return


class TimeOut():
    def __init__(self):
        self.scan = CacheDB('web_timeout')
        self.gone_online = CacheDB('go_online')
        self.get = self.scan.get()
        self.online = 30
        self.offline = 1

    def go_offline(self, manual=False):
        gone_online = self.gone_online.get()
        if gone_online:
            gone_online = int(gone_online)
        else:
            gone_online = 0
        if not manual:
            if gone_online and gone_online + self.online >= int(round(time.time())):
                debug('[TimeOut]: too soon to go back offline! %d s' % (
                    (gone_online + self.online * 4) - int(round(time.time()))))
                return
        if self.timeout() == self.online:
            debug('[TimeOut]: Gone offline! %d s' % ((gone_online + self.online * 4) - int(round(time.time()))))
            showMessage(__language__(30520), __language__(30545) % (self.offline))
            if self.get: self.scan.delete()
            self.scan.add()

    def go_online(self):
        if self.get:
            self.scan.delete()
            debug('[TimeOut]: Gone online!')
            showMessage(__language__(30521), __language__(30545) % (self.online))
            if self.gone_online.get():
                self.gone_online.delete()
            self.gone_online.add()

    def timeout(self):
        if self.get and int(time.time()) - self.get < refresh_period * 3600:
            to = self.offline
        else:
            to = self.online
        # debug('[TimeOut]: '+str(to))
        return to


class ListDB:
    def __init__(self, version=1.0):
        self.dbname = 'list' + '.db3'
        dirname = xbmc.translatePath('special://temp')
        self.dbfilename = os.path.join(dirname, 'xbmcup',
                                       __settings__.getAddonInfo('id').replace('plugin://', '').replace('/', ''),
                                       self.dbname)
        self.version = version
        if not xbmcvfs.exists(self.dbfilename):
            self.creat_db()

    def creat_db(self):
        self._connect()
        self.cur.execute('pragma auto_vacuum=1')
        self.cur.execute('create table db_ver(version real)')
        # self.cur.execute('create table list(addtime integer PRIMARY KEY, title varchar(32), originaltitle varchar(32)'
        #            ', year integer, category varchar(32), subcategory varchar(32))')
        self.cur.execute('create table list(addtime integer PRIMARY KEY, info varchar(32))')
        self.cur.execute('insert into db_ver(version) values(?)', (self.version,))
        self.db.commit()
        self._close()

    def get(self, addtime):
        self._connect()
        self.cur.execute('select info from list where addtime="' + addtime + '"')
        x = self.cur.fetchone()
        self._close()
        return x[0] if x else None

    def get_all(self):
        self._connect()
        # self.cur.execute('select addtime,title,originaltitle,year,category,subcategory from list')
        self.cur.execute('select addtime,info from list')
        x = self.cur.fetchall()
        self._close()
        return x if x else None

    def add(self, url):
        self._connect()
        self.cur.execute('insert into list(addtime,info)'
                         ' values(?,?)', (int(time.time()), url))
        self.db.commit()
        self._close()

    def delete(self, addtime):
        self._connect()
        self.cur.execute('delete from list where addtime="' + addtime + '"')
        self.db.commit()
        self._close()

    def _connect(self):
        self.db = sqlite.connect(self.dbfilename)
        self.cur = self.db.cursor()

    def _close(self):
        self.cur.close()
        self.db.close()


class HistoryDB:
    def __init__(self, version=1.1):
        self.name = 'history.db3'
        self.version = version

    def get_all(self):
        self._connect()
        self.cur.execute('select addtime,string,fav from history order by addtime DESC')
        x = self.cur.fetchall()
        self._close()
        return x if x else None

    def get(self, url):
        self._connect()
        self.cur.execute('select string from history where string="' + url + '"')
        x = self.cur.fetchone()
        self._close()
        return x[0] if x else None

    def get_providers(self, addtime):
        self._connect()
        self.cur.execute('select providers from history where addtime="' + addtime + '"')
        x = self.cur.fetchone()
        self._close()
        return x[0].split(',') if x and x[0] != '' else None

    def set_providers(self, addtime, providers):
        self._connect()
        if isinstance(providers, dict):
            temp = []
            for i in providers.keys():
                if providers.get(i):
                    temp.append(i)
            providers = temp
        str_p = ','.join(providers)
        self.cur.execute('UPDATE history SET providers = "' + str_p + '" where addtime=' + addtime)
        self.db.commit()
        self._close()

    def change_providers(self, addtime, searcher):
        #self._connect()
        providers = self.get_providers(addtime)
        keys = Searchers().dic().keys()
        if providers and len(providers) > 0:
            if searcher in providers:
                providers.remove(searcher)
            else:
                providers.append(searcher)
            for i in providers:
                if i not in keys:
                    providers.remove(i)
            self.set_providers(addtime, providers)
            #self.db.commit()
            #self._close()

    def add(self, url):
        self._connect()
        self.cur.execute('select fav from history where string="' + url + '"')
        x = self.cur.fetchone()
        if x: x = int(x[0])
        fav = True if x else False
        if not fav:
            self.cur.execute('delete from history where string="' + decode(url) + '"')
            self.cur.execute('insert into history(addtime,string,fav,providers)'
                             ' values(?,?,?,?)', (int(time.time()), decode(url), 0, ""))
        self.db.commit()
        self._close()

    def update(self, addtime, fav):
        self._connect()
        self.cur.execute('UPDATE history SET fav = ' + str(fav) + ' where addtime=' + addtime)
        self.db.commit()
        self._close()

    def fav(self, addtime):
        self.update(addtime, fav=1)

    def unfav(self, addtime):
        self.update(addtime, fav=0)

    def delete(self, addtime):
        self._connect()
        self.cur.execute('delete from history where addtime="' + addtime + '"')
        self.db.commit()
        self._close()

    def clear(self):
        self._connect()
        self.cur.execute('delete from history where fav=0')
        self.db.commit()
        self._close()

    def _connect(self):
        dirname = xbmc.translatePath('special://temp')
        for subdir in ('xbmcup', 'plugin.video.torrenter'):
            dirname = os.path.join(dirname, subdir)
            if not xbmcvfs.exists(dirname):
                xbmcvfs.mkdir(dirname)

        self.filename = os.path.join(dirname, self.name)

        first = False
        if not xbmcvfs.exists(self.filename):
            first = True

        self.db = sqlite.connect(self.filename, check_same_thread=False)
        if not first:
            self.cur = self.db.cursor()
            try:
                self.cur.execute('select version from db_ver')
                row = self.cur.fetchone()
                if not row or float(row[0]) != self.version:
                    self.cur.execute('drop table history')
                    self.cur.execute('drop table if exists db_ver')
                    first = True
                    self.db.commit()
                    self.cur.close()
            except:
                self.cur.execute('drop table history')
                first = True
                self.db.commit()
                self.cur.close()

        if first:
            cur = self.db.cursor()
            cur.execute('pragma auto_vacuum=1')
            cur.execute('create table db_ver(version real)')
            cur.execute(
                'create table history(addtime integer PRIMARY KEY, string varchar(32), providers varchar(32), fav integer)')
            cur.execute('insert into db_ver(version) values(?)', (self.version,))
            self.db.commit()
            cur.close()
            self.cur = self.db.cursor()

    def _close(self):
        self.cur.close()
        self.db.close()


class WatchedHistoryDB:
    def __init__(self, version=1.3):
        self.name = 'watched_history.db3'
        self.version = version
        self.history_bool = __settings__.getSetting('history') == 'true'

    def get_all(self):
        self._connect()
        self.cur.execute('select addtime,filename,foldername,path,url,seek,length,ind,size from history order by addtime DESC')
        x = self.cur.fetchall()
        self._close()
        return x if x else None

    def get(self, get, by, equal):
        self._connect()
        self.cur.execute('select '+get+' from history where '+by+'="' + equal + '"')
        x = self.cur.fetchone()
        self._close()
        return x if x else None

    def getbypathind(self, path, ind):
        self._connect()
        self.cur.execute('select seek from history where path="' + path + '" AND ind=' + ind)
        x = self.cur.fetchone()
        self._close()
        return x if x else None

    def add(self, filename, path, foldername = None, seek = 0, length = 1, ind = 0, size = 0):
        try:
            watchedPercent = int((float(seek) / float(length if length else 1)) * 100)
        except:
            watchedPercent = 0
        max_history_add = int(__settings__.getSetting('max_history_add'))
        if self.history_bool and watchedPercent <= max_history_add:
            self._connect()
            url = __settings__.getSetting("lastTorrentUrl")
            #path = __settings__.getSetting("lastTorrent")
            if not foldername:
                foldername = ''
            self.cur.execute('delete from history where filename="' + decode(filename) + '"')
            self.cur.execute('insert into history(addtime,filename,foldername,path,url,seek,length,ind,size)'
                                 ' values(?,?,?,?,?,?,?,?,?)', (int(time.time()), decode(filename), decode(foldername), decode(path),
                                                      decode(url), str(int(seek)), str(int(length)), str(ind), str(size)))
            self.db.commit()
            self._close()

    def update(self, what, to, by, equal):
        self._connect()
        self.cur.execute('UPDATE history SET '+what+' = ' + to + ' where '+by+'=' + equal)
        self.db.commit()
        self._close()

    def delete(self, addtime):
        self._connect()
        self.cur.execute('delete from history where addtime="' + addtime + '"')
        self.db.commit()
        self._close()

    def clear(self):
        self._connect()
        self.cur.execute('delete from history')
        self.db.commit()
        self._close()

    def _connect(self):
        dirname = xbmc.translatePath('special://temp')
        for subdir in ('xbmcup', 'plugin.video.torrenter'):
            dirname = os.path.join(dirname, subdir)
            if not xbmcvfs.exists(dirname):
                xbmcvfs.mkdir(dirname)

        self.filename = os.path.join(dirname, self.name)

        first = False
        if not xbmcvfs.exists(self.filename):
            first = True

        self.db = sqlite.connect(self.filename, check_same_thread=False)
        if not first:
            self.cur = self.db.cursor()
            try:
                self.cur.execute('select version from db_ver')
                row = self.cur.fetchone()
                if not row or float(row[0]) != self.version:
                    self.cur.execute('drop table history')
                    self.cur.execute('drop table if exists db_ver')
                    first = True
                    self.db.commit()
                    self.cur.close()
            except:
                self.cur.execute('drop table history')
                first = True
                self.db.commit()
                self.cur.close()

        if first:
            cur = self.db.cursor()
            cur.execute('pragma auto_vacuum=1')
            cur.execute('create table db_ver(version real)')
            cur.execute(
                'create table history(addtime integer PRIMARY KEY, filename varchar(32), foldername varchar(32), path varchar(32), url varchar(32), seek integer, length integer, ind integer, size integer)')
            cur.execute('insert into db_ver(version) values(?)', (self.version,))
            self.db.commit()
            cur.close()
            self.cur = self.db.cursor()

    def _close(self):
        self.cur.close()
        self.db.close()

class Searchers():
    def __init__(self):
        pass

    def getBoolSetting(self, setting):
        return __settings__.getSetting(setting).lower() == "true"

    def setBoolSetting(self, setting, bool=True):
        __settings__.setSetting(setting, "true" if bool else "false")

    def list(self, only=None):
        searchersDict = {}
        if only!='external':
            searchers_dir = os.path.join(ROOT, 'resources', 'searchers')
            searchers_dirList=xbmcvfs.listdir(searchers_dir)[1]
            for searcherFile in searchers_dirList:
                if re.match('^(\w+)\.py$', searcherFile):
                    name=searcherFile.replace('.py', '')
                    searchersDict[name]={'name':name,
                                         'path':searchers_dir,
                                         'searcher':os.path.join(searchers_dir,name+'.py'),
                                         'type':'local'}
        if only!='local':
            addons_dir = os.path.join(xbmc.translatePath('special://home'),'addons')
            addons_dirsList = xbmcvfs.listdir(addons_dir)[0]
            for searcherDir in addons_dirsList:
                #if len(searchersDict)>1: break
                if re.match('^torrenter\.searcher\.(\w+)$', searcherDir):
                    name=searcherDir.replace('torrenter.searcher.', '')
                    path=os.path.join(addons_dir, searcherDir)
                    searchersDict[name]={'name':name,
                                         'path':path,
                                         'searcher':os.path.join(path,name+'.py'),
                                         'type':'external'}
        return searchersDict

    def dic(self, providers=[]):
        dic = {}
        for searcher in self.list():
            if not providers:
                dic[searcher] = self.old(searcher)
            else:
                dic[searcher] = searcher in providers
        return dic

    def old(self, searcher):
        if not self.getBoolSetting('old_' + searcher):
            self.setBoolSetting('old_' + searcher)
            self.setBoolSetting(searcher)
        return self.getBoolSetting(searcher)

    def get_active(self):
        get_active = []
        for searcher in self.list().keys():
            if self.old(searcher): get_active.append(searcher + '.py')
        log('Active Searchers: ' + str(get_active))
        return get_active

    def searchWithSearcher(self, keyword, searcher):
        import traceback
        filesList = []
        slist = self.list()
        if slist[searcher]['path'] not in sys.path:
            sys.path.insert(0, slist[searcher]['path'])
            log('Added %s in sys.path' % (slist[searcher]['path']))
        try:
            searcherObject = getattr(__import__(searcher), searcher)
            filesList = searcherObject().search(keyword)
            del searcherObject
        except Exception, e:
            log('Unable to use searcher: ' + searcher + ' at ' + __plugin__ + ' searchWithSearcher(). Exception: ' + str(e))
            log(traceback.format_exc())
        return filesList

    def downloadWithSearcher(self, url, searcher):
        slist = Searchers().list()
        if slist[searcher]['path'] not in sys.path:
            sys.path.insert(0, slist[searcher]['path'])
            log('Added %s in sys.path' % (slist[searcher]['path']))
        try:
            searcherObject = getattr(__import__(searcher), searcher)()
            url = searcherObject.getTorrentFile(url)
        except Exception, e:
            log('Unable to use searcher: ' + searcher + ' at ' + __plugin__ + ' downloadWithSearcher(). Exception: ' + str(e))
        return url

    def checkExist(self, searcher):
        if searcher not in self.list():
            yes=xbmcgui.Dialog().yesno('< %s >' % Localization.localize('Torrenter Tracker Install'),
                                        Localization.localize('Torrenter didn\'t find %s searcher' % searcher),
                                        Localization.localize('Would you like to install %s from "MyShows.me Kodi Repo" in Programs section?') % searcher,)
            if yes:
                xbmc.executebuiltin('Dialog.Close(all,true)')
                xbmc.executebuiltin('XBMC.ActivateWindow(Addonbrowser,addons://search/%s)' % ('Torrenter Searcher %s' % searcher))

    def activeExternal(self):
        slist = []
        for searcher in self.list('external').keys():
            if self.old(searcher): slist.append(searcher)
        return slist


def search(url, searchersList, isApi=None):
    from threading import Thread
    try:
        from Queue import Queue, Empty
    except ImportError:
        from queue import Queue, Empty

    num_threads=__settings__.getSetting('num_threads')
    if num_threads and int(num_threads)>0:
        num_threads = int(num_threads)
    else:
        num_threads = 3
    queue = Queue()
    result = {}
    iterator, filesList, left_searchers = 0, [], []
    timeout_multi=int(sys.modules["__main__"].__settings__.getSetting("timeout"))
    wait_time=10+(10*timeout_multi)
    left_searchers.extend(searchersList)
    if not isApi:
        progressBar = xbmcgui.DialogProgress()
        progressBar.create(Localization.localize('Please Wait'), Localization.localize('Materials are loading now.'))

    class CleanExit:
        pass

    def search_one(i, q):
        while True:
            try:
                if not isApi and progressBar.iscanceled():
                    progressBar.update(0)
                    progressBar.close()
                    return
                iterator=100*int(len(searchersList)-len(left_searchers))/len(searchersList)
                if not isApi:
                    progressBar.update(int(iterator), join_list(left_searchers, replace='.py'))
                searcherFile = q.get_nowait()
                if searcherFile == CleanExit:
                    return
                searcher=searcherFile.replace('.py','')
                log("Thread %s: Searching at %s" % (i, searcher))
                result[searcherFile]=Searchers().searchWithSearcher(url, searcher)
                left_searchers.remove(searcherFile)
                q.task_done()
            except Empty:
                pass

    workers=[]
    for i in range(num_threads):
        worker = Thread(target=search_one, args=(i, queue))
        worker.setDaemon(True)
        worker.start()
        workers.append(worker)

    for searcherFile in searchersList:
        queue.put(searcherFile)

    log("Main Thread Waiting")
    queue.join()
    for i in range(num_threads):
        queue.put(CleanExit)

    log("Main Thread Waiting for Threads")
    for w in workers:
        w.join()

    log("Done")

    if not isApi:
        progressBar.update(0)
        progressBar.close()

    for k in result.keys():
        if result.get(k):
            filesList.extend(result[k])
    return filesList

def get_filesList(query, searchersList, addtime = None):
    if __settings__.getSetting('history')=='true':
        HistoryDB().add(query)

    filesList=search(query, searchersList)
    if __settings__.getSetting('sort_search')=='true':
        __settings__.setSetting('sort_search','1')
    if int(__settings__.getSetting('sort_search'))==0:
        filesList = sorted(filesList, key=lambda x: x[0], reverse=True)
    elif int(__settings__.getSetting('sort_search'))==2:
        filesList = sorted(filesList, key=lambda x: x[4], reverse=False)

    debug('get_filesList filesList: '+str(filesList))

    return filesList

def get_searchersList(addtime = None):
    searchersList = []
    if addtime:
        providers=HistoryDB().get_providers(addtime)
        if providers:
            for searcher in providers:
                searchersList.append(searcher)
    if not addtime or not searchersList:
        searchersList = Searchers().get_active()

    debug('get_searchersList: '+str(searchersList))

    return searchersList

def get_contentList(url):
    import Downloader

    url = urllib.unquote_plus(url)
    debug('0' + __settings__.getSetting("lastTorrent"))

    __settings__.setSetting("lastTorrentUrl", url)
    classMatch = re.search('(\w+)::(.+)', url)
    if classMatch:
        searcher = classMatch.group(1)
        url = Searchers().downloadWithSearcher(classMatch.group(2), searcher)
        __settings__.setSetting("lastTorrent", url)

    torrent = Downloader.Torrent(userStorageDirectory, url, torrentFilesDirectory=torrentFilesDirectory)

    debug('1'+__settings__.getSetting("lastTorrent"))
    filename = torrent.saveTorrent(url)
    __settings__.setSetting("lastTorrent", filename)
    debug('2'+__settings__.getSetting("lastTorrent"))

    append_filesize = __settings__.getSetting("append_filesize") == 'true'

    contentList = []
    for filedict in torrent.getContentList():
        fileTitle = filedict.get('title')
        size = filedict.get('size')
        if size:
            if append_filesize:
                fileTitle += ' [%d MB]' % (size / 1024 / 1024)

        contentList.append([unescape(fileTitle), str(filedict.get('ind')), size])
    # contentList = sorted(contentList, key=lambda x: x[0])

    debug('get_contentList contentList: ' + str(contentList))

    return contentList, filename

def join_list(l, char=', ', replace=''):
    string=''
    for i in l:
        string+=i.replace(replace,'')+char
    return string.rstrip(' ,')


class Contenters():
    def __init__(self):
        pass

    def first_time(self, scrapperDB_ver, language='ru'):
        from resources.scrapers.scrapers import Scrapers
        if language not in ['en','ru','he']:
            language = 'ru'
        searcher = 'metadata'
        redl = False
        scrapperDB_ver = scrapperDB_ver[language]
        if scrapperDB_ver != __settings__.getSetting('scrapperDB_ver' + language) and self.getBoolSetting(searcher):
            __settings__.setSetting('scrapperDB_ver' + language, scrapperDB_ver)
            ok = xbmcgui.Dialog().yesno('< %s >' % Localization.localize('Content Lists'),
                                        Localization.localize('Your preloaded databases are outdated!'),
                                        Localization.localize('Do you want to download new ones right now?'))
            if ok:
                dirname = xbmc.translatePath('special://temp')
                dirname = os.path.join(dirname, 'xbmcup', 'plugin.video.torrenter')
                scrapers = {'tvdb': 'TheTVDB.com', 'tmdb': 'TheMovieDB.org', 'kinopoisk': 'KinoPoisk.ru'}
                for i in scrapers.keys():
                    xbmcvfs.delete(os.path.join(dirname, i + '.' + language + '.db'))
                showMessage(Localization.localize('Reset All Cache DBs'), Localization.localize('Deleted!'))
                redl = True
            else:
                xbmcgui.Dialog().ok('< %s >' % Localization.localize('Content Lists'),
                                    Localization.localize(
                                        'You can always restart this by deleting DBs via Context Menu'), )

        if not self.getBoolSetting('oldc_' + searcher + language):
            self.setBoolSetting('oldc_' + searcher + language, True)
            __settings__.setSetting('scrapperDB_ver' + language, scrapperDB_ver)
            ok = xbmcgui.Dialog().yesno('< %s >' % Localization.localize('Content Lists'),
                                        Localization.localize('Do you want to search and cache full metadata + arts?'),
                                        Localization.localize(
                                            'This vastly decreases load speed, but you will be asked to download premade bases!'))
            if ok:
                self.setBoolSetting(searcher, True)
                redl = True
            else:
                self.setBoolSetting(searcher, False)

        if redl:
            self.Scraper = Scrapers()
            scrapers = {'tvdb': 'TheTVDB.com', 'tmdb': 'TheMovieDB.org', 'kinopoisk': 'KinoPoisk.ru'}
            for scraper in scrapers.keys():
                if scraper != 'kinopoisk' or language == 'ru':
                    self.Scraper.scraper(scraper, {'label': 'Мстители', 'search': [u'Мстители', u'The Avengers'],
                                                   'year': 2012}, language)

    def getBoolSetting(self, setting):
        return __settings__.getSetting(setting).lower() == "true"

    def setBoolSetting(self, setting, bool=True):
        __settings__.setSetting(setting, "true" if bool else "false")

    def list(self):
        searchersList = []
        dirList = os.listdir(ROOT + os.sep + 'resources' + os.sep + 'contenters')
        for searcherFile in dirList:
            if re.match('^(\w+)\.py$', searcherFile) and searcherFile != '__init__.py':
                searchersList.append(searcherFile.replace('.py', ''))
        return searchersList

    def dic(self):
        dic = {}
        for searcher in self.list():
            dic[searcher] = self.old(searcher)
        return dic

    def get_activedic(self):
        dic = {}
        # for searcher in self.list():
        #    if self.old(searcher): dic[searcher]=(searcher,)
        for searcher in self.list():
            dic[searcher] = (searcher,)
        return dic

    def old(self, searcher):
        if not self.getBoolSetting('oldc_' + searcher):
            self.setBoolSetting('oldc_' + searcher)
            self.setBoolSetting(searcher)
        return self.getBoolSetting(searcher)

    def get_active(self):
        get_active = []
        for searcher in self.list():
            if self.old(searcher): get_active.append(searcher)
        return get_active


def countSeasons(jdata):
    seasons, epdict = [], {}
    for id in jdata['episodes']:
        seasonNumber = jdata['episodes'][id]['seasonNumber']
        if seasonNumber not in seasons:
            seasons.append(seasonNumber)
        if jdata['episodes'][id]['episodeNumber']:
            if str(jdata['episodes'][id]['seasonNumber']) not in epdict:
                epdict[str(jdata['episodes'][id]['seasonNumber'])] = str(jdata['episodes'][id]['id'])
            else:
                epdict[str(jdata['episodes'][id]['seasonNumber'])] = epdict[str(
                    jdata['episodes'][id]['seasonNumber'])] + ',' + str(jdata['episodes'][id]['id'])
    seasons.sort()
    return seasons, epdict


def fetchData(url, referer=None):
    request = urllib2.Request(url)
    if referer != None:
        request.add_header('Referer', referer)
    request.add_header('User-Agent', USERAGENT)
    if __settings__.getSetting("auth"):
        authString = '; ' + __settings__.getSetting("auth")
    else:
        authString = ''
    request.add_header('Cookie', authString)
    try:
        connection = urllib2.urlopen(request)
        result = connection.read()
        connection.close()
        return (result)
    except (urllib2.HTTPError, urllib2.URLError) as e:
        log(" fetchData(" + url + ") exception: " + str(e))
        return


def file_decode(filename):
    pass
    try:
        filename = filename.decode('utf-8')  # ,'ignore')
    except:
        pass
    return filename


def file_encode(filename):
    if sys.getfilesystemencoding() == 'mbcs' and isAsciiString(filename):
        filename = filename.decode('cp1251').encode('utf-8')
    return filename


def isAsciiString(mediaName):
    for index, char in enumerate(mediaName):
        if ord(char) >= 128:
            return False
    return True


def getParameters(parameterString):
    commands = {}
    splitCommands = parameterString[parameterString.find('?') + 1:].split('&')
    for command in splitCommands:
        if (len(command) > 0):
            splitCommand = command.split('=')
            if (len(splitCommand) > 1):
                name = splitCommand[0]
                value = splitCommand[1]
                commands[name] = value
    return commands


def isSubtitle(filename, filename2):
    filename_if = filename[:len(filename) - len(filename.split('.')[-1]) - 1]
    filename_if = filename_if.split('/')[-1].split('\\')[-1]
    filename_if2 = filename2.split('/')[-1].split('\\')[-1][:len(filename_if)]
    # debug('Compare ' + filename_if.lower() + ' and ' + filename_if2.lower() + ' and ' + filename2.lower().split('.')[-1])
    ext = ['ass', 'mpsub', 'rum', 'sbt', 'sbv', 'srt', 'ssa', 'sub', 'sup', 'w32']
    if filename2.lower().split('.')[-1] in ext and \
                    filename_if.lower() == filename_if2.lower():
        return True
    return False


def delete_russian(ok=False, action='delete'):
    i = 0
    if not ok:
        ok = xbmcgui.Dialog().yesno('< %s >' % Localization.localize('International Check - First Run'),
                                    'Delete Russian stuff?',
                                    Localization.localize('Delete Russian stuff?'))
    if ok:
        fileList = {
            'contenters': ['CXZ.py', 'FastTorrent.py', 'KinoPoisk.py', 'RiperAM.py'],
            'searchers': ['NNMClubRu.py', 'OpenSharing.py', 'RiperAM.py', 'RuTorOrg.py', 'RuTrackerOrg.py',
                          'TFileME.py']
        }

        for path in fileList.keys():
            for filename in fileList[path]:
                if action == 'delete':
                    filepath = os.path.join(ROOT, 'resources', path, filename)
                    if xbmcvfs.exists(filepath):
                        newfilepath = os.path.join(ROOT, 'resources', path, 'unused', filename)
                        xbmcvfs.copy(filepath, newfilepath)
                        xbmcvfs.delete(filepath)
                elif action == 'return':
                    filepath = os.path.join(ROOT, 'resources', path, 'unused', filename)
                    if xbmcvfs.exists(filepath):
                        newfilepath = os.path.join(ROOT, 'resources', path, filename)
                        xbmcvfs.copy(filepath, newfilepath)
                        xbmcvfs.delete(filepath)
                        i = i + 1

        if action == 'return':
            return i
        return True
    else:
        return False


class DownloadDB:
    def __init__(self, version=1.41):
        self.name = 'download.db3'
        self.version = version

    def get_all(self):
        self._connect()
        self._execute(
            'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads order by addtime DESC')
        x = self.cur.fetchall()
        self._close()
        return x if x else None

    def get(self, title):
        self._connect()
        self._execute(
        'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads where title="' + decode(
            title) + '"')
        x = self.cur.fetchone()
        self._close()
        return x if x else None

    def get_byaddtime(self, addtime):
        self._connect()
        self._execute(
            'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads where addtime="' + str(
                addtime) + '"')
        x = self.cur.fetchone()
        self._close()
        return x if x else None

    def _execute(self, sql):
        try:
            self.cur.execute(sql)
        except Exception, e:
            if str(e)=='no such table: downloads':
                cur = self.db.cursor()
                cur.execute('pragma auto_vacuum=1')
                cur.execute(
                    'create table downloads(addtime integer PRIMARY KEY, title varchar(32), path varchar(32), type varchar(32), jsoninfo varchar(32), status varchar(32), torrent varchar(32), ind integer, lastupdate integer, storage varchar(32))')
                self.db.commit()
                cur.close()
                self.cur = self.db.cursor()
            else:
                self._close()
                debug('[DownloadDB]: DELETE ' + str(self.filename))
                xbmcvfs.delete(self.filename)
            self._connect()
            self.cur.execute(sql)

    def get_status(self, title):
        self._connect()
        self._execute('select status from downloads where title="' + decode(title) + '"')
        x = self.cur.fetchone()
        self._close()
        return x[0] if x else None

    def add(self, title, path, type, info, status, torrent, ind, storage):
        if not self.get(title):
            self._connect()
            self.cur.execute(
                'insert into downloads(addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage)'
                ' values(?,?,?,?,?,?,?,?,?,?)', (
                int(time.time()), decode(title), decode(path), type, json.dumps(info), status, decode(torrent), ind,
                int(time.time()), decode(storage)))
            self.db.commit()
            self._close()
            return True
        else:
            return False

    def update(self, title, info={}):
        try:
            title = title.decode('utf-8')
        except:
            pass
        self._connect()
        self._execute(
            'UPDATE downloads SET jsoninfo = "' + urllib.quote_plus(json.dumps(info)) + '", lastupdate=' + str(
                int(time.time())) + ' where title="' + title + '"')
        self.db.commit()
        self._close()

    def update_status(self, addtime, status):
        self._connect()
        self._execute('UPDATE downloads SET status = "' + status + '" where addtime="' + str(addtime) + '"')
        self.db.commit()
        self._close()

    def delete(self, addtime):
        self._connect()
        self._execute('delete from downloads where addtime="' + str(addtime) + '"')
        self.db.commit()
        self._close()

    def clear(self):
        self._connect()
        self._execute('delete from downloads')
        self.db.commit()
        self._close()

    def _connect(self):
        dirname = xbmc.translatePath('special://temp')
        for subdir in ('xbmcup', 'plugin.video.torrenter'):
            dirname = os.path.join(dirname, subdir)
            if not xbmcvfs.exists(dirname):
                xbmcvfs.mkdir(dirname)

        self.filename = os.path.join(dirname, self.name)

        first = False
        if not xbmcvfs.exists(self.filename):
            first = True

        self.db = sqlite.connect(self.filename, check_same_thread=False)
        if not first:
            self.cur = self.db.cursor()
            try:
                self.cur.execute('select version from db_ver')
                row = self.cur.fetchone()
                if not row or float(row[0]) != self.version:
                    self.cur.execute('drop table downloads')
                    self.cur.execute('drop table if exists db_ver')
                    first = True
                    self.db.commit()
                    self.cur.close()
            except:
                try:
                    self.cur.execute('drop table downloads')
                    first = True
                    self.db.commit()
                    self.cur.close()
                except:
                    self.cur.close()
                    self.db.close()
                    os.remove(self.filename)
                    first = True
                    self.db = sqlite.connect(self.filename, check_same_thread=False)

        if first:
            cur = self.db.cursor()
            cur.execute('pragma auto_vacuum=1')
            cur.execute('create table db_ver(version real)')
            cur.execute(
                'create table downloads(addtime integer PRIMARY KEY, title varchar(32), path varchar(32), type varchar(32), jsoninfo varchar(32), status varchar(32), torrent varchar(32), ind integer, lastupdate integer, storage varchar(32))')
            cur.execute('insert into db_ver(version) values(?)', (self.version,))
            self.db.commit()
            cur.close()
            self.cur = self.db.cursor()

    def _close(self):
        self.cur.close()
        self.db.close()


def decode(string, ret=None):
    try:
        string = string.decode('utf-8')
        return string
    except:
        if ret:
            return ret
        else:
            return string


def unquote(string, ret=None):
    try:
        return urllib.unquote_plus(string)
    except:
        if ret:
            return ret
        else:
            return string


def itemScrap(item, kwarg):
    # debug('[itemTVDB]:meta '+str(kwarg))
    if 'title' in kwarg and kwarg['title']:
        item.setLabel(kwarg['title'])

    if 'label' in kwarg and kwarg['label']:
        item.setLabel2(kwarg['label'])

    if 'icon' in kwarg and kwarg['icon']:
        item.setIconImage(kwarg['icon'])

    if 'thumbnail' in kwarg and kwarg['thumbnail']:
        item.setThumbnailImage(kwarg['thumbnail'])

    if 'properties' in kwarg and kwarg['properties']:
        for key, value in kwarg['properties'].iteritems():
            item.setProperty(key, str(value))

    if 'info' in kwarg and kwarg['properties']:
        item.setInfo(type='Video', infoLabels=kwarg['info'])

    return item


def get_ids_video(contentList):
    ids_video = []
    allowed_video_ext = ['avi', 'mp4', 'mkv', 'flv', 'mov', 'vob', 'wmv', 'ogm', 'asx', 'mpg', 'mpeg', 'avc', 'vp3',
                         'fli', 'flc', 'm4v', 'iso']
    allowed_music_ext = ['mp3', 'flac', 'wma', 'ogg', 'm4a', 'aac', 'm4p', 'rm', 'ra']
    for extlist in [allowed_video_ext, allowed_music_ext]:
        for item in contentList:
            title = item[0]
            identifier = item[1]
            try:
                ext = title.split('.')[-1]
                if ext.lower() in extlist:
                    ids_video.append(str(identifier))
            except:
                pass
        if len(ids_video) > 1:
            break
    # print debug('[get_ids_video]:'+str(ids_video))
    return ids_video


def first_run_230(delete_russian):
    if not __settings__.getSetting('first_run_230')=='True':
        __settings__.setSetting('first_run_230','True')
        if not delete_russian:
            yes=xbmcgui.Dialog().yesno('< %s >' % Localization.localize('Torrenter Update 2.3.0'),
                                        Localization.localize('Would you like to install %s from "MyShows.me Kodi Repo" in Programs section?') % 'RuTrackerOrg',
                                        Localization.localize('Open installation window?'))
            if yes:
                xbmc.executebuiltin('Dialog.Close(all,true)')
                xbmc.executebuiltin('XBMC.ActivateWindow(Addonbrowser,addons://search/%s)' % ('Torrenter Searcher'))

def first_run_231():
    if not __settings__.getSetting('first_run_231')=='True':
        __settings__.setSetting('first_run_231','True')
        ok = xbmcgui.Dialog().ok('< %s >' % Localization.localize('Torrenter Update 2.3.1'),
                                    Localization.localize('We added Android ARM full support to Torrenter v2!'),
                                    Localization.localize('I deleted pre-installed ones, install them in Search Control Window!'))

        yes=xbmcgui.Dialog().yesno('< %s >' % Localization.localize('Torrenter Update 2.3.1'),
                                        Localization.localize('You have no installed or active searchers! More info in Search Control Window!'),
                                        Localization.localize('Would you like to install %s from "MyShows.me Kodi Repo" in Programs section?') % '',)
        if yes:
            xbmc.executebuiltin('Dialog.Close(all,true)')
            xbmc.executebuiltin('XBMC.ActivateWindow(Addonbrowser,addons://search/%s)' % ('Torrenter Searcher'))

def first_run_250():
    if __settings__.getSetting('torrent_player')=='3':
        __settings__.setSetting('first_run_250','True')

    if not __settings__.getSetting('first_run_250')=='True':
        __settings__.setSetting('first_run_250','True')
        yes=xbmcgui.Dialog().yesno('< %s >' % (Localization.localize('Torrenter Update ') + '2.5.0'),
                                        Localization.localize('New player to Torrenter v2 - pyrrent2http! Advantages of Torrent2HTTP '
                                                              'but with python-libtorrent library instead of libtorrent-go!'),
                                        Localization.localize('Would you like to try it?'),)
        if yes:
            __settings__.openSettings()
            #__settings__.setSetting('torrent_player','2')
            #ok = xbmcgui.Dialog().ok('< %s >' % (Localization.localize('Torrenter Update ') + '2.4.2'),
            #                        Localization.localize('Torrent2HTTP enabled! Can be changed in Settings.'))

def first_run_260():
    if not __settings__.getSetting('first_run_260') == 'True':
        yes=xbmcgui.Dialog().yesno('< %s >' % (Localization.localize('Torrenter Update ') + '2.6.0'),
                                        Localization.localize('Torrenter Search Window')+' '
                                   +Localization.localize('is recommended for Kodi 17 users and now out of beta.')
                                   +Localization.localize('You can disable it usage in Settings.'),
                                        Localization.localize('Would you like to try it?'),)
        if yes:
            import searchwindow
            searchwindow.main()


def estuary():
    if __settings__.getSetting('skin_optimization') not in ['7', '0'] and \
                    __settings__.getSetting('ask17_skin_optimization') != 'True':

        yes = xbmcgui.Dialog().yesno('< %s >' % (Localization.localize('Torrenter Update ') + '2.6.0'),
                                     Localization.localize('Torrenter has a better view style for Kodi 17 default skin.'),
                                     Localization.localize('Would you like to try it?'), )
        if yes:
            __settings__.setSetting('skin_optimization', '7')
    __settings__.setSetting('ask_skin_optimization', 'True')

def seeking_warning(seek):
    if __settings__.getSetting('torrent_player')!='1':
        seek_point = '%02d:%02d:%02d' % ((seek / (60*60)), (seek / 60) % 60, seek % 60)
        yes=xbmcgui.Dialog().yesno('< %s >' % (Localization.localize('Seeking')),
            Localization.localize('Would you like to resume from %s?') % seek_point,)
        if yes:
            log('[seeking_warning]: yes, seek = '+str(seek))
            return seek
        else:
            log('[seeking_warning]: no, seek = '+str(0))
            return 0
    else:
        if not __settings__.getSetting('seeking_warning')=='True':
            __settings__.setSetting('seeking_warning','True')
            yes=xbmcgui.Dialog().yesno('< %s >' % (Localization.localize('Seeking')),
                                        Localization.localize('Seeking is working only with player Torrent2HTTP.'),
                                     Localization.localize('Would you like to try it?'))
            if yes:
                __settings__.openSettings()
                #__settings__.setSetting('torrent_player','2')
                #ok = xbmcgui.Dialog().ok('< %s >' % (Localization.localize('Seeking')),
                #                        Localization.localize('Torrent2HTTP enabled! Can be changed in Settings.'))
                return seek

def noActiveSerachers():
    yes=xbmcgui.Dialog().yesno('< %s >' % Localization.localize('Torrenter v2'),
                                        Localization.localize('You have no installed or active searchers! More info in Search Control Window!'),
                                        Localization.localize('Would you like to install %s from "MyShows.me Kodi Repo" in Programs section?') % '',)
    if yes:
        xbmc.executebuiltin('Dialog.Close(all,true)')
        xbmc.executebuiltin('XBMC.ActivateWindow(Addonbrowser,addons://search/%s)' % ('Torrenter Searcher'))

def windows_check():
    import platform
    """
    Checks if the current platform is Windows
    :returns: True or False
    :rtype: bool
    """
    return platform.system() in ('Windows', 'Microsoft')

def vista_check():
    import platform
    """
    Checks if the current platform is Windows Vista
    :returns: True or False
    :rtype: bool
    """
    return platform.release() == "Vista"

def is_writable(path):
    if not xbmcvfs.exists(path+os.sep):
        xbmcvfs.mkdirs(path)
    try:
        open(os.path.join(file_decode(path), 'temp'), 'w')
    except:
         return False
    else:
         os.remove(os.path.join(file_decode(path), 'temp'))
         return True

def unescape(string):
    htmlCodes = (
        ('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
        ('"', '&quot;'),
        ("'", '&#39;'),
    )
    for (symbol, code) in htmlCodes:
        string = re.sub(code, symbol, string)
    return string

def stripHtml(string):
    stripPairs = (
        ('<p>', '\n'),
        ('<li>', '\n'),
        ('<br>', '\n'),
        ('<.+?>', ' '),
        ('</.+?>', ' '),
        ('&nbsp;', ' '),
        ('&laquo;', '"'),
        ('&raquo;', '"'),
    )
    for (html, replacement) in stripPairs:
        string = re.sub(html, replacement, string)
    return string

def chooseFile(filelist):
    myshows_items, myshows_files, contentList, myshows_sizes = [], [], [], {}
    for filedict in filelist:
        fileTitle = ''
        if filedict.get('size'):
            myshows_sizes[str(filedict.get('ind'))]='[%d MB] ' % (filedict.get('size') / 1024 / 1024)
        title = filedict.get('title')
        fileTitle = fileTitle + '[%s]%s' % (title[len(title) - 3:], title)
        contentList.append((unescape(fileTitle), str(filedict.get('ind'))))
    contentList = sorted(contentList, key=lambda x: x[0])
    EXTS=['avi','mp4','mkv','flv','mov','vob','wmv','ogm','asx','mpg','mpeg','avc','vp3','fli','flc','m4v','iso','mp3']
    for title, identifier in contentList:
        try:
            if title.split('.')[-1].lower() in EXTS:
                myshows_items.append(title)
                myshows_files.append(identifier)
        except:
            pass
    if len(myshows_items) > 1:
        if len(myshows_sizes)==0:
            myshows_items = cutFileNames(myshows_items)
        else:
            myshows_cut = cutFileNames(myshows_items)
            myshows_items=[]
            x=-1
            for i in myshows_files:
                x=x+1
                fileTitle=myshows_sizes[str(i)]+myshows_cut[x]
                myshows_items.append(fileTitle)

    log('[chooseFile]: myshows_items '+str(myshows_items))
    if len(myshows_items) == 1:
        ret = 0
    else:
        ret = xbmcgui.Dialog().select(Localization.localize('Search results:'), myshows_items)

    if ret > -1:
        return myshows_files[ret]

def check_network_advancedsettings():
    path=xbmc.translatePath('special://profile/advancedsettings.xml')
    updated=False
    #path='''C:\\Users\\Admin\\AppData\\Roaming\\Kodi\\userdata\\advancedsettings.xml'''
    settings={'buffermode':2, 'curlclienttimeout':30, 'cachemembuffersize':252420, 'readbufferfactor':5.0}
    add, update = {}, {}


    if not os.path.exists(path):
        updated=True
        file_cont='''<advancedsettings>
  <network>
    <buffermode>2</buffermode>
    <curlclienttimeout>30</curlclienttimeout>
    <cachemembuffersize>252420</cachemembuffersize>
    <readbufferfactor>5</readbufferfactor>
  </network>
</advancedsettings>'''
    else:
        with open(path) as f:
            file_cont=f.read()

        log('[check_network_advancedsettings]: old file_cont '+str(file_cont))

    if not updated and not re.search('<network>.+?</network>', file_cont, re.DOTALL):
        updated=True
        file_cont=file_cont.replace('<advancedsettings>',
'''<advancedsettings>
  <network>
    <buffermode>2</buffermode>
    <curlclienttimeout>30</curlclienttimeout>
    <cachemembuffersize>252420</cachemembuffersize>
    <readbufferfactor>5</readbufferfactor>
  </network>
</advancedsettings>''')
    elif not updated:
        for key in settings.keys():
            search=re.search('<'+key+'>(.+?)</'+key+'>', file_cont, re.DOTALL)
            if not search:
                add[key]=settings[key]
            else:
                present_value=search.group(1)
                if key == 'buffermode' and int(present_value)==3:
                    update[key]=settings[key]
                elif key in ['curlclienttimeout', 'cachemembuffersize'] and int(present_value)<int(settings[key]):
                    update[key]=settings[key]
                elif key == 'readbufferfactor' and float(present_value)<settings[key]:
                    update[key]=settings[key]
        log('[check_network_advancedsettings]: add '+str(add)+' update '+str(update))
        if len(add)>0 or len(update)>0:
            updated=True
            for key in add.keys():
                file_cont=file_cont.replace('<network>','<network>\r\n    <'+key+'>'+str(add[key])+'</'+key+'>')
            for key in update.keys():
                file_cont=re.sub(r'<'+key+'>.+?</'+key+'>', '<'+key+'>'+str(update[key])+'</'+key+'>', file_cont)

    if updated:
        dialog=xbmcgui.Dialog()
        ok=dialog.yesno(Localization.localize('Upgrade advancedsettings.xml'),
                        Localization.localize('We would like to set some advanced settings for you!'),
                        Localization.localize('Do it!'))
        if ok:
            log('[check_network_advancedsettings]: new file_cont '+str(file_cont))

            f=open(path, mode='w')
            f.write(file_cont)
            f.close()
            dialog.ok(Localization.localize('Upgrade advancedsettings.xml'),
                      Localization.localize('Please, restart Kodi now!'))
            log('Restart Kodi')
        else:
            log('UPDATE advancedsettings.xml disabled by user!')

def get_download_dir():
    import tempfile
    platform = get_platform()

    dialog=xbmcgui.Dialog()
    dialog.ok(Localization.localize('Torrenter'),
                Localization.localize('Please specify storage folder in Settings!'))
    #

    try:
        if not platform['system']=='android':
            download_dir = tempfile.gettempdir()
        else:
            download_dir = tempdir()
    except:
        download_dir = tempdir()
    return download_dir

def check_download_dir():
    if len(__settings__.getSetting("storage"))==0:
        dialog=xbmcgui.Dialog()
        dialog.ok(Localization.localize('Torrenter'),
                    Localization.localize('Please specify storage folder in Settings!'))
        __settings__.openSettings()

def ensure_str(string, encoding='utf-8'):
    if isinstance(string, unicode):
        string = string.encode(encoding)
    if not isinstance(string, str):
        string = str(string)
    return string

def file_url(torrentFile):
    import urlparse
    torrentFile = ensure_str(torrentFile)
    if not re.match("^file\:.+$", torrentFile):
        torrentFile = urlparse.urljoin('file:', urllib.pathname2url(torrentFile))
    return torrentFile

def dump(obj):
    for attr in dir(obj):
        try:
            log("'%s':'%s'," % (attr, getattr(obj, attr)))
        except:
            pass

def getDirectorySizeInBytes(directory):
    dir_size = 0
    for (path, dirs, files) in os.walk(directory):
        for file in files:
            filename = os.path.join(path, file)
            try:
                dir_size += os.path.getsize(filename)
            except:
                pass
    return dir_size

def getDirectorySizeInGB(directory):
    dir_size = int(getDirectorySizeInBytes(directory)/1024/1024/1024)
    return dir_size

def foldername(path):
    if '\\' in path:
        foldername = path.split('\\')[0]
    else:
        foldername = ''
    return foldername

def uri2path(uri):
    import urlparse
    if uri[1] == ':' and sys.platform.startswith('win'):
        uri = 'file:///' + uri
    fileUri = urlparse.urlparse(uri)
    if fileUri.scheme == 'file':
        uriPath = fileUri.path
        if uriPath != '' and sys.platform.startswith('win') and (os.path.sep == uriPath[0] or uriPath[0] == '/'):
            uriPath = uriPath[1:]
    absPath = os.path.abspath(urllib.unquote(uriPath))
    return localize_path(absPath)

def localize_path(path):
    import chardet
    if not isinstance(path, unicode):
        try:
            path = path.decode(chardet.detect(path).get('encoding') or 'utf-8')
        except:
            pass
    if not sys.platform.startswith('win'):
        path = encode_msg(path)
    return path

def encode_msg(msg):
    try:
        msg = isinstance(msg, unicode) and msg.encode(
            (sys.getfilesystemencoding() not in ('ascii', 'ANSI_X3.4-1968')) and sys.getfilesystemencoding() or 'utf-8') or msg
    except:
        import traceback
        log(traceback.format_exc())
        msg = ensure_str(msg)
    return msg

def decode_str(string, encoding='utf-8'):
    if not isinstance(string, unicode):
        string = string.decode(encoding)
    return string

def get_platform():
    ret = {
        "arch": sys.maxsize > 2 ** 32 and "x64" or "x86",
    }
    if xbmc.getCondVisibility("system.platform.android"):
        ret["os"] = "android"
        if "arm" in os.uname()[4] or "aarch64" in os.uname()[4]:
            ret["arch"] = "arm"
    elif xbmc.getCondVisibility("system.platform.linux"):
        ret["os"] = "linux"
        uname=os.uname()[4]
        if "arm" in uname:
            if "armv7" in uname:
                ret["arch"] = "armv7"
            elif "armv6" in uname:
                ret["arch"] = "armv6"
            else:
                ret["arch"] = "arm"
        elif "mips" in uname:
            if sys.maxunicode > 65536:
                ret["arch"] = 'mipsel_ucs4'
            else:
                ret["arch"] = 'mipsel_ucs2'
    elif xbmc.getCondVisibility("system.platform.windows"):
        ret["os"] = "windows"
    elif xbmc.getCondVisibility("system.platform.osx"):
        ret["os"] = "darwin"
    elif xbmc.getCondVisibility("system.platform.ios"):
        ret["os"] = "ios"
        ret["arch"] = "arm"

    return ret

def getTorrentClientIcon():
    client = __settings__.getSetting("torrent")
    if client == '1':
        return 'transmission.png'
    elif client == '2':
        return 'vuze.png'
    elif client == '3':
        return 'deluge.png'
    elif client == '4':
        return 'qbittorrent.png'
    else:
        return 'torrent-client.png'

def get_item():
    #some plugin.video.quasar magic
    item = xbmcgui.ListItem(
        path='',
        label=xbmc.getInfoLabel("ListItem.Label"),
        label2=xbmc.getInfoLabel("ListItem.label2"),
        thumbnailImage=xbmc.getInfoLabel("ListItem.Art(thumb)"))
    _infoLabels = {
        "Title": xbmc.getInfoLabel("ListItem.Title"),
        "OriginalTitle": xbmc.getInfoLabel("ListItem.OriginalTitle"),
        "TVShowTitle": xbmc.getInfoLabel("ListItem.TVShowTitle"),
        "Season": xbmc.getInfoLabel("ListItem.Season"),
        "Episode": xbmc.getInfoLabel("ListItem.Episode"),
        "Premiered": xbmc.getInfoLabel("ListItem.Premiered"),
        "Plot": xbmc.getInfoLabel("ListItem.Plot"),
        # "Date": xbmc.getInfoLabel("ListItem.Date"),
        "VideoCodec": xbmc.getInfoLabel("ListItem.VideoCodec"),
        "VideoResolution": xbmc.getInfoLabel("ListItem.VideoResolution"),
        "VideoAspect": xbmc.getInfoLabel("ListItem.VideoAspect"),
        "DBID": xbmc.getInfoLabel("ListItem.DBID"),
        "DBTYPE": xbmc.getInfoLabel("ListItem.DBTYPE"),
        "Writer": xbmc.getInfoLabel("ListItem.Writer"),
        "Director": xbmc.getInfoLabel("ListItem.Director"),
        "Rating": xbmc.getInfoLabel("ListItem.Rating"),
        "Votes": xbmc.getInfoLabel("ListItem.Votes"),
        "IMDBNumber": xbmc.getInfoLabel("ListItem.IMDBNumber"),
    }
    infoLabels = {}
    for key, value in _infoLabels.iteritems():
        if value:
            infoLabels[key] = value

    poster = xbmc.getInfoLabel("ListItem.Art(poster)")
    if not poster:
        poster = xbmc.getInfoLabel("ListItem.Art(tvshow.poster)")

    item.setArt({
        "poster": poster,
        "banner": xbmc.getInfoLabel("ListItem.Art(banner)"),
        "fanart": xbmc.getInfoLabel("ListItem.Art(fanart)")
    })

    item.setInfo(type='Video', infoLabels=infoLabels)
    return item

def loadsw_onstop():
    if __settings__.getSetting('loadsw_onstop') == 'true':
        import searchwindow
        params = {'mode': 'load'}
        searchwindow.main(params)

def watched_seek(filename, ind):
    db = WatchedHistoryDB()
    seek = db.getbypathind(filename, ind)
    log('[watched_seek] seek - '+str(seek))
    if seek:
        seek = seek[0]
        seek = int(seek) if int(seek) > 3 * 60 else 0
        if seek > 0:
                seek_text = '%02d:%02d:%02d' % ((seek / (60 * 60)), (seek / 60) % 60, seek % 60)
                dialog_items = [Localization.localize('Play (from %s)') % seek_text,
                               Localization.localize('Play (from start)')]
                ret = xbmcgui.Dialog().select(Localization.localize('Play (with seek)'), dialog_items)
                if ret == 0:
                    return str(seek)
    return '0'