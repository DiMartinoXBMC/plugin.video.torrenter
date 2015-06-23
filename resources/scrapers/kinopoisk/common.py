# -*- coding: utf-8 -*-
#
# Russian metadata plugin for Plex, which uses http://www.kinopoisk.ru/ to get the tag data.
# Плагин для обновления информации о фильмах использующий КиноПоиск (http://www.kinopoisk.ru/).
# Copyright (C) 2012 Yevgeny Nyden
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# @author zhenya (Yevgeny Nyden)
# @revision 148

import sys
import math
import difflib

import translit
from HTTP import *

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22'
# USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_2) AppleWebKit/534.51.22 (KHTML, like Gecko) Version/5.1.1 Safari/534.51.22'
ENCODING_PLEX = 'utf-8'

SCORE_PENALTY_ITEM_ORDER = 2
SCORE_PENALTY_YEAR = 30
SCORE_PENALTY_TITLE = 40

IMAGE_SCORE_MAX_NUMBER_OF_ITEMS = 5
IMAGE_SCORE_ITEM_ORDER_BONUS_MAX = 25
IMAGE_SCORE_RESOLUTION_BONUS_MAX = 25
IMAGE_SCORE_RATIO_BONUS_MAX = 45
IMAGE_SCORE_THUMB_BONUS = 5
POSTER_SCORE_MIN_RESOLUTION_PX = 60 * 1000
POSTER_SCORE_MAX_RESOLUTION_PX = 600 * 1000
POSTER_SCORE_BEST_RATIO = 0.7
ART_SCORE_BEST_RATIO = 1.5
ART_SCORE_MIN_RESOLUTION_PX = 200 * 1000
ART_SCORE_MAX_RESOLUTION_PX = 1000 * 1000


class Preferences:
    """ These instance variables are populated from plugin preferences.
    """

    def __init__(self,
                 (maxPostersName, maxPostersDefault),
                 (maxArtName, maxArtDefault),
                 (getAllActorsName, getAllActorsDefault),
                 (imdbSupportName, imdbSupportDefault),
                 (cacheTimeName, cacheTimeDefault),
                 (imdbRatingName, imdbRatingDefault),
                 (additionalRatingName, additionalRatingDefault)):
        self.maxPostersName = maxPostersName
        self.maxPosters = maxPostersDefault
        self.maxArtName = maxArtName
        self.maxArt = maxArtDefault
        self.getAllActorsName = getAllActorsName
        self.getAllActors = getAllActorsDefault
        self.imdbSupportName = imdbSupportName
        self.imdbSupport = imdbSupportDefault
        self.cacheTimeName = cacheTimeName
        self.cacheTime = cacheTimeDefault
        self.cacheTimeDefault = cacheTimeDefault
        self.imdbRatingName = imdbRatingName
        self.imdbRating = imdbRatingDefault
        self.additionalRatingName = additionalRatingName
        self.additionalRating = additionalRatingDefault

    def readPluginPreferences(self):
        # Setting image (poster and funart) preferences.
        if self.maxPostersName is not None:
            self.maxPosters = int(Prefs[self.maxPostersName])
            Log.Debug('PREF: Max poster results is set to %d.' % self.maxPosters)
        if self.maxArtName is not None:
            self.maxArt = int(Prefs[self.maxArtName])
            Log.Debug('PREF: Max art results is set to %d.' % self.maxArt)
        if self.getAllActorsName is not None:
            self.getAllActors = Prefs[self.getAllActorsName]
            Log.Debug('PREF: Parse all actors is set to %s.' % str(self.getAllActors))

        # Setting IMDB support.
        if self.imdbSupportName is not None:
            self.imdbSupport = Prefs[self.imdbSupportName]
            Log.Debug('PREF: IMDB support is set to %s.' % str(self.imdbSupport))

        # Setting cache expiration time.
        if self.cacheTimeName is not None:
            self.cacheTime = parseAndSetCacheTimeFromPrefs(self.cacheTimeName, self.cacheTimeDefault)

        # Setting IMDB rating.
        if self.imdbRatingName is not None:
            self.imdbRating = Prefs[self.imdbRatingName]
        Log.Debug('PREF: IMDB rating is set to %s.' % str(self.imdbRating))

        # Setting kinopoisk.ru rating.
        if self.additionalRatingName is not None:
            self.additionalRating = Prefs[self.additionalRatingName]
        Log.Debug('PREF: kinopoisk rating is set to %s.' % str(self.additionalRating))


