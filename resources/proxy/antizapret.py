# -*- coding: utf-8 -*-

import os, re, fnmatch, threading, urllib2, time, shelve, anydbm
from contextlib import contextmanager, closing
from functions import log, debug, tempdir

PAC_URL = "http://antizapret.prostovpn.org/proxy.pac"
CACHE_DIR = tempdir()
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36"
CONFIG_LOCK = threading.Lock()

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

CACHE_LIFETIME = 24 * 3600 # 24 hour caching

def config():
    shelf = None
    try:
        CONFIG_LOCK.acquire()
        filename = os.path.join(CACHE_DIR, "antizapret.pac_config2")
        try:
            shelf = shelve.open(filename)
        except anydbm.error:
            os.remove(filename)
            shelf = shelve.open(filename)

        created_at = 0
        data = {}

        if 'created_at' in shelf:
            created_at = shelf['created_at']

        if 'data' in shelf:
            data = shelf['data']

        if((time.time() - created_at) <= CACHE_LIFETIME
                and 'domains' in data
                and len(data['domains']) > 0):
            return data

        log("[antizapret]: Fetching Antizapret PAC file on %s" %PAC_URL)
        try:
            pac_data = urllib2.urlopen(PAC_URL).read()
        except:
            pac_data = ""

        r = re.search(r"\"PROXY (.*); DIRECT", pac_data)
        if r:
            data["server"] = r.group(1)
            data["domains"] = map(lambda x: x.replace(r"\Z(?ms)", "").replace("\\", ""), map(fnmatch.translate, re.findall(r"\"(.*?)\",", pac_data)))
        else:
            data["server"] = None
            data["domains"] = []

        shelf.clear()
        shelf.update({
            "created_at": time.time(),
            "data": data,
        })
        return data
    except Exception as ex:
        debug("[antizapret]: " + str(ex))
        raise
    finally:
        if shelf:
            shelf.close()
        if CONFIG_LOCK.locked():
            CONFIG_LOCK.release()

class AntizapretProxyHandler(urllib2.ProxyHandler, object):
    def __init__(self):
        self.config = config()
        urllib2.ProxyHandler.__init__(self, {
            "http" : "<empty>", 
            "https": "<empty>", 
            "ftp"  : "<empty>", 
        })
    def proxy_open(self, req, proxy, type):
        import socket

        hostname = req.get_host().split(":")[0]
        if socket.gethostbyname(hostname) in self.config["domains"] or hostname in self.config["domains"]:
            debug("[antizapret]: Pass request through proxy " + self.config["server"])
            return urllib2.ProxyHandler.proxy_open(self, req, self.config["server"], type)

        return None

def url_get(url, params={}, headers={}, post = None):

    if params:
        import urllib
        url = "%s?%s" % (url, urllib.urlencode(params))

    if post:
        import urllib
        post = urllib.urlencode(post)

    req = urllib2.Request(url, post)
    req.add_header("User-Agent", USER_AGENT)

    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with closing(urllib2.urlopen(req)) as response:
            data = response.read()
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                return zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)
            return data
    except urllib2.HTTPError as e:
        log("[antizapret]: HTTP Error(%s): %s" % (e.errno, e.strerror))
        return None