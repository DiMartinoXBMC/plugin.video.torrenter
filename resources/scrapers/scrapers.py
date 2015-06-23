# !/usr/bin/python
# -*- coding: utf-8 -*-

import re
# import xbmc, xbmcgui, xbmcplugin, xbmcvfs
from tvdb import TvDb
from tmdbs import TmDb
from kinopoisks import KinoPoisk

STATUS = {
    'moder': (40501, 'FFFF0000'),
    'check': (40502, 'FFFF0000'),
    'repeat': (40503, 'FFFF0000'),
    'nodesc': (40504, 'FFFF0000'),
    'copyright': (40505, 'FFFF0000'),
    'close': (40506, 'FFFF0000'),
    'absorb': (40507, 'FFFF0000'),

    'nocheck': (40508, 'FFFF9900'),
    'neededit': (40509, 'FFFF9900'),
    'doubtful': (40510, 'FFFF9900'),
    'temp': (40511, 'FFFF9900'),

    'ok': (40512, 'FF339933')
}

GENRE = (
    ('anime', 80102),
    ('biography', 80103),
    ('action', 80104),
    ('western', 80105),
    ('military', 80106),
    ('detective', 80107),
    ('children', 80108),
    ('documentary', 80109),
    ('drama', 80110),
    ('game', 80111),
    ('history', 80112),
    ('comedy', 80113),
    ('concert', 80114),
    ('short', 80115),
    ('criminal', 80116),
    ('romance', 80117),
    ('music', 80118),
    ('cartoon', 80119),
    ('musical', 80120),
    ('news', 80121),
    ('adventures', 80122),
    ('realitytv', 80123),
    ('family', 80124),
    ('sports', 80125),
    ('talkshows', 80126),
    ('thriller', 80127),
    ('horror', 80128),
    ('fiction', 80129),
    ('filmnoir', 80130),
    ('fantasy', 80131)
)

WORK = (
    ('actor', u'Актер'),
    ('director', u'Режиссер'),
    ('writer', u'Сценарист'),
    ('producer', u'Продюсер'),
    ('composer', u'Композитор'),
    ('operator', u'Оператор'),
    ('editor', u'Монтажер'),
    ('design', u'Художник'),
    ('voice', u'Актер дубляжа'),
    ('voice_director', u'Режиссер дубляжа')
)

MPAA = ('G', 'PG', 'PG-13', 'R', 'NC-17', 'C', 'GP')


class Scrapers():
    RE = {
        'year': re.compile(r'\(([1-2]{1}[0-9]{3})\)', re.U),
        'second': re.compile(r'^([^\[]*)\[(.+)\]([^\]]*)$', re.U)
    }

    def scraper(self, content, item, language='en'):
        # если есть специализированный скрабер, то запускаем его...

        scraped_item = self.scraper_default(item)

        if content == 'tvdb':
            scraper = TvDb(language)
        elif content == 'tmdb':
            scraper = TmDb(language)
        else:  # if content == 'kinopoisk':
            scraper = KinoPoisk(language)

        name, search, year = item['label'], item['search'], item['year']

        if not search:
            return scraped_item

        scraper_item = scraper.scraper(search, year)
        if not scraper_item:
            scraped_item['label'] = name
            return scraped_item

        scraped_item.update(scraper_item)
        scraped_item['label'] = name

        return scraped_item

    def default(self, item):
        scraper = self.scraper_default(item)
        name, search, year = item['label'], item['search'], item['year']
        scraper['label'] = name

        item.update(scraper)
        return item

    def scraper_default(self, item):
        return {
            'label': item['label'],
            'icon': None,
            'thumbnail': None,
            'info': {},
            'properties': {
                'fanart_image': None
            },
        }