def getElementFromHttpRequest(url, encoding, userAgent=USER_AGENT):
    """ Fetches a given URL and returns it as an element.
        Функция преобразования html-кода в xml-код.
    """
    for i in range(3):
        errorCount = 0
        try:
            req = HTTPRequest(url, headers={'User-agent': userAgent, 'Accept': 'text/html'})
            response = HTTP().fetch(req)
            return str(response.body).decode(encoding)
        except:
            errorCount += 1
            Log.Debug('Error fetching URL: "%s".' % url)
            time.sleep(1 + errorCount)
    return None


def requestImageJpeg(url, userAgent):
    """ Requests an image given its URL and returns a request object.
    """
    try:
        response = HTTP.Request(url, headers={
            'User-agent': userAgent,
            'Accept': 'image/jpeg'
        })
        return response
    except:
        Log.Debug('Error fetching URL: "%s".' % url)
    return None


def getWin1252ResponseFromHttpRequest(url):
    """ Requests an image given its URL and returns a request object.
    """
    try:
        response = HTTP.Request(url, headers={
            'User-agent': USER_AGENT,
            'Accept-Charset': 'ISO-8859-1;q=0.7,*;q=0.3',
            'Accept-Language': 'en-US,en;q=0.8'
        })
        return response
    except:
        Log.Error('Error fetching URL: "%s".' % url)
    return None


def printSearchArrayResults(results):
    """ Sends a list of media array results to debug log.
    """
    Log.Debug('Search produced %d results:' % len(results))
    index = -1
    for result in results:
        index += 1
        Log.Debug(' ... %d: id="%s", name="%s", year="%s", score="%d".' %
                  (index, result[0], result[1], str(result[2]), result[3]))


def printSearchResults(results):
    """ Sends a list of media results to debug log.
    """
    Log.Debug('Search produced %d results:' % len(results))
    index = 0
    for result in results:
        Log.Debug(' ... %d: id="%s", name="%s", year="%s", score="%d".' %
                  (index, result.id, result.name, str(result.year), result.score))
        index += 1


def printImageSearchResults(thumbnailList):
    Log.Debug('printing %d image results:' % len(thumbnailList))
    index = 0
    for result in thumbnailList:
        Log.Debug(' ... %d: index=%s, score=%s, URL="%s".' %
                  (index, result.index, result.score, result.url))
        index += 1
    return None


def logException(msg):
    excInfo = sys.exc_info()
    Log.Exception('%s; exception: %s; cause: %s' % (msg, excInfo[0], excInfo[1]))


def scoreMediaTitleMatch(mediaName, mediaYear, title, altTitle, year, itemIndex):
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
    # TODO(zhenya): add logging that works in unit tests.
    #  Log.Debug('comparing item %d::: "%s-%s" with "%s-%s" (%s)...' %
    #      (itemIndex, str(mediaName), str(mediaYear), str(title), str(year), str(altTitle)))
    # Max score is when both title and year match exactly.
    score = 100

    # Item order penalty (the lower it is on the list or results, the larger the penalty).
    score = score - (itemIndex * SCORE_PENALTY_ITEM_ORDER)

    # Compute year penalty: [equal, diff>=3] --> [0, MAX].
    yearPenalty = SCORE_PENALTY_YEAR
    mediaYear = toInteger(mediaYear)
    year = toInteger(year)
    if mediaYear is not None and year is not None:
        yearDiff = abs(mediaYear - year)
        if not yearDiff:
            yearPenalty = 0
        elif yearDiff == 1:
            yearPenalty = 15
        elif yearDiff == 2:
            yearPenalty = 25
    score = score - yearPenalty
    # print str(mediaYear)+' '+str(year)+' '+str(yearPenalty)

    # Compute title penalty.
    titlePenalty = computeTitlePenalty(mediaName, title)
    altTitlePenalty = 100
    if altTitle is not None:
        altTitlePenalty = computeTitlePenalty(mediaName, altTitle)

    # Get detranlitirated media name (in case filename is in latin characters),
    # compare it's score with the original, and pick the min.
    try:
        altMediaName = translit.detranslify(mediaName)
        detranslifiedTitlePenalty = computeTitlePenalty(altMediaName, title)
        titlePenalty = min(detranslifiedTitlePenalty, titlePenalty)
        if altTitle is not None:
            detranslifiedAltTitlePenalty = computeTitlePenalty(altMediaName, altTitle)
            altTitlePenalty = min(detranslifiedAltTitlePenalty, altTitlePenalty)
    except:
        pass

    titlePenalty = min(titlePenalty, altTitlePenalty)
    score = score - titlePenalty

    # If the score is not high enough, add a few points to the first result -
    # let's give KinoPoisk some credit :-).
    if itemIndex == 0 and score <= 80:
        score = score + 5

    # IMPORTANT: always return an int.
    score = int(score)
    #  Log.Debug('***** title scored %d' % score)
    return score


