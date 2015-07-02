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

import urllib2
import re
import socket
import datetime
import time
import sys
import os
import json
import urllib
import hashlib

import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import xbmcvfs
import Localization
from resources.scrapers.scrapers import Scrapers

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

__settings__ = xbmcaddon.Addon(id='plugin.video.torrenter')
__language__ = __settings__.getLocalizedString
ROOT = __settings__.getAddonInfo('path')  # .decode('utf-8').encode(sys.getfilesystemencoding())
userStorageDirectory = __settings__.getSetting("storage")
USERAGENT = "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0"
torrentFilesDirectory = 'torrents'
__addonpath__ = __settings__.getAddonInfo('path')
icon = __addonpath__ + '/icon.png'
debug = __settings__.getSetting("debug")
__version__ = __settings__.getAddonInfo('version')
__plugin__ = __settings__.getAddonInfo('name') + " v." + __version__


def clearStorage(userStorageDirectory):
    try:
        userStorageDirectory = userStorageDirectory.decode('utf-8')
    except:
        pass
    if xbmcvfs.exists(userStorageDirectory + os.sep):
        import shutil

        temp = userStorageDirectory.rstrip('Torrenter').rstrip('/\\')
        torrents_temp, i = None, 0
        while not torrents_temp or xbmcvfs.exists(torrents_temp):
            torrents_temp = os.path.join(temp, 'torrents' + str(i)) + os.sep
            i += 1
        shutil.move(os.path.join(userStorageDirectory, 'torrents'), torrents_temp)
        shutil.rmtree(userStorageDirectory, ignore_errors=True)
        xbmcvfs.mkdir(userStorageDirectory)
        shutil.move(torrents_temp, os.path.join(userStorageDirectory, 'torrents'))
    DownloadDB().clear()
    showMessage(Localization.localize('Storage'), Localization.localize('Storage was cleared'), forced=True)


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
    hasher = hashlib.md5()
    try:
        hasher.update(string)
    except:
        hasher.update(string.encode('utf-8', 'ignore'))
    return hasher.hexdigest()


def Debug(msg, force=False):
    if (1 == 1 or debug == 'true' or force):
        try:
            print "[Torrenter v2] " + msg
        except UnicodeEncodeError:
            print "[Torrenter v2] " + msg.encode("utf-8", "ignore")


def showMessage(heading, message, times=10000, forced=False):
    xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (
        heading.replace('"', "'"), message.replace('"', "'"), times, icon))


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
        # Debug('[get_url]: arr"'+str(array)+'"')
        if array == '':
            # Debug('[get_url][2]: arr=""')
            array = True
        return array
    except urllib2.HTTPError as e:
        # Debug('[get_url]: HTTPError, e.code='+str(e.code))
        if e.code == 401:
            Debug('[get_url]: Denied! Wrong login or api is broken!')
            return
        elif e.code in [503]:
            Debug('[get_url]: Denied, HTTP Error, e.code=' + str(e.code))
            return
        else:
            showMessage('HTTP Error', str(e.code))
            Debug('[get_url]: HTTP Error, e.code=' + str(e.code))
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
    Debug('[cutFileNames] ' + unicode(result))

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
    Debug('[cutFileNames] [start] ' + start)
    Debug('[cutFileNames] [end] ' + end)
    for fl in newl:
        if cutStr(fl[0:len(start)]) == cutStr(start): fl = fl[len(start):]
        if cutStr(fl[len(fl) - len(end):]) == cutStr(end): fl = fl[0:len(fl) - len(end)]
        try:
            isinstance(int(fl.split(sep_file)[0]), int)
            fl = fl.split(sep_file)[0]
        except:
            pass
        l.append(fl)
    Debug('[cutFileNames] [sorted l]  ' + unicode(sorted(l, key=lambda x: x)), True)
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
    Debug('[sortext]: lol:' + str(lol))
    popext = lol[-1][0]
    result, i = [], 0
    for name in filelist:
        if name.split('.')[-1] == popext:
            result.append(name)
            i = i + 1
    result = sweetpair(result)
    Debug('[sortext]: result:' + str(result))
    return result


