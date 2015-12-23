# -*- coding: utf-8 -*-

import re
import time
import urllib
import os
import tempfile
import zipfile

import xbmc
from net import HTTP
from cache import Cache
from functions import log


class TvDb:
    """
    
    API:
        scraper  - скрапер
        search   - поиск сериалов
        movie    - профайл фильма
        
    """

    def __init__(self, language='en'):
        self.api_key = '33DBB309BB2B0ADB'
        dbname='tvdb.%s.db' % language
        self.cache = Cache(dbname, 1.0)

        self.language = language

        self.http = HTTP()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
            'Cache-Control': 'no-cache',
            'Referer': 'http://www.thetvdb.com/'
        }


    # API

    def scraper(self, search, year=None):
        try:
            if not isinstance(search, list):
                search = [search]
            tag = 'scraper:' + urllib.quote_plus(":".join(search).encode('utf8'))
        except:
            return None
        else:

            if year:
                tag += ':' + str(year)

            id = self.cache.get(tag, self._scraper, search, year)
            if not id:
                return None

            return self.movie(id)

    def search(self, search, year=None):
        return self._search(search, year)


    def movie(self, id):
        id = str(id)
        return self.cache.get('movie:' + id, self._movie, id)


    def _movie(self, id):
        try:
            dirname = tempfile.mkdtemp()
        except:
            dirname = xbmc.translatePath('special://temp')
            for subdir in ('xbmcup', 'plugin.video.torrenter'):
                dirname = os.path.join(dirname, subdir)
                if not os.path.exists(dirname):
                    os.mkdir(dirname)

        url = 'http://www.thetvdb.com/api/' + self.api_key + '/series/' + id + '/all/' + self.language + '.zip'
        # print url
        response = self.http.fetch(url, headers=self.headers, download=os.path.join(dirname, 'movie.zip'), timeout=20)
        if response.error:
            log("ERRRRRROR! " + str(response.error))
            self._movie_clear(dirname)
            return False, None

        try:
            filezip = zipfile.ZipFile(os.path.join(dirname, 'movie.zip'), 'r')
            filezip.extractall(dirname)
            filezip.close()
            movie = file(os.path.join(dirname, self.language + '.xml'), 'rb').read().decode('utf8')
        except:
            self._movie_clear(dirname)
            return False, None

        self._movie_clear(dirname)

        body = re.compile(r'<Series>(.+?)</Series>', re.U | re.S).search(movie)
        if not body:
            return False, None

        body = body.group(1)

        res = {
            'icon': None,
            'thumbnail': None,
            'properties': {
                'fanart_image': None,
            },
            'info': {
                'count': int(id)
            }
        }

        # режисеры и сценаристы
        for tag in ('Director', 'Writer'):
            people = {}
            people_list = []
            [people_list.extend(x.split('|')) for x in
             re.compile(r'<' + tag + r'>([^<]+)</' + tag + r'>', re.U | re.S).findall(movie)]
            [people.update({x: 1}) for x in [x.strip() for x in people_list] if x]
            if people:
                res['info'][tag.lower()] = u', '.join([x for x in people.keys() if x])

        for tag, retag, typeof, targettype in (
                ('plot', 'Overview', None, None),
                ('mpaa', 'ContentRating', None, None),
                ('premiered', 'FirstAired', None, None),
                ('studio', 'Network', None, None),
                ('title', 'SeriesName', None, None),
                ('runtime', 'Runtime', None, None),
                ('votes', 'RatingCount', None, None),
                ('rating', 'Rating', float, None),
                ('genre', 'Genre', list, unicode),
                ('cast', 'Actors', list, None)
        ):
            r = re.compile(r'<' + retag + r'>([^<]+)</' + retag + r'>', re.U | re.S).search(body)
            if r:
                r = r.group(1).strip()
                if typeof == float:
                    res['info'][tag] = float(r)
                elif typeof == list:
                    if targettype == unicode:
                        res['info'][tag] = u', '.join([x for x in [x.strip() for x in r.split(u'|')] if x])
                    else:
                        res['info'][tag] = [x for x in [x.strip() for x in r.split(u'|')] if x]
                else:
                    res['info'][tag] = r

        # год
        if 'premiered' in res['info']:
            res['info']['year'] = int(res['info']['premiered'].split('-')[0])

        # постер
        r = re.compile(r'<poster>([^<]+)</poster>', re.U | re.S).search(body)
        if r:
            res['icon'] = 'http://thetvdb.com/banners/' + r.group(1).strip()
            res['thumbnail'] = 'http://thetvdb.com/banners/' + r.group(1).strip()

        # фанарт
        r = re.compile(r'<fanart>([^<]+)</fanart>', re.U | re.S).search(body)
        if r:
            res['properties']['fanart_image'] = 'http://thetvdb.com/banners/' + r.group(1).strip()

        timeout = True
        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if 'year' not in res['info'] or not res['properties']['fanart_image'] \
                or int(res['info']['year']) > time.gmtime(time.time()).tm_year:
            timeout = 7 * 24 * 60 * 60 * 4  #4 week

        return timeout, res


    def _movie_clear(self, dirname):
        for filename in os.listdir(dirname):
            try:
                os.unlink(os.path.join(dirname, filename))
            except:
                raise
        try:
            os.rmdir(dirname)
        except:
            raise


    def _search(self, search, year=None):
        i = -1
        id = None
        for name in search:
            # print urllib.quote_plus(name.encode('utf-8'))
            url = 'http://www.thetvdb.com/api/GetSeries.php?language=' + self.language + '&seriesname=' + urllib.quote_plus(
                name.encode('utf-8'))
            #print url
            i += 1
            response = self.http.fetch(url, headers=self.headers, timeout=20)
            #print response.body
            if response.error:
                #print "ERRRRRROR! "+str(response.error)
                return None

            res = []
            rows = re.compile('<Series>(.+?)</Series>', re.U | re.S).findall(response.body.decode('utf8'))
            if rows:
                recmd = re.compile('<seriesid>([0-9]+)</seriesid>', re.U | re.S)

                for row in [x for x in rows if x.find(u'<language>%s</language>' % self.language.decode('utf8')) != -1]:
                    r = recmd.search(row)
                    if r:
                        res.append(int(r.group(1)))
                # в некоторых случаях можно найти только по оригинальному названию, 
                # но при этом русское описание есть
                if not res and self.language != 'en':
                    for row in [x for x in rows if x.find(u'<language>en</language>') != -1]:
                        r = recmd.search(row)
                        if r:
                            res.append(int(r.group(1)))

                if len(res) > 1:
                    Data = []
                    for id in res:
                        for row in rows:
                            recmd = re.compile('<seriesid>([0-9]+)</seriesid>', re.U | re.S)
                            r = recmd.search(row)
                            if int(r.group(1)) == id:
                                title = re.compile('<SeriesName>(.+?)</SeriesName>', re.U | re.S).search(row)
                                Syear = re.compile('<FirstAired>(.+?)</FirstAired>', re.U | re.S).search(row)
                                if not Syear:
                                    Syear = 0
                                else:
                                    Syear = Syear.group(1)
                                Data.append((title.group(1), Syear, id))

                    index = get_best(Data, search, year)
                    if index and index['rate'] > 70:
                        id = str(index['id'])
                elif len(res) == 1:
                    id = str(res[0])

            if id:
                break

        return id


    def _scraper(self, search, year):
        timeout = True

        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if year and year > time.gmtime(time.time()).tm_year:
            timeout = 7 * 24 * 60 * 60 * 4  # 4week

        id = self._search(search, year)

        if id is None:
            return 7 * 24 * 60 * 60 * 4, None

        else:
            # print str((timeout, ids['data'][0]))
            return timeout, id


