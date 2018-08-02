# -*- coding: utf-8 -*-

import time
import urllib

from cache import Cache
from functions import log
import tmdb


class TmDb:
    """
    
    API:
        scraper  - скрапер
        search   - поиск сериалов
        movie    - профайл фильма
        
    """

    def __init__(self, language='en'):
        tmdb.configure("33dd11cb87f2b5fd9ecaff4a81d47edb", language=language)
        dbname='tmdb.%s.db' % language
        self.cache = Cache(dbname, 1.0)

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

    def search(self, name, year):
        return self._search(name, year)


    def movie(self, id):
        id = str(id)
        return self.cache.get('movie:' + id, self._movie, id)


    def _movie(self, id):

        movie = tmdb.Movie(id)

        body = movie.movies
        cast = movie.casts

        # print str(body)

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

        timeout = True
        if not body:
            return timeout, res

        # год
        if body.get('release_date'):
            res['info']['year'] = int(body.get('release_date').split('-')[0])

        # постер
        if body.get('poster_path'):
            res['icon'] = u'http://image.tmdb.org/t/p/original' + body.get('poster_path')
            res['thumbnail'] = u'http://image.tmdb.org/t/p/original' + body.get('poster_path')

        # фанарт
        if body.get('backdrop_path'):
            res['properties']['fanart_image'] = u'http://image.tmdb.org/t/p/original' + body.get('backdrop_path')

        for tag, retag, typeof, targettype in (
                ('plot', 'overview', None, None),
                ('title', 'title', None, None),
                ('originaltitle', 'original_title', None, None),
                ('tagline', 'tagline', None, None),
                ('premiered', 'release_date', None, None),
                ('code', 'imdb_id', None, None),
                ('studio', 'production_companies', list, unicode),
                ('runtime', 'runtime', int, unicode),
                ('votes', 'vote_count', int, unicode),
                ('rating', 'vote_average', float, None),
                ('genre', 'genres', list, unicode),
        ):
            r = body.get(retag)
            if r:
                if typeof == float:
                    res['info'][tag] = float(r)
                elif typeof == list:
                    if targettype == unicode:
                        res['info'][tag] = u', '.join([x for x in [x.get('name') for x in r] if x])
                    else:
                        res['info'][tag] = [x for x in [x.get('name') for x in r] if x]
                elif typeof == int:
                    if targettype == unicode:
                        res['info'][tag] = unicode(r)
                    else:
                        res['info'][tag] = int(r)
                else:
                    res['info'][tag] = r

        if cast and cast.get('cast'):
            info_cast, info_castandrole = [], []
            for role_dict in cast.get('cast'):
                if role_dict.get('name') and role_dict.get('character'):
                    role = role_dict['name'] + u'|' + role_dict['character']
                    info_cast.append(role_dict['name'])
                    info_castandrole.append(role)
            res['info']['cast'] = info_cast
            res['info']['castandrole'] = info_castandrole

        if cast and cast.get('crew'):
            for role_dict in cast.get('crew'):
                if role_dict.get('name') and role_dict.get('job'):
                    if role_dict.get('job') == 'Director':
                        tag = 'director'
                    elif role_dict.get('job') in ['Author', 'Story']:
                        tag = 'writer'
                    else:
                        continue
                    if tag in res['info']:
                        res['info'][tag] = res['info'][tag] + u', ' + role_dict.get('name')
                    else:
                        res['info'][tag] = role_dict.get('name')

        timeout = True
        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if 'year' not in res['info'] or not res['properties']['fanart_image'] \
                or int(res['info']['year']) > time.gmtime(time.time()).tm_year:
            timeout = 7 * 24 * 60 * 60 * 4  #4 week

        return timeout, res

    def _search(self, search, year):
        movie_id = None
        for name in search:
            movies = tmdb.Movies(title=name, year=year, limit=True).get_ordered_matches()
            log('********************************************************')
            try:
                log(str(isAsciiString(movies[1]['title'])))
            except:
                pass

            if len(movies) > 0:
                best = get_best(movies, search, year)
                if best:
                    index = best['itemIndex']
                    if best['rate'] > 70:
                        movie_id = movies[index][1]['id']

            if movie_id:
                break

        return movie_id


    def _scraper(self, name, year):
        timeout = True

        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if year and year > time.gmtime(time.time()).tm_year:
            timeout = 7 * 24 * 60 * 60  # week

        movie_id = self._search(name, year)

        if movie_id is None:
            return 7 * 24 * 60 * 60 * 4, None

        else:
            return timeout, movie_id


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
SCORE_PENALTY_YEAR = 30
SCORE_PENALTY_TITLE = 40