def cutFolder(contentList, tdir=None):
    dirList, contentListNew = [], []

    if len(contentList) > 1:
        common_folder = contentList[0][0]
        if '\\' in common_folder:
            common_folder = common_folder.split('\\')[0]
        elif '/' in common_folder:
            common_folder = common_folder.split('/')[0]

        common = True
        for fileTitle, contentId in contentList:
            if common_folder not in fileTitle:
                print 'no common'
                common = False
                break

        # print common_folder
        for fileTitle, contentId in contentList:
            dir = None
            if common:
                fileTitle = fileTitle[len(common_folder) + 1:]

            # print fileTitle

            if '\\' in fileTitle:
                dir = fileTitle.split('\\')[0]
            elif '/' in fileTitle:
                dir = fileTitle.split('/')[0]
            elif not tdir:
                contentListNew.append((fileTitle, contentId))

            if tdir and dir == tdir:
                contentListNew.append((fileTitle[len(dir) + 1:], contentId))

            if not tdir and dir and dir not in dirList:
                dirList.append(dir)

        return dirList, contentListNew
    else:
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
            # Debug('1 - %d %d' % (id1, id2))
        elif (ratio[id2] <= ratio[i] or id1 == id2) and i != id1:
            id2 = i
            # Debug('2 - %d %d' % (id1, id2))

    Debug('[sweetpair]: id1 ' + l[id1] + ':' + str(ratio[id1]))
    Debug('[sweetpair]: id2 ' + l[id2] + ':' + str(ratio[id2]))

    return [l[id1], l[id2]]


def FileNamesPrepare(filename):
    my_season = None
    my_episode = None

    try:
        if int(filename):
            my_episode = int(filename)
            Debug('[FileNamesPrepare] ' + str([my_season, my_episode, filename]))
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
            Debug('[FileNamesPrepare] ' + str([my_season, my_episode, filename]))
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
            # Debug('[filename2match] '+str(results))
            return results
    if no_date: return
    urls = ['(.+)(\d{4})\.(\d{2,4})\.(\d{2,4})', '(.+)(\d{4}) (\d{2}) (\d{2})']  # same in service
    for file in urls:
        match = re.compile(file, re.I | re.IGNORECASE).findall(filename)
        if match:
            results['showtitle'] = match[0][0].replace('.', ' ').strip().replace('The Daily Show',
                                                                                 'The Daily Show With Jon Stewart')
            results['date'] = '%s.%s.%s' % (match[0][3], match[0][2], match[0][1])
            Debug('[filename2match] ' + str(results))
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
    num_skin, style = 0, 'info'
    view_style = int(__settings__.getSetting("skin_optimization"))
    if view_style in [3, 2]:
        styles['searchOption'] = styles['History'] = styles['List'] = 'info'
        styles['drawContent'] = styles['drawtrackerList'] = styles['drawcontentList'] = 'info'
        styles['sectionMenu'] = styles['Seasons'] = 'list'
        styles['uTorrentBrowser'] = styles['torrentPlayer'] = styles['openTorrent'] = 'wide'
        styles['showFilesList'] = styles['DownloadStatus'] = 'wide'
    elif view_style in [1, 4]:
        styles['searchOption'] = 'info'
        styles['drawContent'] = styles['torrentPlayer'] = styles['openTorrent'] = styles['drawtrackerList'] = 'info'
        styles['uTorrentBrowser'] = styles['History'] = styles['DownloadStatus'] = 'wide'
        styles['showFilesList'] = styles['sectionMenu'] = 'wide'
        styles['List'] = styles['drawcontentList'] = 'info3'

    if view_style == 1:
        styles['uTorrentBrowser'] = styles['torrentPlayer'] = 'wide'
        styles['openTorrent'] = styles['History'] = styles['DownloadStatus'] = 'wide'
        styles['sectionMenu'] = 'icons'

    if view_style in [1, 3, 4]:
        num_skin = 0
    elif view_style == 2:
        num_skin = 1

    style = styles.get(func)
    # Debug('[view_style]: lock '+str(style))
    lockView(style, num_skin)


