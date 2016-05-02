# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import urllib
import urllib2
import cookielib
import base64
import mimetools
import json
import itertools
from StringIO import StringIO
import gzip
from functions import log, dump

import xbmc
import xbmcgui
import xbmcvfs

os.sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

import dopal.main

__plugin__ = sys.modules["__main__"].__plugin__
__settings__ = sys.modules["__main__"].__settings__
ROOT = sys.modules["__main__"].__root__  # .decode('utf-8').encode(sys.getfilesystemencoding())
userStorageDirectory = __settings__.getSetting("storage")
USERAGENT = "Mozilla/5.0 (Windows NT 6.1; rv:5.0) Gecko/20100101 Firefox/5.0"
URL = 'http://torrenter.host.org'
torrentFilesDirectory = 'torrents'
__addonpath__ = __settings__.getAddonInfo('path')
icon = __addonpath__ + '/icon.png'

RE = {
    'content-disposition': re.compile('attachment;\sfilename="*([^"\s]+)"|\s')
}

# ################################
#
# HTTP
#
# ################################

class HTTP:
    def __init__(self):
        self._dirname = xbmc.translatePath('special://temp')  # .decode('utf-8').encode('cp1251')
        for subdir in ('xbmcup', sys.argv[0].replace('plugin://', '').replace('/', '')):
            self._dirname = os.path.join(self._dirname, subdir)
            if not xbmcvfs.exists(self._dirname):
                xbmcvfs.mkdir(self._dirname)

    def fetch(self, request, **kwargs):
        self.con, self.fd, self.progress, self.cookies, self.request = None, None, None, None, request

        if not isinstance(self.request, HTTPRequest):
            self.request = HTTPRequest(url=self.request, **kwargs)

        self.response = HTTPResponse(self.request)

        # Debug('XBMCup: HTTP: request: ' + str(self.request))

        try:
            self._opener()
            self._fetch()
        except Exception, e:
            xbmc.log('XBMCup: HTTP: ' + str(e), xbmc.LOGERROR)
            if isinstance(e, urllib2.HTTPError):
                self.response.code = e.code
            self.response.error = e
        else:
            self.response.code = 200

        if self.fd:
            self.fd.close()
            self.fd = None

        if self.con:
            self.con.close()
            self.con = None

        if self.progress:
            self.progress.close()
            self.progress = None

        self.response.time = time.time() - self.response.time

        xbmc.log('XBMCup: HTTP: response: ' + str(self.response), xbmc.LOGDEBUG)

        return self.response

    def _opener(self):

        build = [urllib2.HTTPHandler()]

        if self.request.redirect:
            build.append(urllib2.HTTPRedirectHandler())

        if self.request.proxy_host and self.request.proxy_port:
            build.append(urllib2.ProxyHandler(
                {self.request.proxy_protocol: self.request.proxy_host + ':' + str(self.request.proxy_port)}))

            if self.request.proxy_username:
                proxy_auth_handler = urllib2.ProxyBasicAuthHandler()
                proxy_auth_handler.add_password('realm', 'uri', self.request.proxy_username,
                                                self.request.proxy_password)
                build.append(proxy_auth_handler)

        if self.request.cookies:
            self.request.cookies = os.path.join(self._dirname, self.request.cookies)
            self.cookies = cookielib.MozillaCookieJar()
            if os.path.isfile(self.request.cookies):
                self.cookies.load(self.request.cookies)
            build.append(urllib2.HTTPCookieProcessor(self.cookies))

        urllib2.install_opener(urllib2.build_opener(*build))

    def _fetch(self):
        params = {} if self.request.params is None else self.request.params

        if self.request.upload:
            boundary, upload = self._upload(self.request.upload, params)
            req = urllib2.Request(self.request.url)
            req.add_data(upload)
        else:

            if self.request.method == 'POST':
                if isinstance(params, dict) or isinstance(params, list):
                    params = urllib.urlencode(params)
                req = urllib2.Request(self.request.url, params)
            else:
                req = urllib2.Request(self.request.url)

        for key, value in self.request.headers.iteritems():
            req.add_header(key, value)

        if self.request.upload:
            req.add_header('Content-type', 'multipart/form-data; boundary=%s' % boundary)
            req.add_header('Content-length', len(upload))

        if self.request.auth_username and self.request.auth_password:
            req.add_header('Authorization', 'Basic %s' % base64.encodestring(
                ':'.join([self.request.auth_username, self.request.auth_password])).strip())

        # self.con = urllib2.urlopen(req, timeout=self.request.timeout)
        self.con = urllib2.urlopen(req)
        self.response.headers = self._headers(self.con.info())

        if self.request.download:
            self._download()
        else:
            if not self.response.headers.get('content-encoding') == 'gzip':
                self.response.body = self.con.read()
            else:
                buf = StringIO(self.con.read())
                f = gzip.GzipFile(fileobj=buf)
                self.response.body = f.read()

        if self.request.cookies:
            self.cookies.save(self.request.cookies)

    def _download(self):
        fd = open(self.request.download, 'wb')
        if self.request.progress:
            self.progress = xbmcgui.DialogProgress()
            self.progress.create(u'Download')

        bs = 1024 * 8
        size = -1
        read = 0
        name = None

        if self.request.progress:
            if 'content-length' in self.response.headers:
                size = int(self.response.headers['content-length'])
            if 'content-disposition' in self.response.headers:
                r = RE['content-disposition'].search(self.response.headers['content-disposition'])
                if r:
                    name = urllib.unquote(r.group(1))

        while 1:
            buf = self.con.read(bs)
            if buf == '':
                break
            read += len(buf)
            fd.write(buf)

            if self.request.progress:
                self.progress.update(*self._progress(read, size, name))

        self.response.filename = self.request.download

    def _upload(self, upload, params):
        res = []
        boundary = mimetools.choose_boundary()
        part_boundary = '--' + boundary

        if params:
            for name, value in params.iteritems():
                res.append([part_boundary, 'Content-Disposition: form-data; name="%s"' % name, '', value])

        if isinstance(upload, dict):
            upload = [upload]

        for obj in upload:
            name = obj.get('name')
            filename = obj.get('filename', 'default')
            content_type = obj.get('content-type')
            try:
                body = obj['body'].read()
            except AttributeError:
                body = obj['body']

            if content_type:
                res.append([part_boundary,
                            'Content-Disposition: file; name="%s"; filename="%s"' % (name, urllib.quote(filename)),
                            'Content-Type: %s' % content_type, '', body])
            else:
                res.append([part_boundary,
                            'Content-Disposition: file; name="%s"; filename="%s"' % (name, urllib.quote(filename)), '',
                            body])

        result = list(itertools.chain(*res))
        result.append('--' + boundary + '--')
        result.append('')
        return boundary, '\r\n'.join(result)

    def _headers(self, raw):
        headers = {}
        for line in raw.headers:
            pair = line.split(':', 1)
            if len(pair) == 2:
                tag = pair[0].lower().strip()
                value = pair[1].strip()
                if tag and value:
                    headers[tag] = value
        return headers

    def _progress(self, read, size, name):
        res = []
        if size < 0:
            res.append(1)
        else:
            res.append(int(float(read) / (float(size) / 100.0)))
        if name:
            res.append(u'File: ' + name)
        if size != -1:
            res.append(u'Size: ' + self._human(size))
        res.append(u'Load: ' + self._human(read))
        return res

    def _human(self, size):
        human = None
        for h, f in (('KB', 1024), ('MB', 1024 * 1024), ('GB', 1024 * 1024 * 1024), ('TB', 1024 * 1024 * 1024 * 1024)):
            if size / f > 0:
                human = h
                factor = f
            else:
                break
        if human is None:
            return (u'%10.1f %s' % (size, u'byte')).replace(u'.0', u'')
        else:
            return u'%10.2f %s' % (float(size) / float(factor), human)