def scoreThumbnailResult(thumb, isPoster):
    """ Given a Thumbnail object that represents an poster or a funart result,
        scores it, and stores the score on the passed object (thumb.score).
    """
    score = 0
    if thumb.url is None:
        thumb.score = 0
        return

    if thumb.index < IMAGE_SCORE_MAX_NUMBER_OF_ITEMS:
        # Score bonus from index for items below 10 on the list.
        bonus = IMAGE_SCORE_ITEM_ORDER_BONUS_MAX * \
                ((IMAGE_SCORE_MAX_NUMBER_OF_ITEMS - thumb.index) / float(IMAGE_SCORE_MAX_NUMBER_OF_ITEMS))
        score += bonus

    if thumb.width is not None and thumb.height is not None:
        # Get a resolution bonus if width*height is more than a certain min value.
        if isPoster:
            minPx = POSTER_SCORE_MIN_RESOLUTION_PX
            maxPx = POSTER_SCORE_MAX_RESOLUTION_PX
            bestRatio = POSTER_SCORE_BEST_RATIO
        else:
            minPx = ART_SCORE_MIN_RESOLUTION_PX
            maxPx = ART_SCORE_MAX_RESOLUTION_PX
            bestRatio = ART_SCORE_BEST_RATIO
        pixelsCount = thumb.width * thumb.height
        if pixelsCount > minPx:
            if pixelsCount > maxPx:
                pixelsCount = maxPx
            bonus = float(IMAGE_SCORE_RESOLUTION_BONUS_MAX) * \
                    float((pixelsCount - minPx)) / float((maxPx - minPx))
            score += bonus

        # Get an orientation (Portrait vs Landscape) bonus. (we prefer images that are have portrait orientation.
        ratio = thumb.width / float(thumb.height)
        ratioDiff = math.fabs(bestRatio - ratio)
        if ratioDiff < 0.5:
            bonus = IMAGE_SCORE_RATIO_BONUS_MAX * (0.5 - ratioDiff) * 2.0
            score += bonus

    # Get a bonus if image has a separate thumbnail URL.
    if thumb.thumbUrl is not None and thumb.url != thumb.thumbUrl:
        score += IMAGE_SCORE_THUMB_BONUS

    thumb.score = int(score)


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
                #    print '++++++ DIFF("%s", "%s") = %g --> %d' % (mediaName.encode('utf8'), title.encode('utf8'), diffRatio, penalty)
                #    Log.Debug('++++++ DIFF("%s", "%s") = %g --> %d' % (mediaName.encode('utf8'), title.encode('utf8'), diffRatio, penalty))
        return penalty
    return 0


class HttpUtils():
    def __init__(self, encoding, userAgent):
        self.encoding = encoding
        self.userAgent = userAgent

    def requestAndParseHtmlPage(self, url):
        return getElementFromHttpRequest(url, self.encoding, self.userAgent)

    def requestImageJpeg(self, url):
        return requestImageJpeg(url, self.userAgent)