def lockView(viewId='info', num_skin=0):
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    skinOptimizations = (
        {'list': 50, 'info': 50, 'wide': 51, 'icons': 500, 'info3': 515, },  # Confluence
        {'list': 50, 'info': 51, 'wide': 52, 'icons': 53, }  # Transperency!
    )
    try:
        xbmc.executebuiltin("Container.SetViewMode(%s)" % str(skinOptimizations[num_skin][viewId]))
    except:
        return

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
    Debug('[smbtopath]:' + '\\\\' + path.replace('/', '\\'))
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


def kinorate(title, year, titleAlt=None, kinopoiskId=None):
    if kinopoiskId:
        match = {'title': title.replace('"', ''), 'year': str(year), 'kinopoiskId': str(kinopoiskId)}
    else:
        match = {'title': title.replace('"', ''), 'year': str(year)}
    if titleAlt:
        match['titleAlt'] = titleAlt.replace('"', '')
    try:
        xbmc.executebuiltin(
            'xbmc.RunScript(' + xbmcaddon.Addon("script.myshows").getAddonInfo("path") + os.sep +
            'sync_exec.py,' + json.dumps(match).replace(',', '|:|') + ')')
    except:
        return False


class RateShow():
    def __init__(self, showId, watched_jdata=None):
        self.dialog = xbmcgui.Dialog()
        self.showId = showId
        self.list = {}
        if watched_jdata:
            self.watched_jdata = watched_jdata
        else:
            watched_data = Data(cookie_auth, __baseurl__ + '/profile/shows/' + str(showId) + '/',
                                __baseurl__ + '/profile/shows/' + str(showId) + '/')
            try:
                self.watched_jdata = json.loads(watched_data.get())
            except:
                Debug('[RateShow] no watched_jdata1')
                return
            if not self.watched_jdata:
                Debug('[RateShow] no watched_jdata2')
                return

    def seasonrates(self):
        jload = Data(cookie_auth, __baseurl__ + '/profile/shows/').get()
        jshowdata = json.loads(jload)
        if str(self.showId) in jshowdata:
            self.list, seasonNumber = self.listSE(jshowdata[str(self.showId)]['totalEpisodes'])
            ratedict = {}
            for i in self.list:
                for j in self.list[i]:
                    if self.watched_jdata.has_key(j):
                        if self.watched_jdata[j]['rating']:
                            if ratedict.has_key(i):
                                ratedict[i].append(self.watched_jdata[j]['rating'])
                            else:
                                ratedict[i] = [self.watched_jdata[j]['rating']]
            # Debug('[ratedict]:'+str(ratedict))
            for i in ratedict:
                ratedict[i] = (round(float(sum(ratedict[i])) / len(ratedict[i]), 2), len(ratedict[i]))
            Debug('[ratedict]:' + str(ratedict))
        else:
            ratedict = {}
        return ratedict

    def count(self):
        ratings, seasonratings = [], []
        showId = str(self.showId)
        jload = Data(cookie_auth, __baseurl__ + '/profile/shows/').get()
        jshowdata = json.loads(jload)
        self.list, seasonNumber = self.listSE(jshowdata[showId]['totalEpisodes'])
        old_rating = jshowdata[showId]['rating']
        for id in self.watched_jdata:
            if self.watched_jdata[id]['rating']:
                ratings.append(self.watched_jdata[id]['rating'])
                if id in self.list[str(seasonNumber)]:
                    seasonratings.append(self.watched_jdata[id]['rating'])
        # Debug('ratings:'+str(ratings)+'; seasonratings:'+str(seasonratings))
        if len(ratings) > 0:
            rating = round(float(sum(ratings)) / len(ratings), 2)
        else:
            rating = 0
        if len(seasonratings) > 0:
            seasonrating = round(float(sum(seasonratings)) / len(seasonratings), 2)
        else:
            seasonrating = 0
        return rating, seasonNumber, seasonrating, old_rating

    def listSE(self, maxep):
        listSE, seasonNumber = {}, 0
        data = Data(cookie_auth, __baseurl__ + '/shows/' + str(self.showId))
        jdata = json.loads(data.get())
        for id in jdata['episodes']:
            if maxep >= jdata['episodes'][id]['sequenceNumber']:
                if listSE.has_key(str(jdata['episodes'][id]['seasonNumber'])):
                    listSE[str(jdata['episodes'][id]['seasonNumber'])].append(id)
                else:
                    listSE[str(jdata['episodes'][id]['seasonNumber'])] = [id]
                if jdata['episodes'][id]['seasonNumber'] > seasonNumber:
                    seasonNumber = jdata['episodes'][id]['seasonNumber']
        # Debug('[listSE] '+str(listSE)+str(seasonNumber))
        return listSE, seasonNumber