class HTTPRequest:
    def __init__(self, url, method='GET', headers=None, cookies=None, params=None, upload=None, download=None,
                 progress=False, auth_username=None, auth_password=None, proxy_protocol='http', proxy_host=None,
                 proxy_port=None, proxy_username=None, proxy_password='', timeout=20.0, redirect=True, gzip=False):
        if headers is None:
            headers = {}

        self.url = url
        self.method = method
        self.headers = headers

        self.cookies = cookies

        self.params = params

        self.upload = upload
        self.download = download
        self.progress = progress

        self.auth_username = auth_username
        self.auth_password = auth_password

        self.proxy_protocol = proxy_protocol
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

        self.timeout = timeout

        self.redirect = redirect

        self.gzip = gzip

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, ','.join('%s=%r' % i for i in self.__dict__.iteritems()))


class HTTPResponse:
    def __init__(self, request):
        self.request = request
        self.code = None
        self.headers = {}
        self.error = None
        self.body = None
        self.filename = None
        self.time = time.time()

    def __repr__(self):
        args = ','.join('%s=%r' % i for i in self.__dict__.iteritems() if i[0] != 'body')
        if self.body:
            args += ',body=<data>'
        else:
            args += ',body=None'
        return '%s(%s)' % (self.__class__.__name__, args)