def isAsciiString(mediaName):
    """ Returns True if all characters of the string are ASCII.
    """
    for index, char in enumerate(mediaName):
        if ord(char) >= 128:
            return False
    return True


def toInteger(maybeNumber):
    """ Returns the argument converted to an integer if it represents a number
        or None if the argument is None or does not represent a number.
    """
    try:
        if maybeNumber is not None and str(maybeNumber).strip() != '':
            return int(maybeNumber)
    except:
        pass
    return None


import difflib

SCORE_PENALTY_ITEM_ORDER = 0
SCORE_PENALTY_YEAR = 40
SCORE_PENALTY_TITLE = 40


def computeTitlePenalty(mediaName, title, year=None):
    """ Given media name and a candidate title, returns the title result score penalty.
        @param mediaName Movie title parsed from the file system.
        @param title Movie title from the website.
    """
    mediaName = mediaName.lower()
    title = title.lower()
    if mediaName != title:
        # First approximate the whole strings.
        diffRatio = difflib.SequenceMatcher(None, mediaName, title).ratio()
        penalty = int(SCORE_PENALTY_TITLE * (1 - diffRatio))
        # print '++++++ DIFF("%s", "%s") = %g --> %d' % (mediaName.encode('utf8'), title.encode('utf8'), diffRatio, penalty)

        # If the penalty is more than 1/2 of max title penalty, check to see if
        # this title starts with media name. This means that media name does not
        # have the whole name of the movie - very common case. For example, media name
        # "Кавказская пленница" for a movie title "Кавказская пленница, или Новые приключения Шурика".
        if penalty >= 15:  # This is so that we don't have to do the 'split' every time.
            # Compute the scores of the
            # First, check if the title starts with media name.
            mediaNameParts = mediaName.split()
            titleParts = title.split()
            penaltyYear = 100
            if year:
                diffRatio = difflib.SequenceMatcher(None, mediaName, '%s (%s)' % (title, str(year))).ratio()
                penaltyYear = int(SCORE_PENALTY_TITLE * (1 - diffRatio))
            if len(mediaNameParts) <= len(titleParts):
                i = 0
                # Start with some small penalty, value of which depends on how
                # many words media name has relative to the title's word count.
                penaltyAlt = max(5, int(round((1.0 - (float(len(mediaNameParts)) / len(titleParts))) * 15 - 5)))
                penaltyPerPart = SCORE_PENALTY_TITLE / len(mediaNameParts)
                for mediaNamePart in mediaNameParts:
                    partDiffRatio = difflib.SequenceMatcher(None, mediaNamePart, titleParts[i]).ratio()
                    penaltyAlt = penaltyAlt + int(penaltyPerPart * (1 - partDiffRatio))
                    i = i + 1
                penalty = min(penalty, penaltyAlt, penaltyYear)
                # print '++++++ DIFF("%s", "%s") = %g --> %d' % (mediaName.encode('utf8'), title.encode('utf8'), diffRatio, penalty)
                #    Log.Debug('++++++ DIFF("%s", "%s") = %g --> %d' % (mediaName.encode('utf8'), title.encode('utf8'), diffRatio, penalty))
        return penalty
    return 0