def isRemoteTorr():
    localhost = ['127.0.0.1', '0.0.0.0', 'localhost']
    if __settings__.getSetting("torrent") == '0':
        if __settings__.getSetting("torrent_utorrent_host") not in localhost:
            Debug('[isRemoteTorr]: uTorrent is Remote!')
            return True
    elif __settings__.getSetting("torrent") == '1':
        if __settings__.getSetting("torrent_transmission_host") not in localhost:
            Debug('[isRemoteTorr]: Transmission is Remote!')
            return True


def changeDBTitle(showId):
    from utilities import xbmcJsonRequest

    shows = xbmcJsonRequest(
        {'jsonrpc': '2.0', 'method': 'VideoLibrary.GetTVShows', 'params': {'properties': ['title']}, 'id': 0})

    if not shows:
        Debug('[changeDBTitle]: XBMC JSON Result was empty.')
        return

    if 'tvshows' in shows:
        shows = shows['tvshows']
        Debug("[changeDBTitle]: XBMC JSON Result: '%s'" % str(shows))
    else:
        Debug("[changeDBTitle]: Key 'tvshows' not found")
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
                    Debug("[changeDBTitle]: XBMC JSON Result: '%s'" % str(result))
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
                Debug('[TimeOut]: too soon to go back offline! %d s' % (
                    (gone_online + self.online * 4) - int(round(time.time()))))
                return
        if self.timeout() == self.online:
            Debug('[TimeOut]: Gone offline! %d s' % ((gone_online + self.online * 4) - int(round(time.time()))))
            showMessage(__language__(30520), __language__(30545) % (self.offline))
            if self.get: self.scan.delete()
            self.scan.add()

    def go_online(self):
        if self.get:
            self.scan.delete()
            Debug('[TimeOut]: Gone online!')
            showMessage(__language__(30521), __language__(30545) % (self.online))
            if self.gone_online.get():
                self.gone_online.delete()
            self.gone_online.add()

    def timeout(self):
        if self.get and int(time.time()) - self.get < refresh_period * 3600:
            to = self.offline
        else:
            to = self.online
        # Debug('[TimeOut]: '+str(to))
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
        # print 'get_providers: '+str(x[0].split(',') if x and x[0]!='' else None)
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
        self._connect()
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
            self.db.commit()
            self._close()

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
        for searcher in self.list().iterkeys():
            if self.old(searcher): get_active.append(searcher + '.py')
        print 'Active Searchers: ' + str(get_active)
        return get_active

    def searchWithSearcher(self, keyword, searcher):
        filesList = []
        slist = Searchers().list()
        if slist[searcher]['path'] not in sys.path:
            sys.path.insert(0, slist[searcher]['path'])
            print 'Added %s in sys.path' % (slist[searcher]['path'])
        try:
            searcherObject = getattr(__import__(searcher), searcher)()
            filesList = searcherObject.search(keyword)
        except Exception, e:
            print 'Unable to use searcher: ' + searcher + ' at ' + __plugin__ + ' searchWithSearcher(). Exception: ' + str(
                e)
        return filesList

    def downloadWithSearcher(self, url, searcher):
        slist = Searchers().list()
        if slist[searcher]['path'] not in sys.path:
            sys.path.insert(0, slist[searcher]['path'])
            print 'Added %s in sys.path' % (slist[searcher]['path'])
        try:
            searcherObject = getattr(__import__(searcher), searcher)()
            url = searcherObject.getTorrentFile(url)
        except Exception, e:
            print 'Unable to use searcher: ' + searcher + ' at ' + __plugin__ + ' downloadWithSearcher(). Exception: ' + str(
                e)
        return url