class UTorrent:
    def config(self, login, password, host, port, url=None):
        self.login = login
        self.password = password

        self.url = 'http://' + host
        if port:
            self.url += ':' + str(port)
        self.url += '/gui/'

        self.http = HTTP()

        self.re = {
            'cookie': re.compile('GUID=([^;]+);'),
            'token': re.compile("<div[^>]+id='token'[^>]*>([^<]+)</div>")
        }

    def listdirs(self):
        obj = self.action('action=list-dirs')
        if not obj:
            return False
        items = []
        clean = []
        for r in obj.get('download-dirs', []):
            available = int(r['available'])
            if available > 1024:
                memory = '[%s GB]' % str(available / 1024)
            else:
                memory = '[%s MB]' % str(available)
            items.append(r['path'] + ' ' + memory)
            path = r['path']
            if path[len(path) - 1:] != '\\': path += '\\'
            clean.append(path)
        return items, clean

    def list(self):
        obj = self.action('list=1')
        if not obj:
            return False

        res = []
        for r in obj.get('torrents', []):
            res.append({
                'id': r[0],
                'status': self.get_status(r[1], r[4] / 10),
                'name': r[2],
                'size': r[3],
                'progress': r[4] / 10,
                'download': r[5],
                'upload': r[6],
                'ratio': float(r[7]) / 1000,
                'upspeed': r[8],
                'downspeed': r[9],
                'eta': r[10],
                'peer': r[12] + r[14],
                'leach': r[12],
                'seed': r[14],
                'add': r[23],
                'finish': r[24],
                'dir': r[26]
            })

        return res

    def listfiles(self, id):
        obj = self.action('action=getfiles&hash=' + id)
        if not obj:
            return None
        res = []
        i = -1

        for x in obj['files'][1]:
            i += 1
            if x[1] >= 1024 * 1024 * 1024:
                size = str(x[1] / (1024 * 1024 * 1024)) + 'GB'
            elif x[1] >= 1024 * 1024:
                size = str(x[1] / (1024 * 1024)) + 'MB'
            elif x[1] >= 1024:
                size = str(x[1] / 1024) + 'KB'
            else:
                size = str(x[1]) + 'B'
            res.append((x[0], (int(x[2] * 100 / x[1])), i, size))
        return res

    def dirid(self, dirname):
        if __settings__.getSetting("torrent_save") == '0':
            dirid = self.listdirs()[1].index(dirname)
        else:
            dirname = __settings__.getSetting("torrent_dir")
            clean = self.listdirs()[1]
            try:
                dirid = clean.index(dirname)
            except:
                dirid = 0
        return dirid

    def add(self, torrent, dirname):
        dirid = self.dirid(dirname)
        res = self.action('action=add-file&download_dir=' + str(dirid),
                          {'name': 'torrent_file', 'download_dir': str(dirid),
                           'content-type': 'application/x-bittorrent', 'body': torrent})
        return True if res else None

    def add_url(self, torrent, dirname):
        dirid = self.dirid(dirname)
        res = self.action('action=add-url&download_dir=' + str(dirid) + '&s=' + urllib.quote(torrent))
        return True if res else None

    def setprio(self, id, ind):
        obj = self.action('action=getfiles&hash=' + id)

        if not obj or ind == None:
            return None

        i = -1
        for x in obj['files'][1]:
            i += 1
            if x[3] == 2: self.setprio_simple(id, '0', i)

        res = self.setprio_simple(id, '3', ind)

        return True if res else None

    def setprio_simple(self, id, prio, ind):
        obj = self.action('action=setprio&hash=%s&p=%s&f=%s' % (id, prio, ind))

        if not obj or ind == None:
            return None

        return True if obj else None

    def setprio_simple_multi(self, menu):
        for hash, action, ind in menu:
            self.setprio_simple(hash, action, ind)

    def action(self, uri, upload=None):
        cookie, token = self.get_token()
        if not cookie:
            return None

        req = HTTPRequest(self.url + '?' + uri + '&token=' + token, headers={'Cookie': cookie},
                          auth_username=self.login, auth_password=self.password)
        if upload:
            req.upload = upload

        response = self.http.fetch(req)
        if response.error:
            return None
        else:
            try:
                obj = json.loads(response.body)
            except:
                return None
            else:
                return obj

    def action_simple(self, action, id):
        obj = self.action('action=%s&hash=%s' % (action, id))
        return True if obj else None

    def get_token(self):
        response = self.http.fetch(self.url + 'token.html', auth_username=self.login, auth_password=self.password)
        if response.error:
            return None, None

        r = self.re['cookie'].search(response.headers.get('set-cookie', ''))
        if r:
            cookie = r.group(1).strip()
            r = self.re['token'].search(response.body)
            if r:
                token = r.group(1).strip()
                if cookie and token:
                    return 'GUID=' + cookie, token

        return None, None

    def get_status(self, status, progress):
        mapping = {
            'error': 'stopped',
            'paused': 'stopped',
            'forcepaused': 'stopped',
            'stopped': 'stopped',
            'notloaded': 'check_pending',
            'checked': 'checking',
            'queued': 'download_pending',
            'downloading': 'downloading',
            'forcedownloading': 'downloading',
            'finished': 'seed_pending',
            'queuedseed': 'seed_pending',
            'seeding': 'seeding',
            'forceseeding': 'seeding'
        }
        return mapping[self.get_status_raw(status, progress)]

    def get_status_raw(self, status, progress):
        """
            Return status: notloaded, error, checked,
                           paused, forcepaused,
                           queued,
                           downloading,
                           finished, forcedownloading
                           queuedseed, seeding, forceseeding
        """

        started = bool(status & 1)
        checking = bool(status & 2)
        start_after_check = bool(status & 4)
        checked = bool(status & 8)
        error = bool(status & 16)
        paused = bool(status & 32)
        queued = bool(status & 64)
        loaded = bool(status & 128)

        if not loaded:
            return 'notloaded'

        if error:
            return 'error'

        if checking:
            return 'checked'

        if paused:
            if queued:
                return 'paused'
            else:
                return 'forcepaused'

        if progress == 100:

            if queued:
                if started:
                    return 'seeding'
                else:
                    return 'queuedseed'

            else:
                if started:
                    return 'forceseeding'
                else:
                    return 'finished'
        else:

            if queued:
                if started:
                    return 'downloading'
                else:
                    return 'queued'

            else:
                if started:
                    return 'forcedownloading'

        return 'stopped'


