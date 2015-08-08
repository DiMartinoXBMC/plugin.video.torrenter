#!/usr/bin/env python
import time
import sys
import argparse
import os.path
from threading import Thread
import re
import urlparse
import BaseHTTPServer as htserver
import types
import logging
import logging.handlers
import traceback
import urllib
import SocketServer
import socket
import pickle
import json
import shutil

from cachebt import CacheBT

from common import AbstractFile, Hasher, BaseMonitor, BaseClient, Resolver

logging.basicConfig()
logger = logging.getLogger()


INITIAL_TRACKERS = ['udp://tracker.openbittorrent.com:80',
                    'udp://tracker.istole.it:80',
                    'udp://open.demonii.com:80',
                    'udp://tracker.coppersurfer.tk:80',
                    'udp://tracker.leechers-paradise.org:6969',
                    'udp://exodus.desync.com:6969',
                    'udp://tracker.publicbt.com:80']

VIDEO_EXTS = {'.avi': 'video/x-msvideo', '.mp4': 'video/mp4', '.mkv': 'video/x-matroska',
              '.m4v': 'video/mp4', '.mov': 'video/quicktime', '.mpg': 'video/mpeg', '.ogv': 'video/ogg',
              '.ogg': 'video/ogg', '.webm': 'video/webm', '.ts': 'video/mp2t', '.3gp': 'video/3gpp'}

RANGE_RE = re.compile(r'bytes=(\d+)-')

# offset from end to download first
FILE_TAIL = 10000

class x:
    lol=''

def parse_range(range):  # @ReservedAssignment
    if range:
        m = RANGE_RE.match(range)
        if m:
            try:
                return int(m.group(1))
            except:
                pass
    return 0


