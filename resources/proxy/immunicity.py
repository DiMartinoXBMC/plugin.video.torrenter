# -*- coding: utf-8 -*-

import os, re, fnmatch, threading, urllib2
from contextlib import contextmanager, closing
from functions import log, debug, tempdir

LOCKS = {}
PAC_URL = "http://clientconfig.immunicity.org/pacs/all.pac"
CACHE_DIR = tempdir()
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

CACHE = 24 * 3600 # 24 hour caching

@contextmanager
def shelf(filename, ttl=0):
    import shelve
    filename = os.path.join(CACHE_DIR, filename)
    with LOCKS.get(filename, threading.RLock()):
        with closing(shelve.open(filename, writeback=True)) as d:
            import time
            if not d:
                d.update({
                    "created_at": time.time(),
                    "data": {},
                })
            elif ttl > 0 and (time.time() - d["created_at"]) > ttl:
                d["data"] = {}
            yield d["data"]

_config = {}

def config():
    global _config
    if not _config:
        with shelf("xbmctorrent.immunicity.pac_config", ttl=CACHE) as pac_config:
            log("Fetching Immunicity PAC file")
            pac_data = urllib2.urlopen(PAC_URL).read()
            pac_config["server"] = re.search(r"var proxyserver = '(.*)'", pac_data).group(1)
            pac_config["domains"] = map(lambda x: x.replace(r"\Z(?ms)", ""), map(fnmatch.translate, re.findall(r"\"(.*?)\",", pac_data)))
            _config = pac_config
    return _config

class ImmunicityProxyHandler(urllib2.ProxyHandler, object):
    def __init__(self):
        self.config = config()
        urllib2.ProxyHandler.__init__(self, {
            "http" : "<empty>",
            "https": "<empty>",
            "ftp"  : "<empty>",
        })
    def proxy_open(self, req, proxy, type):
        import socket

        if socket.gethostbyname(req.get_host().split(":")[0]) in self.config["domains"]:
            debug("[immunicity]: Pass request through proxy " + self.config["server"])
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
        log("[immunicity]: HTTP Error(%s): %s" % (e.errno, e.strerror))
        return None