class Transmission:
    def config(self, login, password, host, port, url):
        self.login = login
        self.password = password

        self.url = 'http://' + host
        if port:
            self.url += ':' + str(port)

        if url[0] != '/':
            url = '/' + url
        if url[-1] != '/':
            url += '/'

        self.url += url

        self.http = HTTP()

        self.token = '0'

    def list(self):
        obj = self.action({'method': 'torrent-get', 'arguments': {
            'fields': ['id', 'status', 'name', 'totalSize', 'sizeWhenDone', 'leftUntilDone', 'downloadedEver',
                       'uploadedEver', 'uploadRatio', 'rateUpload', 'rateDownload', 'eta', 'peersConnected',
                       'peersFrom',
                       'addedDate', 'doneDate', 'downloadDir', 'fileStats', 'peersConnected', 'peersGettingFromUs',
                       'peersSendingToUs']}})
        if obj is None:
            return False

        res = []
        for r in obj['arguments'].get('torrents', []):
            if len(r['fileStats']) > 1:
                res.append({
                    'id': str(r['id']),
                    'status': self.get_status(r['status']),
                    'name': r['name'],
                    'size': r['totalSize'],
                    'progress': 0 if not r['sizeWhenDone'] else int(
                        100.0 * float(r['sizeWhenDone'] - r['leftUntilDone']) / float(r['sizeWhenDone'])),
                    'download': r['downloadedEver'],
                    'upload': r['uploadedEver'],
                    'upspeed': r['rateUpload'],
                    'downspeed': r['rateDownload'],
                    'ratio': float(r['uploadRatio']),
                    'eta': r['eta'],
                    'peer': r['peersConnected'],
                    'seed': r['peersSendingToUs'],
                    'leech': r['peersGettingFromUs'],
                    'add': r['addedDate'],
                    'finish': r['doneDate'],
                    'dir': os.path.join(r['downloadDir'], r['name'])
                })
            else:
                res.append({
                    'id': str(r['id']),
                    'status': self.get_status(r['status']),
                    'name': r['name'],
                    'size': r['totalSize'],
                    'progress': 0 if not r['sizeWhenDone'] else int(
                        100.0 * float(r['sizeWhenDone'] - r['leftUntilDone']) / float(r['sizeWhenDone'])),
                    'download': r['downloadedEver'],
                    'upload': r['uploadedEver'],
                    'upspeed': r['rateUpload'],
                    'downspeed': r['rateDownload'],
                    'ratio': float(r['uploadRatio']),
                    'eta': r['eta'],
                    'peer': r['peersConnected'],
                    'seed': r['peersSendingToUs'],
                    'leech': r['peersGettingFromUs'],
                    'add': r['addedDate'],
                    'finish': r['doneDate'],
                    'dir': r['downloadDir']
                })

        return res

    def listdirs(self):
        obj = self.action({'method': 'session-get'})
        if obj is None:
            return False

        res = [obj['arguments'].get('download-dir')]
        # Debug('[Transmission][listdirs]: %s' % (str(res)))
        return res, res

    def listfiles(self, id):
        obj = self.action({"method": "torrent-get", "arguments": {
            "fields": ["id", "activityDate", "corruptEver", "desiredAvailable", "downloadedEver", "fileStats",
                       "haveUnchecked", "haveValid", "peers", "startDate", "trackerStats", "comment", "creator",
                       "dateCreated", "files", "hashString", "isPrivate", "pieceCount", "pieceSize"],
            "ids": [int(id)]}})['arguments']['torrents'][0]
        if obj is None:
            return None

        res = []
        i = -1

        lenf = len(obj['files'])
        for x in obj['files']:
            i += 1
            if x['length'] >= 1024 * 1024 * 1024:
                size = str(x['length'] / (1024 * 1024 * 1024)) + 'GB'
            elif x['length'] >= 1024 * 1024:
                size = str(x['length'] / (1024 * 1024)) + 'MB'
            elif x['length'] >= 1024:
                size = str(x['length'] / 1024) + 'KB'
            else:
                size = str(x['length']) + 'B'
            if lenf > 1:
                x['name'] = x['name'].strip('/\\').replace('\\', '/')
                x['name'] = x['name'].replace(x['name'].split('/')[0] + '/', '')
            res.append([x['name'], (int(x['bytesCompleted'] * 100 / x['length'])), i, size])
        return res

    def add(self, torrent, dirname):
        if self.action({'method': 'torrent-add',
                        'arguments': {'download-dir': dirname, 'metainfo': base64.b64encode(torrent)}}) is None:
            return None
        return True

    def add_url(self, torrent, dirname):
        if self.action({'method': 'torrent-add', 'arguments': {'download-dir': dirname, 'filename': torrent}}) is None:
            return None
        return True

    def setprio(self, id, ind):
        obj = self.action({"method": "torrent-get", "arguments": {"fields": ["id", "fileStats", "files"],
                                                                  "ids": [int(id)]}})['arguments']['torrents'][0]
        if not obj or ind == None:
            return None

        inds = []
        i = -1

        for x in obj['fileStats']:
            i += 1
            if x['wanted'] == True and x['priority'] == 0:
                inds.append(i)

        if len(inds) > 1: self.action(
            {"method": "torrent-set", "arguments": {"ids": [int(id)], "priority-high": inds, "files-unwanted": inds}})

        res = self.setprio_simple(id, '3', ind)

        # self.action_simple('start',id)

        return True if res else None

    def setprio_simple(self, id, prio, ind):
        if ind == None:
            return None

        res = None
        inds = [int(ind)]

        if prio == '3':
            res = self.action(
                {"method": "torrent-set", "arguments": {"ids": [int(id)], "priority-high": inds, "files-wanted": inds}})
        elif prio == '0':
            res = self.action({"method": "torrent-set",
                               "arguments": {"ids": [int(id)], "priority-high": inds, "files-unwanted": inds}})

        return True if res else None

    def setprio_simple_multi(self, menu):
        id = menu[0][0]
        prio = menu[0][1]
        res = None

        inds = []
        for hash, action, ind in menu:
            inds.append(int(ind))

        if prio == '3':
            res = self.action(
                {"method": "torrent-set", "arguments": {"ids": [int(id)], "priority-high": inds, "files-wanted": inds}})
        elif prio == '0':
            res = self.action({"method": "torrent-set",
                               "arguments": {"ids": [int(id)], "priority-high": inds, "files-unwanted": inds}})
        return True if res else None

    def action(self, request):
        try:
            jsobj = json.dumps(request)
        except:
            return None
        else:

            while True:
                # пробуем сделать запрос
                if self.login:
                    response = self.http.fetch(self.url + 'rpc/', method='POST', params=jsobj,
                                               headers={'X-Transmission-Session-Id': self.token,
                                                        'X-Requested-With': 'XMLHttpRequest',
                                                        'Content-Type': 'charset=UTF-8'}, auth_username=self.login,
                                               auth_password=self.password)
                else:
                    response = self.http.fetch(self.url + 'rpc/', method='POST', params=jsobj,
                                               headers={'X-Transmission-Session-Id': self.token,
                                                        'X-Requested-With': 'XMLHttpRequest',
                                                        'Content-Type': 'charset=UTF-8'})

                if response.error:

                    # требуется авторизация?
                    if response.code == 401:
                        if not self.get_auth():
                            return None

                    # требуется новый токен?
                    elif response.code == 409:
                        if not self.get_token(response.error):
                            return None

                    else:
                        return None

                else:
                    try:
                        obj = json.loads(response.body)
                    except:
                        return None
                    else:
                        return obj

    def action_simple(self, action, id):
        actions = {'start': {"method": "torrent-start", "arguments": {"ids": [int(id)]}},
                   'stop': {"method": "torrent-stop", "arguments": {"ids": [int(id)]}},
                   'remove': {"method": "torrent-remove", "arguments": {"ids": [int(id)], "delete-local-data": False}},
                   'removedata': {"method": "torrent-remove",
                                  "arguments": {"ids": [int(id)], "delete-local-data": True}}}
        obj = self.action(actions[action])
        return True if obj else None

    def get_auth(self):
        response = self.http.fetch(self.url, auth_username=self.login, auth_password=self.password)
        if response.error:
            if response.code == 409:
                return self.get_token(response.error)
        return False

    def get_token(self, error):
        token = error.headers.get('x-transmission-session-id')
        if not token:
            return False
        self.token = token
        return True

    def get_status(self, code):
        mapping = {
            0: 'stopped',
            1: 'check_pending',
            2: 'checking',
            3: 'download_pending',
            4: 'downloading',
            5: 'seed_pending',
            6: 'seeding'
        }
        return mapping[code]