def search(url, searchersList, isApi=None):
    from threading import Thread
    from Queue import Queue

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

    def search_one(i, q):
        while True:
            if not isApi and progressBar.iscanceled():
                progressBar.update(0)
                progressBar.close()
                return
            iterator=100*int(len(searchersList)-len(left_searchers))/len(searchersList)
            if not isApi:
                progressBar.update(int(iterator), join_list(left_searchers, replace='.py'))
            searcherFile = q.get()
            searcher=searcherFile.replace('.py','')
            print "Thread %s: Searching at %s" % (i, searcher)
            result[searcherFile]=Searchers().searchWithSearcher(url, searcher)
            left_searchers.remove(searcherFile)
            q.task_done()

    for i in range(num_threads):
        worker = Thread(target=search_one, args=(i, queue))
        worker.setDaemon(True)
        worker.start()

    for searcherFile in searchersList:
        queue.put(searcherFile, timeout=wait_time)

    print "Main Thread Waiting"
    queue.join()
    print "Done"

    if not isApi:
        progressBar.update(0)
        progressBar.close()

    for k in result.keys():
        filesList.extend(result[k])
    return filesList


def join_list(l, char=', ', replace=''):
    string=''
    for i in l:
        string+=i.replace(replace,'')+char
    return string.rstrip(' ,')


class Contenters():
    def __init__(self):
        pass

    def first_time(self, scrapperDB_ver, language='ru'):
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
            if re.match('^(\w+)\.py$', searcherFile):
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