def computeTitlePenalty(mediaName, title):
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
                penalty = min(penalty, penaltyAlt)
                # print '++++++ DIFF("%s", "%s") = %g --> %d' % (mediaName.encode('utf8'), title.encode('utf8'), diffRatio, penalty)
                #    Log.Debug('++++++ DIFF("%s", "%s") = %g --> %d' % (mediaName.encode('utf8'), title.encode('utf8'), diffRatio, penalty))
        return penalty
    return 0


def scoreMediaTitleMatch(mediaName, mediaAltTitle, mediaYear, title, original_title, year, itemIndex, popularity):
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
    if popularity:
        score = score + popularity

    # Compute year penalty: [equal, diff>=3] --> [0, MAX].
    yearPenalty = SCORE_PENALTY_YEAR
    mediaYear = toInteger(mediaYear)
    year = toInteger(year)
    if mediaYear is not None and year is not None:
        yearDiff = abs(mediaYear - year)
        if not yearDiff:
            yearPenalty = 0
        elif yearDiff == 1:
            yearPenalty = int(SCORE_PENALTY_YEAR / 4)
        elif yearDiff == 2:
            yearPenalty = int(SCORE_PENALTY_YEAR / 3)
    else:
        # If year is unknown, don't penalize the score too much.
        yearPenalty = int(SCORE_PENALTY_YEAR / 3)
    score = score - yearPenalty

    # Compute title penalty.
    titlePenalty = computeTitlePenalty(mediaName, title)
    altTitlePenalty, altTitlePenalty2 = 100, 100
    if mediaAltTitle not in [None, '']:
        altTitlePenalty2 = computeTitlePenalty(mediaAltTitle, title)
        if original_title not in [None, '']:
            altTitlePenalty = computeTitlePenalty(mediaAltTitle, original_title)

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
    log('****** Finding TMDB: ' + str(search) + '; year ' + str(year))
    shows = []
    itemIndex = -1
    if len(search) == 2:
        mediaName, mediaAltTitle = search
    else:
        mediaName, mediaAltTitle = search[0], None
    for show in Data:
        show = show[1]
        itemIndex = itemIndex + 1
        Syear = None
        if show.get('release_date'):
            Syear = int(show.get('release_date').split('-')[0])
        Stitle = show.get('title')
        popularity = int(show.get('popularity'))
        Soriginal_title = show.get('original_title')

        rate = scoreMediaTitleMatch(mediaName, mediaAltTitle, year, Stitle, Soriginal_title, Syear, itemIndex,
                                    popularity)
        shows.append({'rate': rate, 'itemIndex': itemIndex})

    shows = sorted(shows, key=lambda x: x['rate'], reverse=True)
    for s in shows:
        i = int(s['itemIndex'])
        show = Data[i][1]
        if isinstance(show.get('release_date'), str):
            release_date=str(show.get('release_date').split('-')[0])
        else:
            release_date='0'
        log(' ... %d: id="%s", name="%s", year="%s", score="%d".' %
               (i, str(show['id']), show.get('title').encode('utf-8'), release_date,
                s['rate']))
    if shows:
        return shows[0]