class qBittorrent:
    def config(self, login, password, host, port, url):
        self.login = login
        self.password = password

        self.url = 'http://'+host
        if port:
            self.url += ':' + str(port)
        self.url += url

        self.http = HTTP()
        self.cookie = self.get_auth()

    def list(self):
        obj = self.action('/query/torrents')
        log('[list]:'+str(obj))
        if obj is None:
            return False

        res = []
        if len(obj) > 0:
            for r in obj:
                add = {
                    'id': r['hash'],
                    'status': self.get_status(r['state']),
                    'name': r['name'],
                    'size': r['size'],
                    'progress': round(r['progress'], 4)*100,
                    'upspeed': r['upspeed'],
                    'downspeed': r['dlspeed'],
                    'ratio': round(r['ratio'], 2),
                    'eta': r['eta'],
                    'seed': r['num_seeds'],
                    'leech': r['num_leechs'],
                    'dir': r['save_path']
                }
                flist = self.action('/query/propertiesFiles/'+r['hash'])
                if len(flist) > 1: add['dir'] = os.path.join(r['save_path'], r['name'])
                res.append(add)
        return res

    def listdirs(self):
        obj = self.action('/query/preferences')
        log('[listdirs]:'+str(obj))
        if obj is None:
            return False

        try:
            res = [obj['save_path']]
        except:
            res = [None]
        return res, res

    def listfiles(self, id):
        obj = self.action('/query/propertiesFiles/'+id)
        log('[listfiles]:'+str(obj))
        i = -1
        if obj is None:
            return None

        res = []

        if len(obj) == 1:
            strip_path = None
        else:
            tlist = self.list()
            for t in tlist:
                if t['id']==id:
                    strip_path = t['name']
                    break
                strip_path = None

        for x in obj:
            if x['size'] >= 1024 * 1024 * 1024:
                size = str(x['size'] / (1024 * 1024 * 1024)) + 'GB'
            elif x['size'] >= 1024 * 1024:
                size = str(x['size'] / (1024 * 1024)) + 'MB'
            elif x['size'] >= 1024:
                size = str(x['size'] / 1024) + 'KB'
            else:
                size = str(x['size']) + 'B'
            if strip_path:
                path = x['name'].lstrip(strip_path).lstrip('\\')
            else:
                path = x['name']

            if x['priority'] == 0:
                path = path.replace('.unwanted\\','')

            if x.get('progress'):
                percent = int(x['progress'] * 100)
            else:
                percent = 0

            i += 1
            res.append([path.replace('\\','/'), percent, i, size])

        return res

    def get_prio(self, id):
        res = []
        obj = self.action('/query/propertiesFiles/'+id)
        log('[get_prio]:'+str(obj))
        if obj is None:
            return None
        for f in obj:
            res.append(f['priority'])
        log('[get_prio]:'+str(res))
        return res

    def add(self, torrent, dirname):

        upload={'name': 'torrent_file', 'filename': 'and_nothing_else_matters.torrent',
                           'content-type': 'application/x-bittorrent', 'body': torrent}
        res = self.action('/command/upload', upload=upload)

        if res:
            return True

    def add_url(self, torrent, dirname):

        upload={'name': 'urls', 'content-type': 'application/x-bittorrent', 'body': torrent}
        res = self.action('/command/download', upload=upload)

        if res:
            return True

    def setprio(self, id, ind):
        obj = self.action('/query/propertiesFiles/'+id)

        if not obj or ind == None:
            return None

        i = -1
        for x in obj:
            i += 1
            print str(x)
            if x['priority'] == 1: self.setprio_simple(id, '0', i)

        res = self.setprio_simple(id, '7', ind)

        return True if res else None

    def setprio_simple(self, id, prio, ind):
        #log(str((id, prio, ind)))
        if prio == '3': prio = '7'
        params = {'hash':id, 'priority':prio, 'id': ind}
        obj = self.action_post('/command/setFilePrio', params)
        if not obj or ind == None:
            return None

        return True if obj else None

    def setprio_simple_multi(self, menu):
        for hash, action, ind in menu:
            self.setprio_simple(hash, action, ind)

    def action(self, uri, upload=None):
        req = HTTPRequest(self.url + uri, headers={'Cookie': self.cookie})

        if upload:
            req.upload = upload

        response = self.http.fetch(req)

        if response.error:
            return None

        if response.code == 200 and upload:
            return True

        else:
            try:
                obj = json.loads(response.body)
            except:
                return None
            else:
                return obj

    def action_post(self, uri, params=None):
        response = self.http.fetch(self.url + uri, headers={'Cookie': self.cookie},
                                   method='POST', params=params, gzip=True,)

        #dump(response)
        if response.error:
            return None

        if response.code == 200:
            return True

        return response

    def action_simple(self, action, id):
        actions = {'start': ['/command/resume',{'hash':id,}],
                   'stop': ['/command/pause',{'hash':id,}],
                   'remove': ['/command/delete',{'hashes':id}],
                   'removedata': ['/command/deletePerm',{'hashes':id}]}
        obj = self.action_post(actions[action][0],actions[action][1])
        return True if obj else None

    def get_auth(self):
        params = {"username": self.login, "password": self.password}
        response = self.http.fetch(self.url + '/login', method='POST', params=params, gzip=True)
        if response.error:
            return None

        r = re.compile('SID=([^;]+);').search(response.headers.get('set-cookie', ''))
        if r:
            cookie = r.group(1).strip()
            return 'SID=' + cookie

    def get_status(self, code):
        mapping = {
            'error': 'stopped',
            'pausedUP': 'seed_pending',
            'checkingUP': 'checking',
            'checkingDL': 'checking',
            'pausedDL': 'stopped',
            'queuedUP': 'seeding',
            'queuedDL': 'stopped',
            'downloading': 'downloading',
            'stalledDL': 'downloading',
            'uploading': 'seeding',
            'stalledUP': 'seeding',
        }
        if code in mapping:
            return mapping[code]
        else:
            return 'unknown'