class WatchedDB:
    def __init__(self):
        dirname = xbmc.translatePath('special://temp')
        for subdir in ('xbmcup', __settings__.getAddonInfo('id').replace('plugin://', '').replace('/', '')):
            dirname = os.path.join(dirname, subdir)
            if not xbmcvfs.exists(dirname):
                xbmcvfs.mkdir(dirname)
        self.dbfilename = os.path.join(dirname, 'data.db3')
        if not xbmcvfs.exists(self.dbfilename):
            creat_db(self.dbfilename)
        self.dialog = xbmcgui.Dialog()

    def _get(self, id):
        self._connect()
        Debug('[WatchedDB][_get]: Checking ' + id)
        id = id.replace("'", "<&amp>").decode('utf-8', 'ignore')
        self.where = " where id='%s'" % (id)
        try:
            self.cur.execute('select rating from watched' + self.where)
        except:
            self.cur.execute('create table watched(addtime integer, rating integer, id varchar(32) PRIMARY KEY)')
            self.cur.execute('select rating from watched' + self.where)
        res = self.cur.fetchone()
        self._close()
        return res[0] if res else None

    def _get_all(self):
        self._connect()
        self.cur.execute('select id, rating from watched order by addtime desc')
        res = [[unicode(x[0]).replace("<&amp>", "'").encode('utf-8', 'ignore'), x[1]] for x in self.cur.fetchall()]
        self._close()
        return res

    def check(self, id, rating=0):
        ok1, ok3 = None, None
        db_rating = self._get(id)
        title = titlesync(id)
        TimeOut().go_offline()
        if getSettingAsBool("silentoffline"):
            if db_rating == None and rating >= 0:
                showMessage(__language__(30520), __language__(30522) % (str(rating)))
                ok1 = True
            elif db_rating >= 0 and rating != db_rating and rating > 0:
                showMessage(__language__(30520), __language__(30523) % (str(rating)))
                ok3 = True
            elif db_rating != None and rating == db_rating:
                showMessage(__language__(30520), __language__(30524) % (str(rating)))
        else:
            if db_rating == None and rating >= 0:
                if title:
                    title = title.encode('utf-8', 'ignore')
                    ok1 = self.dialog.yesno(__language__(30520), __language__(30525) % (str(rating)), title)
                else:
                    ok1 = True
            elif db_rating and rating != db_rating:
                if title:
                    title = title.encode('utf-8', 'ignore')
                    ok3 = self.dialog.yesno(__language__(30520), __language__(30526) % (str(db_rating), str(rating)),
                                            title)
                else:
                    ok3 = True
            elif db_rating == 0 and rating != db_rating:
                ok3 = True
            elif db_rating != None and rating == db_rating:
                showMessage(__language__(30520), __language__(30527) % (str(rating)))

        Debug('[WatchedDB][check]: rating: %s DB: %s, ok1: %s, ok3: %s' % (
            str(rating), str(db_rating), str(ok1), str(ok3)))

        if ok1:
            self._add(id, rating)
            return True
        if ok3:
            self._delete(id)
            self._add(id, rating)
            return True

    def onaccess(self):
        # Debug('[WatchedDB][onaccess]: Start')
        TimeOut().go_online()
        self._connect()
        try:
            self.cur.execute('select count(id) from watched')
        except:
            self.cur.execute('create table watched(addtime integer, rating integer, id varchar(32) PRIMARY KEY)')
            self.cur.execute('select count(id) from watched')
        x = self.cur.fetchone()
        res = int(x[0])
        self._close()
        i = 0

        if res > 0:
            # Debug('[WatchedDB][onaccess]: Found %s' % (str(res)))
            silentofflinesend = getSettingAsBool('silentofflinesend')
            if not silentofflinesend:
                ok2 = self.dialog.yesno(__language__(30521), __language__(30528) % (str(res)), __language__(30529))
            else:
                ok2 = True
            if ok2:
                for id, rating in self._get_all():
                    from addon import SyncXBMC

                    j = SyncXBMC(id, int(rating)).doaction()
                    if j:
                        i = i + int(j)
                        self._delete(id)
                        showMessage(__language__(30521), __language__(30530) % (i))
                __settings__.setSetting("duo_last_id", '')
            else:
                ok2 = self.dialog.yesno(__language__(30521), __language__(30531) % (str(res)))
                if ok2:
                    for id, rating in self._get_all():
                        self._delete(id)
        return res

    def _add(self, id, rating=0):
        __settings__.setSetting("duo_last_id", '')
        self._connect()
        id = id.replace("'", "<&amp>").decode('utf-8', 'ignore')
        Debug('[WatchedDB][_add]: Adding %s with rate %d' % (id, rating))
        self.cur.execute('insert into watched(addtime, rating, id) values(?,?,?)', (int(time.time()), int(rating), id))
        self.db.commit()
        self._close()

    def _delete(self, id):
        self._connect()
        id = id.replace("'", "<&amp>").decode('utf-8', 'ignore')
        self.cur.execute("delete from watched where id=('" + id + "')")
        self.db.commit()
        self._close()

    def count(self):
        return len(self._get_all())

    def _connect(self):
        self.db = sqlite.connect(self.dbfilename)
        self.cur = self.db.cursor()

    def _close(self):
        self.cur.close()
        self.db.close()


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
        print " fetchData(" + url + ") exception: " + str(e)
        return