def scoreMediaTitleMatch(mediaName, mediaAltTitle, mediaYear, title, year, itemIndex):
    """ Compares page and media titles taking into consideration
        media item's year and title values. Returns score [0, 100].
        Search item scores 100 when:
          - it's first on the list of results; AND
          - it equals to the media title (ignoring case) OR all media title words are found in the search item; AND
          - search item year equals to media year.

        For now, our title scoring is pretty simple - we check if individual words
        from media item's title are found in the title from search results.
        We should also take into consideration order of words, so that "One Two" would not
        have the same score as "Two One". Also, taking into consideration year difference.
    """
    # add logging that works in unit tests.
    # Log.Debug('comparing item %d::: "%s-%s" with "%s-%s" (%s)...' %
    # (itemIndex, str(mediaName), str(mediaYear), str(title), str(year), str(altTitle)))
    # Max score is when both title and year match exactly.
    score = 100

    # Item order penalty (the lower it is on the list or results, the larger the penalty).
    #score = score - (itemIndex * SCORE_PENALTY_ITEM_ORDER)

    # Compute year penalty: [equal, diff>=3] --> [0, MAX].
    yearPenalty = SCORE_PENALTY_YEAR
    mediaYear = toInteger(mediaYear)
    year = toInteger(year)
    if mediaYear is not None and year is not None:
        yearDiff = abs(mediaYear - year)
        if not yearDiff:
            yearPenalty = 0
        elif yearDiff == 1:
            yearPenalty = int(SCORE_PENALTY_YEAR / 2)
        elif yearDiff == 2:
            yearPenalty = int(SCORE_PENALTY_YEAR / 1)
    else:
        # If year is unknown, don't penalize the score too much.
        yearPenalty = int(SCORE_PENALTY_YEAR / 1)
    score = score - yearPenalty

    # Compute title penalty.
    titlePenalty = computeTitlePenalty(mediaName, title, mediaYear)
    altTitlePenalty, altTitlePenalty2 = 100, 100
    if mediaAltTitle not in [None, '']:
        altTitlePenalty2 = computeTitlePenalty(mediaAltTitle, title, mediaYear)

    titlePenalty = min(titlePenalty, altTitlePenalty, altTitlePenalty2)
    score = score - titlePenalty

    # If the score is not high enough, add a few points to the first result -
    # let's give KinoPoisk some credit :-).
    if itemIndex == 0 and score <= 80:
        score = score + 5

    # IMPORTANT: always return an int.
    score = int(score)
    #  Log.Debug('***** title scored %d' % score)
    return score


def get_best(Data, search, year):
    shows = []
    itemIndex = -1
    if len(search) == 2:
        mediaName, mediaAltTitle = search
    else:
        mediaName, mediaAltTitle = search[0], None
    # print str(shows)+str(mediaAltTitle.encode('utf-8'))+str(year)
    for show in Data:
        itemIndex = itemIndex + 1
        Syear = None
        if isinstance(show[1], unicode):
            Syear = int(show[1].split('-')[0])
        Stitle = show[0]
        id = show[2]

        rate = scoreMediaTitleMatch(mediaName, mediaAltTitle, year, Stitle, Syear, itemIndex)
        shows.append({'rate': rate, 'id': id})

    shows = sorted(shows, key=lambda x: x['rate'], reverse=True)
    log('********************** TheTVDB ******************************')
    log(str(shows) + str(mediaName.encode('utf-8')))
    if shows:
        return shows[0]