class Deluge:
    def config(self, login, password, host, port, url):
        self.login = login
        self.password = password

        self.url = 'http://'+host
        if port:
            self.url += ':' + str(port)
        self.url += url
        #log(str(self.url))
        self.http = HTTP()

    def get_info(self):
        obj = self.action({"method": "web.update_ui",
                           "params": [[], {}], "id": 1})
        return obj

    def list(self):
        obj = self.get_info()
        if obj is None:
            return False

        res = []
        if len(obj['result'].get('torrents')) > 0:
            for k in obj['result'].get('torrents').keys():
                r = obj['result']['torrents'][k]
                add = {
                    'id': str(k),
                    'status': self.get_status(r['state']),
                    'name': r['name'],
                    'size': r['total_wanted'],
                    'progress': round(r['progress'], 2),
                    'download': r['total_done'],
                    'upload': r['total_uploaded'],
                    'upspeed': r['upload_payload_rate'],
                    'downspeed': r['download_payload_rate'],
                    'ratio': round(r['ratio'], 2),
                    'eta': r['eta'],
                    'peer': r['total_peers'],
                    'seed': r['num_seeds'],
                    'leech': r['num_peers'],
                    'add': r['time_added'],
                    'dir': r['save_path']
                }
                if len(r['files']) > 1: add['dir'] = os.path.join(r['save_path'], r['name'])
                res.append(add)
        return res

    def listdirs(self):
        obj = self.action({"method": "core.get_config", "params": [], "id": 5})
        if obj is None:
            return False

        try:
            res = [obj['result'].get('download_location')]
        except:
            res = [None]
        return res, res

    def listfiles(self, id):
        obj = self.get_info()
        i = 0
        if obj is None:
            return None

        res = []
        obj = obj['result']['torrents'][id]
        # print str(obj)
        if len(obj['files']) == 1:
            strip_path = None
        else:
            strip_path = obj['name']

        for x in obj['files']:
            if x['size'] >= 1024 * 1024 * 1024:
                size = str(x['size'] / (1024 * 1024 * 1024)) + 'GB'
            elif x['size'] >= 1024 * 1024:
                size = str(x['size'] / (1024 * 1024)) + 'MB'
            elif x['size'] >= 1024:
                size = str(x['size'] / 1024) + 'KB'
            else:
                size = str(x['size']) + 'B'
            if strip_path:
                path = x['path'].lstrip(strip_path).lstrip('/')
            else:
                path = x['path']

            if x.get('progress'):
                percent = int(x['progress'] * 100)
            elif obj.get('file_progress') and len(obj['file_progress']) >= i:
                percent = int(obj['file_progress'][i] * 100)
            else:
                percent = 0

            i += 1
            res.append([path, percent, x['index'], size])

        return res

    def get_prio(self, id):
        obj = self.get_info()
        if obj is None:
            return None
        res = obj['result']['torrents'][id]['file_priorities']
        return res

    def add(self, torrent, dirname):
        torrentFile = os.path.join(self.http._dirname, 'deluge.torrent')
        if self.action({'method': 'core.add_torrent_file',
                        'params': [torrentFile,
                                   base64.b64encode(torrent), {"download_path": dirname}], "id": 3}) is None:
            return None
        return True

    def add_url(self, torrent, dirname):
        if re.match("^magnet\:.+$", torrent):
            if self.action({'method': 'core.add_torrent_magnet', 'params': [torrent,
                                                                            {'download_path': dirname}],
                            "id": 3}) is None:
                return None
        else:
            if self.action({"method": "core.add_torrent_url", "params": [torrent, {'download_path': dirname}],
                            "id": 3}) is None:
                return None
        return True

    def setprio(self, id, ind):
        i = -1
        prios = self.get_prio(id)

        for p in prios:
            i = i + 1
            if p == 1:
                prios.pop(i)
                prios.insert(i, 0)

        prios.pop(int(ind))
        prios.insert(int(ind), 7)

        if self.action({"method": "core.set_torrent_file_priorities", "params": [id, prios], "id": 6}) is None:
            return None

        return True

    def setprio_simple(self, id, prio, ind):
        prios = self.get_prio(id)

        if ind != None:
            prios.pop(int(ind))
            if prio == '3':
                prios.insert(int(ind), 7)
            elif prio == '0':
                prios.insert(int(ind), 0)

        if self.action({"method": "core.set_torrent_file_priorities", "params": [id, prios], "id": 6}) is None:
            return None
        return True

    def setprio_simple_multi(self, menu):
        id = menu[0][0]
        prios = self.get_prio(id)

        for hash, action, ind in menu:
            prios.pop(int(ind))
            if action == '3':
                prios.insert(int(ind), 7)
            elif action == '0':
                prios.insert(int(ind), 0)

        if self.action({"method": "core.set_torrent_file_priorities", "params": [id, prios], "id": 6}) is None:
            return None

    def action(self, request):
        cookie = self.get_auth()
        if not cookie:
            return None

        try:
            jsobj = json.dumps(request)
        except:
            return None
        else:
            response = self.http.fetch(self.url + '/json', method='POST', params=jsobj,
                                       headers={'X-Requested-With': 'XMLHttpRequest', 'Cookie': cookie,
                                                'Content-Type': 'application/json; charset=UTF-8'})

            if response.error:
                return None

            else:
                try:
                    obj = json.loads(response.body)
                except:
                    return None
                else:
                    return obj

    def action_simple(self, action, id):
        actions = {'start': {"method": "core.resume_torrent", "params": [[id]], "id": 4},
                   'stop': {"method": "core.pause_torrent", "params": [[id]], "id": 4},
                   'remove': {"method": "core.remove_torrent", "params": [id, False], "id": 4},
                   'removedata': {"method": "core.remove_torrent", "params": [id, True], "id": 4}}
        obj = self.action(actions[action])
        return True if obj else None

    def get_auth(self):
        params = json.dumps({"method": "auth.login", "params": [self.password], "id": 0})
        response = self.http.fetch(self.url + '/json', method='POST', params=params, gzip=True,
                                   headers={'X-Requested-With': 'XMLHttpRequest',
                                            'Content-Type': 'application/json; charset=UTF-8'})
        if response.error:
            return None

        auth = json.loads(response.body)
        if auth["result"] == False:
            return False
        else:
            r = re.compile('_session_id=([^;]+);').search(response.headers.get('set-cookie', ''))
            if r:
                cookie = r.group(1).strip()
                return '_session_id=' + cookie

    def get_status(self, code):
        mapping = {
            'Queued': 'stopped',
            'Error': 'stopped',
            'Checking': 'checking',
            'Paused': 'seed_pending',
            'Downloading': 'downloading',
            'Active': 'seed_pending',
            'Seeding': 'seeding'
        }
        return mapping[code]