def file_decode(filename):
    if not __settings__.getSetting('delete_russian') == 'true':
        try:
            filename = filename.decode('utf-8')  # ,'ignore')
        except:
            pass
    return filename


def file_encode(filename):
    if not __settings__.getSetting('delete_russian') == 'true':
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
    # Debug('Compare ' + filename_if.lower() + ' and ' + filename_if2.lower() + ' and ' + filename2.lower().split('.')[-1])
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
        try:
            self.cur.execute(
                'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads order by addtime DESC')
        except:
            Debug('[DownloadDB]: DELETE ' + str(self.filename))
            xbmcvfs.delete(self.filename)
            self._connect()
            self.cur.execute(
                'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads order by addtime DESC')
        x = self.cur.fetchall()
        self._close()
        return x if x else None

    def get(self, title):
        self._connect()
        try:
            self.cur.execute(
            'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads where title="' + decode(
                title) + '"')
        except:
            Debug('[DownloadDB]: DELETE ' + str(self.filename))
            xbmcvfs.delete(self.filename)
            self._connect()
            self.cur.execute(
            'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads where title="' + decode(
                title) + '"')
        x = self.cur.fetchone()
        self._close()
        return x if x else None

    def get_byaddtime(self, addtime):
        self._connect()
        self.cur.execute(
            'select addtime, title, path, type, jsoninfo, status, torrent, ind, lastupdate, storage from downloads where addtime="' + str(
                addtime) + '"')
        x = self.cur.fetchone()
        self._close()
        return x if x else None

    def get_status(self, title):
        self._connect()
        self.cur.execute('select status from downloads where title="' + decode(title) + '"')
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
        self.cur.execute(
            'UPDATE downloads SET jsoninfo = "' + urllib.quote_plus(json.dumps(info)) + '", lastupdate=' + str(
                int(time.time())) + ' where title="' + title + '"')
        self.db.commit()
        self._close()

    def update_status(self, addtime, status):
        self._connect()
        self.cur.execute('UPDATE downloads SET status = "' + status + '" where addtime="' + str(addtime) + '"')
        self.db.commit()
        self._close()

    def delete(self, addtime):
        self._connect()
        self.cur.execute('delete from downloads where addtime="' + str(addtime) + '"')
        self.db.commit()
        self._close()

    def clear(self):
        self._connect()
        self.cur.execute('delete from downloads')
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
                self.cur.execute('drop table downloads')
                first = True
                self.db.commit()
                self.cur.close()

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
    # Debug('[itemTVDB]:meta '+str(kwarg))
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
        for title, identifier in contentList:
            try:
                ext = title.split('.')[-1]
                if ext.lower() in extlist:
                    ids_video.append(str(identifier))
            except:
                pass
        if len(ids_video) > 1:
            break
    # print Debug('[get_ids_video]:'+str(ids_video))
    return ids_video


def first_run_230(delete_russian):
    ok = xbmcgui.Dialog().ok('< %s >' % Localization.localize('Torrenter Update 2.3.0'),
                                Localization.localize('I added custom searchers for Torrenter v2!'),
                                Localization.localize('Now you can use your login on trackers or write and install your own searcher!'))
    if not delete_russian:
        yes=xbmcgui.Dialog().yesno('< %s >' % Localization.localize('Torrenter Update 2.3.0'),
                                    Localization.localize('Would you like to install %s from "MyShows.me Kodi Repo" in Programs section?') % 'RuTrackerOrg',
                                    Localization.localize('Open installation window?'))
        if yes:
            xbmc.executebuiltin('XBMC.ActivateWindow(Addonbrowser,addons://search/%s)' % ('Torrenter Searcher'))
