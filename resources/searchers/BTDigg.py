# -*- coding: utf-8 -*-

import urllib
import json
import sys

import SearcherABC


class BTDigg(SearcherABC.SearcherABC):
    '''
    Weight of source with this searcher provided.
    Will be multiplied on default weight.
    Default weight is seeds number
    '''
    sourceWeight = 1

    '''
    Relative (from root directory of plugin) path to image
    will shown as source image at result listing
    '''
    searchIcon = '/resources/searchers/icons/BTDigg.png'

    '''
    Flag indicates is this source - magnet links source or not.
    Used for filtration of sources in case of old library (setting selected).
    Old libraries won't to convert magnet as torrent file to the storage
    '''

    @property
    def isMagnetLinkSource(self):
        return True

    '''
    Main method should be implemented for search process.
    Receives keyword and have to return dictionary of proper tuples:
    filesList.append((
        int(weight),# Calculated global weight of sources
        int(seeds),# Seeds count
        str(title),# Title will be shown
        str(link),# Link to the torrent/magnet
        str(image),# Path/URL to image shown at the list
    ))
    '''

    def search(self, keyword):
        filesList = []
        url="http://api.btdigg.org/api/private-c47ba652ee73735a/s02?q=%s" % (urllib.quote_plus(keyword))
        headers = [('User-Agent',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 YaBrowser/14.10.2062.12061 Safari/537.36'),
                   ('Referer', 'https://eztv.it/'), ('Accept-encoding', 'gzip'), ]
        response = self.makeRequest(url, headers=headers)

        if None != response and 0 < len(response):
            #print response
            dat = json.loads(response)
            print str(dat)
            for item in dat:
                size = self.sizeConvert(item['size'])
                seeds,leechers=0,0
                image = sys.modules["__main__"].__root__ + self.searchIcon
                filesList.append((
                    int(int(self.sourceWeight) * int(seeds)),
                    int(seeds), int(leechers), size,
                    self.unescape(self.stripHtml(item['name'])),
                    self.__class__.__name__ + '::' + item['magnet'],
                    image,
                ))
        return filesList