class Vuze:
    def config(self, login, password, host, port, url):
        self.login = login
        self.password = password

        self.connection = dopal.main.make_connection(host=host, port=port, user=login, password=password)
        try:
            self.interface = self.connection.getPluginInterface()
            self.downloads = self.interface.getDownloadManager().getDownloads()
        except:
            self.downloads = False

    def list(self):

        if self.downloads == False:
            return self.downloads

        i = -1
        res = []
        for r in self.downloads:
            i += 1
            res.append({
                'id': str(i),
                'status': self.get_status(int(getattr(r, 'state'))),
                'name': getattr(getattr(r, 'torrent'), 'name'),
                'size': getattr(getattr(r, 'torrent'), 'size'),
                'progress': round(
                    float(long(r.stats.downloaded) + 1 / (long(r.stats.downloaded) + long(r.stats.remaining) + 1)),
                    4) * 100,
                'download': float(getattr(getattr(r, 'stats'), 'downloaded')),
                'upload': getattr(getattr(r, 'stats'), 'uploaded'),
                # 'upspeed': r['rateUpload'],
                # 'downspeed': r['rateDownload'],
                'ratio': float(r.stats.share_ratio) / 1000,
                'eta': getattr(getattr(r, 'stats'), 'eta'),
                'peer': getattr(getattr(r, 'scrape_result'), 'non_seed_count') + getattr(getattr(r, 'scrape_result'),
                                                                                         'seed_count'),
                'seed': getattr(getattr(r, 'scrape_result'), 'seed_count'),
                'leech': getattr(getattr(r, 'scrape_result'), 'non_seed_count'),
                'add': getattr(r, 'creation_time'),
                'finish': getattr(r, 'creation_time') + getattr(getattr(r, 'stats'), 'seconds_downloading'),
                'dir': getattr(r, 'save_path')
            })

        return res

    def listdirs(self):
        res = []
        return res, res

    def listfiles(self, id):
        obj = self.downloads[int(id)].getDiskManagerFileInfo()
        if obj is None:
            return None

        res = []
        i = -1

        for x in obj:
            i += 1
            if long(x.length) >= 1024 * 1024 * 1024:
                size = str(long(x.length) / (1024 * 1024 * 1024)) + 'GB'
            elif long(x.length) >= 1024 * 1024:
                size = str(long(x.length) / (1024 * 1024)) + 'MB'
            elif x.length >= 1024:
                size = str(long(x.length) / 1024) + 'KB'
            else:
                size = str(long(x.length)) + 'B'

            if '\\' in x.file:
                title = x.file.split('\\')[-1]
            elif '/' in x.file:
                title = x.file.split('/')[-1]
            else:
                title = x.file
            res.append([title, (long(x.downloaded * 100 / long(x.length))), i, size])
        return res

    def add(self, torrent, dirname):
        torrent = self.interface.getTorrentManager().createFromBEncodedData(torrent)
        obj = self.interface.getDownloadManager().addDownload(torrent)
        return True if obj else None

    def add_url(self, torrent, dirname):

        obj = self.interface.getDownloadManager().addDownload(torrent)
        return True if obj else None

    def setprio(self, id, ind):
        self.setprioobj = self.downloads[int(id)].getDiskManagerFileInfo()
        # -1 low, 0 normal, 1 high

        if not self.setprioobj or ind == None:
            return None

        i = -1
        for x in self.setprioobj:
            i += 1
            if not x.isPriority(): self.setprio_simple_vuze(id, i, skip=True, prio=-1)

        res = self.setprio_simple_vuze(id, ind, skip=False, prio=1)

        return True if res else None

    def setprio_simple(self, id, prio, ind):
        if ind == None:
            return None

        res = None

        if prio == '0':
            res = self.setprio_simple_vuze(id, ind, skip=True, prio=-1)
        elif prio == '3':
            res = self.setprio_simple_vuze(id, ind, skip=False, prio=1)

    def setprio_simple_vuze(self, id, ind, skip=None, prio=None):
        obj = None

        self.setprioobj = self.downloads[int(id)].getDiskManagerFileInfo()

        if prio != None:
            obj = self.setprioobj[int(ind)].setNumericPriority(prio)

        if skip != None:
            obj = self.setprioobj[int(ind)].setSkipped(skip)

        if not obj or ind == None:
            return None
        time.sleep(0.1)
        return True if obj else None

    def setprio_simple_multi(self, menu):
        for hash, action, ind in menu:
            self.setprio_simple(hash, action, ind)

    def action_simple(self, action, id):
        torrent = self.downloads[int(id)]
        obj = None
        if action == 'start':
            obj = torrent.restart()
        if action == 'stop':
            obj = torrent.stopDownload()
        if action == 'remove':
            obj = torrent.remove()
        if action == 'removedata':
            obj = torrent.remove(True, True)

        return True if obj else None

    def get_status(self, status):
        mapping = ['stopped', 'download_pending', 'download_pending', 'download_pending', 'downloading', 'seeding',
                   'seed_pending', 'stopped', 'stopped', 'download_pending']
        return mapping[status]


