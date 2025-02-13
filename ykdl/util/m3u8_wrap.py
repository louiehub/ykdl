#!/usr/bin/env python

from logging import getLogger
from .html import fake_headers_without_ae as fake_headers

logger = getLogger("m3u8_wrap")

try:
    import m3u8
    import time
    import signal

    try:
        from m3u8.httpclient import DefaultHTTPClient
        import urllib.request
    except ImportError:
        pass
    else:
        # hack verify ssl of m3u8, use cykdl's settings
        def _download(self, uri, timeout=None, headers={}, *args, **kwargs):
            resource = urllib.request.urlopen(
                urllib.request.Request(uri, headers=headers),
                timeout=timeout)
            base_uri = m3u8.httpclient._parsed_url(resource.geturl())
            content = resource.read().decode(
                resource.headers.get_content_charset(failobj='utf-8')
            )
            return content, base_uri

        DefaultHTTPClient.download = _download

    stop = False

    def m3u8_live_stopper():
        default_INT_handle = None
        def handle(sig, x):
            print("stopping m3u8 live download!!")
            global stop
            stop = True
            if default_INT_handle:
                signal.signal(signal.SIGINT, default_INT_handle)

        default_INT_handle = signal.signal(signal.SIGINT, handle)

    def load_m3u8_playlist(url):
        stream_types = []
        streams = {}
        m = m3u8.load(url, headers=fake_headers).playlists
        for l in m:
            stream_types.append(str(l.stream_info.bandwidth))
            streams[str(l.stream_info.bandwidth)] = {'container': 'm3u8', 'video_profile': str(l.stream_info.bandwidth), 'src' : [l.absolute_uri], 'size': 0}
        stream_types.sort()
        return stream_types, streams

    def load_m3u8(url):
        urls = []
        m =  m3u8.load(url, headers=fake_headers)
        l = len(m.playlists)
        if l == 1:
            m =  m3u8.load(m.playlists[0].absolute_uri, headers=fake_headers)
        elif l > 1:
            raise ValueError("can't load m3u8 segments, there is more than one media in m3u8 playlist")
        for seg in m.segments:
            urls.append(seg.absolute_uri)
        return urls

    __lenth__ = 0

    def live_m3u8_lenth():
        global __lenth__
        return __lenth__

    def load_live_m3u8(url):
        """
        the stream is live stream. so we use sleep to simulate player. but not perfact!
        """
        global __lenth__
        m =  m3u8.load(url, headers=fake_headers)
        __lenth__ = now = d = 0
        i = 0
        m3u8_live_stopper()
        while True:
            if stop:
                print('stopped!!')
                raise StopIteration
            if i < len(m.segments):
                delta = d -( time.time() - now)
                if (delta) > 0:
                    time.sleep(delta)
                segurl = m.segments[i].absolute_uri
                now = time.time()
                d = m.segments[i].duration
                i += 1
                __lenth__ += 1
                yield segurl
            else:
                i = 0
                delta = d -( time.time() - now)
                if (delta) > 0:
                    time.sleep(d - (time.time() - now))
                m = m3u8.load(url, headers=fake_headers)
                now = time.time()
                d = 0
except:
    from ykdl.util import log
    def load_m3u8_playlist(url):
        logger.warning("No python-m3u8 found, use stub m3u8!!! please install it by pip install m3u8")
        stream_types = ['current']
        streams['current'] = {'container': 'm3u8', 'video_profile': 'current', 'src' : [url], 'size': 0}
        return stream_types, streams

    def load_m3u8(url):
        logger.warning("No python-m3u8 found, use stub m3u8!!! please install it by pip install m3u8")
        return [url]

    def load_live_m3u8(url):
        return [url]

    def live_m3u8_lenth():
        return 0