class StreamServer(SocketServer.ThreadingMixIn, htserver.HTTPServer):
    daemon_threads = True

    def __init__(self, address, handler_class, tfile=None, allow_range=True, status_fn=None):
        htserver.HTTPServer.__init__(self, address, handler_class)
        self.file = tfile
        self._running = True
        self.allow_range = allow_range
        self.status_fn = status_fn

    def stop(self):
        self._running = False

    def set_file(self, f):
        self.file = f

    def serve(self, w):
        while self._running:
            try:
                self.handle_request()
                time.sleep(w)
            except Exception, e:
                print >> sys.stderr, str(e)

    def run(self):
        self.timeout = 0.5
        t = Thread(target=self.serve, args=[self.timeout], name='HTTP Server')
        t.daemon = True
        t.start()

    def handle_error(self, request, client_address):
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.

        """
        _, e, _ = sys.exc_info()
        if isinstance(e, socket.error) and e.errno == 32:
            logger.debug("Socket disconnect for client %s", client_address)
            # pprint.pprint(e)
        else:
            logger.exception("HTTP Server Error")
            traceback.print_exc()


class BTFileHandler(htserver.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        if self.do_HEAD(only_header=False):
            with self.server.file.create_cursor(self._offset) as f:
                send_something = False
                while True:
                    buf = f.read(1024)
                    if not send_something and logger.level <= logging.DEBUG:
                        logger.debug('Start sending data')
                        send_something = True
                    if buf:
                        self.wfile.write(buf)
                    else:
                        if logger.level <= logging.DEBUG:
                            logger.debug('Finished sending data')
                        break

    def _file_info(self):
        size = self.server.file.size
        ext = os.path.splitext(self.server.file.path)[1]
        mime = (self.server.file.mime if hasattr(self.server.file, 'mime')  else None) or VIDEO_EXTS.get(ext)
        if not mime:
            mime = 'application/octet-stream'
        return size, mime

    def do_HEAD(self, only_header=True):
        parsed_url = urlparse.urlparse(self.path)
        if parsed_url.path == "/status" and self.server.status_fn:
            s = self.server.status_fn()
            status = json.dumps(s)
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(status))
            self._finish_header(only_header)
            if not only_header:
                self.wfile.write(status)
            return False

        elif self.server.file and urllib.unquote(parsed_url.path) == '/' + self.server.file.path:
            self._offset = 0
            size, mime = self._file_info()
            range = None  # @ReservedAssignment
            if self.server.allow_range:
                range = parse_range(self.headers.get('Range', None))  # @ReservedAssignment
                if range not in [None, False]:
                    self._offset = range
                    range = (range, size - 1, size)  # @ReservedAssignment
                    logger.debug('Request range %s - (header is %s', range, self.headers.get('Range', None))
            self.send_resp_header(mime, size, range, only_header)
            return True

        else:
            logger.error('Requesting wrong path %s, but file is %s', parsed_url.path, '/' + self.server.file.path)
            self.send_error(404, 'Not Found')

    def send_resp_header(self, cont_type, cont_length, range=False, only_header=False):  # @ReservedAssignment
        logger.debug('range is %s'% str(range))
        if self.server.allow_range and range not in [None, False]:
            self.send_response(206, 'Partial Content')
        else:
            self.send_response(200, 'OK')
        self.send_header('Content-Type', cont_type)
        self.send_header('transferMode.dlna.org', 'Streaming')
        self.send_header('contentFeatures.dlna.org',
                         'DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000')
        if self.server.allow_range:
            self.send_header('Accept-Ranges', 'bytes')
        else:
            self.send_header('Accept-Ranges', 'none')
        if self.server.allow_range and range not in [None, False]:
            if isinstance(range, (types.TupleType, types.ListType)) and len(range) == 3:
                self.send_header('Content-Range', 'bytes %d-%d/%d' % range)
                self.send_header('Content-Length', range[1] - range[0] + 1)
            else:
                raise ValueError('Invalid range value')
        else:
            self.send_header('Content-Range', 'bytes %d-%d/%d' % (range, cont_length-1, cont_length))
            self.send_header('Content-Length', cont_length)
        self._finish_header(only_header)

    def _finish_header(self, only_header):
        self.send_header('Connection', 'close')
        if not only_header: self.end_headers()

    def log_message(self, format, *args):  # @ReservedAssignment
        logger.debug(format, *args)


class BTClient(BaseClient):
    def __init__(self, path_to_store,
                 args=None,
                 state_file="",
                 lt=None,
                 **kwargs):
        super(BTClient, self).__init__(path_to_store, args=args)
        self.lt=lt
        self._cache = CacheBT(path_to_store, self.lt)
        self._torrent_params = {'save_path': path_to_store,
                                'storage_mode': self.lt.storage_mode_t.storage_mode_sparse
                                }
        if not state_file:
            state_file=os.path.join(path_to_store,'.btclient_state')
        self._state_file = os.path.expanduser(state_file)
        self._ses = self.lt.session()
        if os.path.exists(self._state_file):
            with open(self._state_file) as f:
                state = pickle.load(f)
                self._ses.load_state(state)
        # self._ses.set_alert_mask(self.lt.alert.category_t.progress_notification)
        if args:
            s = self._ses.get_settings()
            s['download_rate_limit'] = int(round(args.bt_download_limit * 1024))
            s['upload_rate_limit'] = int(round(args.bt_upload_limit * 1024))
            self._ses.set_settings(s)
            self._ses.listen_on(args.listen_port_min, args.listen_port_max)
            self.content_id=args.content_id
        else:
            self._ses.listen_on(6881, 6891)
        self._start_services()
        self._th = None

        self._monitor.add_listener(self._check_ready)
        self._dispatcher = BTClient.Dispatcher(self, lt=self.lt)
        self._dispatcher.add_listener(self._update_ready_pieces)
        self._hash = None
        self._url = None

        if args and args.debug_log and args.trace:
            self.add_monitor_listener(self.debug_download_queue)
            self.add_dispatcher_listener(self.debug_alerts)

    @property
    def is_file_complete(self):
        pcs = self._th.status().pieces[self._file.first_piece:self._file.last_piece + 1]
        return all(pcs)

    def _update_ready_pieces(self, alert_type, alert):
        if alert_type == 'read_piece_alert' and self._file:
            self._file.update_piece(alert.piece, alert.buffer)

    def _check_ready(self, s, **kwargs):
        if s.state in [3, 4, 5] and not self._file and s.progress > 0:
            try:
                self._meta_ready(self._th.torrent_file())
            except:
                self._meta_ready(self._th.get_torrent_info())
            logger.debug('Got torrent metadata and start download')
            self.hash = True
            self.hash = Hasher(self._file, self._on_file_ready)

    def _choose_file(self, files, i):
        if not i and i!=0:
            videos = filter(lambda f: VIDEO_EXTS.has_key(os.path.splitext(f.path)[1]), files)
            if not videos:
                raise Exception('No video files in torrent')
            f = sorted(videos, key=lambda f: f.size)[-1]
            i = files.index(f)
            f.index = i
        f=files[i]
        f.index = i
        return f

    def _meta_ready(self, meta):
        fs = meta.files()
        files = fs if isinstance(fs, list) else [fs.at(i) for i in xrange(fs.num_files())]
        f = self._choose_file(files, self.content_id)
        fmap = meta.map_file(f.index, 0, 1)
        self._file = BTFile(f.path, self._base_path, f.index, f.size, fmap, meta.piece_length(),
                            self.prioritize_piece)

        self.prioritize_file()
        print ('File %s pieces (pc=%d, ofs=%d, sz=%d), total_pieces=%d, pc_length=%d' %
               (f.path, fmap.piece, fmap.start, fmap.length,
                     meta.num_pieces(), meta.piece_length()))

        try:
            meta = self._th.torrent_file()
        except:
            meta=self._th.get_torrent_info()
        self._cache.file_complete(meta,
                                  self._url if self._url and self._url.startswith('http') else None)

    def prioritize_piece(self, pc, idx):
        piece_duration = 1000
        min_deadline = 2000
        dl = idx * piece_duration + min_deadline
        self._th.set_piece_deadline(pc, dl, self.lt.deadline_flags.alert_when_available)
        logger.debug("Set deadline %d for piece %d", dl, pc)

        # we do not need to download pieces that are lower then current index, but last two pieces are special because players sometime look at end of file
        if idx == 0 and (self._file.last_piece - pc) > 2:
            for i in xrange(pc - 1):
                self._th.piece_priority(i, 0)
                self._th.reset_piece_deadline(i)

    def prioritize_file(self):
        try:
            meta = self._th.torrent_file()
        except:
            meta=self._th.get_torrent_info()
        priorities = [1 if i >= self._file.first_piece and i <= self.file.last_piece else 0 \
                      for i in xrange(meta.num_pieces())]
        self._th.prioritize_pieces(priorities)

    def encrypt(self):
        # Encryption settings
        print 'Encryption enabling...'
        try:
            encryption_settings = self.lt.pe_settings()
            encryption_settings.out_enc_policy = self.lt.enc_policy(self.lt.enc_policy.forced)
            encryption_settings.in_enc_policy = self.lt.enc_policy(self.lt.enc_policy.forced)
            encryption_settings.allowed_enc_level = self.lt.enc_level.both
            encryption_settings.prefer_rc4 = True
            self._ses.set_pe_settings(encryption_settings)
            print 'Encryption on!'
        except Exception, e:
            print 'Encryption failed! Exception: ' + str(e)
            pass

    @property
    def unique_file_id(self):
        try:
            meta = self._th.torrent_file()
        except:
            meta=self._th.get_torrent_info()
        return str(meta.info_hash())

    @property
    def pieces(self):
        return self._th.status().pieces

    def add_dispatcher_listener(self, cb):
        self._dispatcher.add_listener(cb)

    def remove_dispacher_listener(self, cb):
        self._dispatcher.remove_listener(cb)

    def remove_all_dispatcher_listeners(self):
        self._dispatcher.remove_all_listeners()

    def info_from_file(self, uri):
        if os.access(uri, os.R_OK):
            e = self.lt.bdecode(open(uri, 'rb').read())
            info = self.lt.torrent_info(e)
            tp = {'ti': info}
            resume_data = self._cache.get_resume(info_hash=str(info.info_hash()))
            if resume_data:
                tp['resume_data'] = resume_data
            return tp
        raise ValueError('Invalid torrent path %s' % uri)

    def start_url(self, uri):
        if self._th:
            raise Exception('Torrent is already started')

        if uri.startswith('http://') or uri.startswith('https://'):
            self._url = uri
            stored = self._cache.get_torrent(url=uri)
            if stored:
                tp = self.info_from_file(stored)
            else:
                tp = {'url': uri}
                resume_data = self._cache.get_resume(url=uri)
                if resume_data:
                    tp['resume_data'] = resume_data
        elif uri.startswith('magnet:'):
            self._url = uri
            stored = self._cache.get_torrent(info_hash=CacheBT.hash_from_magnet(uri))
            if stored:
                tp = self.info_from_file(stored)
            else:
                tp = {'url': uri}
                resume_data = self._cache.get_resume(info_hash=CacheBT.hash_from_magnet(uri))
                if resume_data:
                    tp['resume_data'] = resume_data
        elif os.path.isfile(uri):
            tp = self.info_from_file(uri)
        else:
            raise ValueError("Invalid torrent %s" % uri)

        tp.update(self._torrent_params)
        self._th = self._ses.add_torrent(tp)
        for tr in INITIAL_TRACKERS:
            self._th.add_tracker({'url': tr})
        self._th.set_sequential_download(True)
        time.sleep(1)
        self._th.force_dht_announce()

        self._monitor.start()
        self._dispatcher.do_start(self._th, self._ses)

    def stop(self):
        BaseClient.stop(self)(self)
        self._dispatcher.stop()
        self._dispatcher.join()

    def _start_services(self):
        self._ses.add_dht_router('router.bittorrent.com', 6881)
        self._ses.add_dht_router('router.utorrent.com', 6881)
        self._ses.add_dht_router('router.bitcomet.com', 6881)
        self._ses.start_dht()
        self._ses.start_lsd()
        self._ses.start_upnp()
        self._ses.start_natpmp()

    def _stop_services(self):
        self._ses.stop_natpmp()
        self._ses.stop_upnp()
        self._ses.stop_lsd()
        self._ses.stop_dht()

    def save_state(self):
        state = self._ses.save_state()
        with open(self._state_file, 'wb') as f:
            pickle.dump(state, f)

    def save_resume(self):
        if self._th.need_save_resume_data() and self._th.is_valid() and self._th.status().has_metadata:
            r = BTClient.ResumeData(self)
            start = time.time()
            while (time.time() - start) <= 5:
                if r.data or r.failed:
                    break
                time.sleep(0.1)
            if r.data:
                logger.debug('Savig fast resume data')
                self._cache.save_resume(self.unique_file_id, self.lt.bencode(r.data))
            else:
                logger.warn('Fast resume data not available')

    def close(self):
        self.remove_all_dispatcher_listeners()
        self._monitor.stop()
        self._cache.close()
        if self._ses:
            self._ses.pause()
            if self._th:
                self.save_resume()
            self.save_state()
            self._stop_services()
            try:
                self._ses.remove_torrent(self._th)
            except:
                print 'RuntimeError: invalid torrent handle used'
        BaseClient.close(self)

    @property
    def status(self):
        if self._th:
            s = self._th.status()
            if self._file:
                pieces = s.pieces[self._file.first_piece:self._file.last_piece]
                if len(pieces)>0:
                    progress = float(sum(pieces)) / len(pieces)
                else:
                    progress = 0
            else:
                progress = 0
            size = self._file.size if self._file else 0
            s.desired_rate = self._file.byte_rate if self._file and progress > 0.003 else 0
            s.progress_file = progress
            s.file_size = size
            return s

    class ResumeData(object):
        def __init__(self, client):
            self.data = None
            self.failed = False
            client.add_dispatcher_listener(self._process_alert)
            client._th.save_resume_data()

        def _process_alert(self, t, alert):
            if t == 'save_resume_data_failed_alert':
                logger.debug('Fast resume data generation failed')
                self.failed = True
            elif t == 'save_resume_data_alert':
                self.data = alert.resume_data

    class Dispatcher(BaseMonitor):
        def __init__(self, client, lt=None):
            super(BTClient.Dispatcher, self).__init__(client, name='Torrent Events Dispatcher')
            self.lt=lt

        def do_start(self, th, ses):
            self._th = th
            self._ses = ses
            self.start()

        def run(self):
            if not self._ses:
                raise Exception('Invalid state, session is not initialized')

            while (self._running):
                a = self._ses.wait_for_alert(1000)
                if a:
                    alerts = self._ses.pop_alerts()
                    for alert in alerts:
                        with self._lock:
                            for cb in self._listeners:
                                if "udp_error_alert" not in self.lt.alert.what(alert):
                                    cb(self.lt.alert.what(alert), alert)

    STATE_STR = ['queued', 'checking', 'downloading metadata',
                    'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']

    def print_status(self, s, client):
        if self._th:

            state_str = ['queued', 'checking', 'downloading metadata',
                    'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']
            print('[%s] %.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s' %
                  (self.lt.version, s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000,
                   s.num_peers, state_str[s.state]))

    def get_normalized_status(self):
        s = self.status
        if self._file:
            pieces = s.pieces[self._file.first_piece: self._file.last_piece + 1]
            downloaded = reduce(lambda s, x: s + (x and 1 or 0) * self._file.piece_size, pieces[:-1], 0)
            if pieces[-1]:
                rem = self._file.size % self._file.piece_size
                downloaded += rem if rem else self._file.piece_size
        else:
            downloaded = 0
        return {'source_type': 'bittorrent',
                'state': BTClient.STATE_STR[s.state],
                'downloaded': downloaded,
                'total_size': s.file_size,
                'download_rate': s.download_rate,
                'upload_rate': s.upload_rate,
                'desired_rate': s.desired_rate,
                'piece_size': self._file.piece_size if self._file else 0,
                'progress': s.progress_file,
                # BT specific
                'seeds_connected': s.num_seeds,
                'seeds_total': s.num_complete,
                'peers_connected': s.num_peers,
                'peers_total': s.num_incomplete,
                'num_pieces': s.num_pieces,

                }

    def debug_download_queue(self, s, client):
        if s.state != 3:
            return
        download_queue = self._th.get_download_queue()
        if self.file:
            first = self.file.first_piece
        else:
            first = 0
        q = map(lambda x: x['piece_index'] + first, download_queue)
        logger.debug('Download queue: %s', q)

    def debug_alerts(self, type, alert):
        logger.debug("Alert %s - %s", type, alert)


class BTFile(AbstractFile):
    def __init__(self, path, base, index, size, fmap, piece_size, prioritize_fn):
        AbstractFile.__init__(self, path, base, size, piece_size)
        self.index = index
        self.first_piece = fmap.piece
        self.last_piece = self.first_piece + max((size - 1 + fmap.start), 0) // piece_size
        self.offset = fmap.start
        self._prioritize_fn = prioritize_fn

    def prioritize_piece(self, n, idx):
        self._prioritize_fn(n, idx)


class LangAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super(LangAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        if len(values) != 3:
            raise ValueError('subtitles language should be 3 letters code')
        setattr(namespace, self.dest, values)


def main(args=None):
    #from argparse import Namespace
    #args=Namespace(bt_download_limit=0,
    #                  bt_upload_limit=0,
    #                  choose_subtitles=False,
    #                  clear_older=0,
    #                  debug_log='D:\\log.txt',
    #                  delete_on_finish=True,#Flase,
    #                  directory='D:\\',
    #                  listen_port_max=6891,
    #                  listen_port_min=6881,
    #                  no_resume=False,
    #                  player='vlc',#kodi
    #                  port=5001,
    #                  print_pieces=False,
    #                  quiet=False,
    #                  stdin=False,
    #                  stream=False,
    #                  subtitles=None,
    #                  trace=True,
    #                  url='D:\\ntest.torrent')
    if not args:
        p = argparse.ArgumentParser()
        p.add_argument("url", help="Torrent file, link to file or magnet link")
        p.add_argument("-d", "--directory", default="./", help="directory to save download files")
        p.add_argument("-p", "--player", default="mplayer", choices=["mplayer", "vlc"], help="Video player")
        p.add_argument("--port", type=int, default=5001, help="Port for http server")
        p.add_argument("--debug-log", default='', help="File for debug logging")
        p.add_argument("--stdin", action='store_true', help='sends video to player via stdin (no seek then)')
        p.add_argument("--print-pieces", action="store_true",
                       help="Prints map of downloaded pieces and ends (X is downloaded piece, O is not downloaded)")
        p.add_argument("-s", "--subtitles", action=LangAction,
                       help="language for subtitle 3 letter code eng,cze ... (will try to get subtitles from opensubtitles.org)")
        p.add_argument("--stream", action="store_true", help="just file streaming, but will not start player")
        p.add_argument("--no-resume", action="store_true", help="Do not resume from last known position")
        p.add_argument("-q", "--quiet", action="store_true", help="Quiet - did not print progress to stdout")
        p.add_argument('--delete-on-finish', action="store_true", help="Delete downloaded file when program finishes")
        p.add_argument('--clear-older', type=int, default=0,
                       help="Deletes files older then x days from download directory, if set will slowdown start of client")
        p.add_argument('--bt-download-limit', type=int, default=0, help='Download limit for torrents kB/s')
        p.add_argument('--bt-upload-limit', type=int, default=0, help='Upload limit for torrents kB/s')
        p.add_argument('--listen-port-min', type=int, default=6881, help='Bitorrent input port range - minimum port')
        p.add_argument('--listen-port-max', type=int, default=6891, help='Bitorrent input port range - maximum port')
        p.add_argument('--choose-subtitles', action="store_true",
                       help="Always manually choose subtitles (otherwise will try to use best match in many cases)")
        p.add_argument('--trace', action='store_true', help='More detailed debug logging')
        args = p.parse_args(args)
    # str(args)
    if args.debug_log:
        logger.setLevel(logging.DEBUG)
        h = logging.handlers.RotatingFileHandler(args.debug_log)
        logger.addHandler(h)
    else:
        logger.setLevel(logging.CRITICAL)
        logger.addHandler(logging.StreamHandler())

    if args.clear_older:
        days = args.clear_older
        items = os.listdir(args.directory)
        now = time.time()
        for item in items:
            if item != CacheBT.CACHE_DIR:
                full_path = os.path.join(args.directory, item)
                if now - os.path.getctime(full_path) > days * 24 * 3600:
                    logger.debug('Deleting path %s', full_path)
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path, ignore_errors=True)
                    else:
                        os.unlink(full_path)

    if args.print_pieces:
        print_pieces(args)
    elif re.match('https?://localhost', args.url):
        class TestResolver(Resolver):
            SPEED_LIMIT = 300
            THREADS = 2

        #stream(args, HTClient, TestResolver)
    else:
        #rclass = plugins.find_matching_plugin(args.url)
        #if rclass:
        #    stream(args, HTClient, rclass)
        #else:
        #stream(args, BTClient)
        return args

#def stream(args, client_class, resolver_class=None):
#    c = client_class(args.directory, args=args, resolver_class=resolver_class)
#    player = None
#
#    def on_exit(sig=None, frame=None):
#        c.close()
#        if player:
#            player.terminate()
#        if sig:
#            logger.info('Exiting by signal %d', sig)
#            sys.exit(0)
#
#    try:
#
#        if not args.stream:
#            player = Player.create(args.player, c.update_play_time)
#
#        server = None
#        # test if port if free, otherwise find free
#        free_port = args.port
#        while True:
#
#            try:
#                s = socket.socket()
#                res = s.connect_ex(('127.0.0.1', free_port))
#                if res:
#                    break
#            finally:
#                s.close()
#            free_port += 1
#        if not args.stdin:
#            server = StreamServer(('127.0.0.1', free_port), BTFileHandler, allow_range=True,
#                                  status_fn=c.get_normalized_status)
#            logger.debug('Started http server on port %d', free_port)
#            server.run()
#            #thread.start_new_thread(server.run, ())
#        if player:
#            def start_play(f, finished):
#                base = None
#                if not args.stdin:
#                    server.set_file(f)
#                    base = 'http://127.0.0.1:' + str(free_port) + '/'
#                sin = args.stdin
#                if finished:
#                    base = args.directory
#                    sin = False
#                    logger.debug('File is already downloaded, will play it directly')
#                    args.play_file = True
#
#                if args.no_resume:
#                    start_time = 0
#                else:
#                    start_time = c.last_play_time or 0
#                player.start(f, base, stdin=sin, sub_lang=args.subtitles, start_time=start_time,
#                             always_choose_subtitles=args.choose_subtitles)
#                logger.debug('Started media player for %s', f)
#
#            c.set_on_file_ready(start_play)
#        else:
#            def print_url(f, done):
#                server.set_file(f)
#                base = 'http://127.0.0.1:' + str(free_port) + '/'
#                url = urlparse.urljoin(base, urllib.quote(f.path))
#                print "\nServing file on %s" % url
#                sys.stdout.flush()
#
#            c.set_on_file_ready(print_url)
#
#        logger.debug('Starting btclient - libtorrent version %s', self.lt.version)
#        c.start_url(args.url)
#        while not c.is_file_ready:
#            time.sleep(1)
#        if not args.stdin or hasattr(args, 'play_file') and args.play_file:
#            f = None
#        else:
#            f = c.file.create_cursor()
#
#        while True:
#            if player and not player.is_playing():
#                break
#            if not f:
#                time.sleep(1)
#            else:
#                buf = f.read(1024)
#                if buf:
#                    try:
#                        player.write(buf)
#                        logger.debug("written to stdin")
#                    except IOError:
#                        pass
#                else:
#                    player.close()
#        if f:
#            f.close()
#        logger.debug('Play ended')
#        if server:
#            server.stop()
#        if player:
#            if player.rcode != 0:
#                msg = 'Player ended with error %d\n' % (player.rcode or 0)
#                sys.stderr.write(msg)
#                logger.error(msg)
#
#            logger.debug("Player output:\n %s", player.log)
#    finally:
#        on_exit()
#        # logger.debug("Remaining threads %s", list(threading.enumerate()))


def pieces_map(pieces, w):
    idx = 0
    sz = len(pieces)
    w(" " * 4)
    for i in xrange(10):
        w("%d " % i)
    w('\n')
    while idx < sz:
        w("%3d " % (idx / 10))
        for _c in xrange(min(10, sz - idx)):
            if pieces[idx]:
                w('X ')
            else:
                w('O ')
            idx += 1
        w('\n')


def print_pieces(args):
    def w(x):
        sys.stdout.write(x)

    c = BTClient(args.directory)
    c.start_url(args.url)
    # c.add_listener(print_status)
    start = time.time()
    while time.time() - start < 60:
        if c.file:
            print "Pieces (each %.0f k) for file: %s" % (c.file.piece_size / 1024.0, c.file.path)
            pieces = c.pieces
            pieces_map(pieces, w)
            return
        time.sleep(1)
    print >> sys.stderr, "Cannot get metadata"


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print >> sys.stderr, '\nProgram interrupted, exiting'
        logger.info('Exiting by SIGINT')
    except Exception:
        traceback.print_exc()
        logger.exception('General error')