class Download():
    def __init__(self):
        self.handle()

    def handle(self):
        config = self.get_torrent_client()

        if self.client == 'utorrent':
            self.client = UTorrent()

        elif self.client == 'transmission':
            self.client = Transmission()

        elif self.client == 'vuze':
            self.client = Vuze()

        elif self.client == 'deluge':
            self.client = Deluge()

        elif self.client == 'qbittorrent':
            self.client = qBittorrent()

        self.client.config(host=config['host'], port=config['port'], login=config['login'], password=config['password'],
                           url=config['url'])
        # print(self.client.list())
        return True

    def get_torrent_client(self):
        self.setting = __settings__
        client = self.setting.getSetting("torrent")
        config = {}
        if client == '0':
            self.client = 'utorrent'
            config = {
                'host': self.setting.getSetting("torrent_utorrent_host"),
                'port': self.setting.getSetting("torrent_utorrent_port"),
                'url': '',
                'login': self.setting.getSetting("torrent_utorrent_login"),
                'password': self.setting.getSetting("torrent_utorrent_password")
            }
        elif client == '1':
            self.client = 'transmission'
            config = {
                'host': self.setting.getSetting("torrent_transmission_host"),
                'port': self.setting.getSetting("torrent_transmission_port"),
                'url': self.setting.getSetting("torrent_transmission_url"),
                'login': self.setting.getSetting("torrent_transmission_login"),
                'password': self.setting.getSetting("torrent_transmission_password")
            }
        elif client == '2':
            self.client = 'vuze'
            config = {
                'host': self.setting.getSetting("torrent_vuze_host"),
                'port': self.setting.getSetting("torrent_vuze_port"),
                'url': '',
                'login': self.setting.getSetting("torrent_vuze_login"),
                'password': self.setting.getSetting("torrent_vuze_password")
            }
        elif client == '3':
            self.client = 'deluge'
            config = {
                'host': self.setting.getSetting("torrent_deluge_host"),
                'port': self.setting.getSetting("torrent_deluge_port"),
                'url': self.setting.getSetting("torrent_deluge_path"),
                'login': '',
                'password': self.setting.getSetting("torrent_deluge_password")
            }
        elif client == '4':
            self.client = 'qbittorrent'
            config = {
                'host': self.setting.getSetting("torrent_qbittorrent_host"),
                'port': self.setting.getSetting("torrent_qbittorrent_port"),
                'url': '',
                'login': self.setting.getSetting("torrent_qbittorrent_login"),
                'password': self.setting.getSetting("torrent_qbittorrent_password")
            }
        return config

    def add(self, torrent, dirname):
        return self.client.add(torrent, dirname)

    def add_url(self, torrent, dirname):
        return self.client.add_url(torrent, dirname)

    def list(self):
        return self.client.list()

    def listdirs(self):
        return self.client.listdirs()

    def listfiles(self, id):
        return self.client.listfiles(id)

    def setprio(self, id, ind):
        return self.client.setprio(id, ind)

    def setprio_simple(self, id, prio, ind):
        # Debug('[setprio_simple] '+str((id, prio, ind)))
        return self.client.setprio_simple(id, prio, ind)

    def setprio_simple_multi(self, prio_list):
        return self.client.setprio_simple_multi(prio_list)

    def action_simple(self, action, id):
        return self.client.action_simple(action, id)
