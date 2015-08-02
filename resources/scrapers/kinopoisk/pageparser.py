# -*- coding: utf-8 -*-
#
# Russian metadata plugin for Plex, which uses http://www.kinopoisk.ru/ to get the tag data.
# Плагин для обновления информации о фильмах использующий КиноПоиск (http://www.kinopoisk.ru/).
# Copyright (C) 2013 Yevgeny Nyden
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
# @version 1.52
# @revision 148

import re
import urllib
import operator

import common
import pluginsettings as S
import translit





# MATCHER_MOVIE_DURATION = re.compile('\s*(\d+).*?', re.UNICODE | re.DOTALL)
# MATCHER_IMDB_RATING = re.compile('IMDb:\s*(\d+\.?\d*)\s*\(\s*([\s\d]+)\s*\)', re.UNICODE | re.DOTALL)
# MATCHER_IMDB_RATING = re.compile('IMDb:\s*(\d+\.?\d*)\s?\((.*)\)', re.UNICODE)

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22'
'''
MOVIE_THUMBNAIL_SMALL_WIDTH = 130
MOVIE_THUMBNAIL_SMALL_HEIGHT = 168
MOVIE_THUMBNAIL_BIG_WIDTH = 780
MOVIE_THUMBNAIL_BIG_HEIGHT = 1024

# Compiled regex matchers.
MATCHER_WIDTH_FROM_STYLE = re.compile('.*width\s*:\s*(\d+)px.*', re.UNICODE)
MATCHER_HEIGHT_FROM_STYLE = re.compile('.*height\s*:\s*(\d+)px.*', re.UNICODE)
MATCHER_LEADING_NONALPHA = re.compile('^[\s\d\.\(\)]*', re.UNICODE | re.MULTILINE)


# Русские месяца, пригодятся для определения дат.
RU_MONTH = {
  u'января': '01',
  u'февраля': '02',
  u'марта': '03',
  u'апреля': '04',
  u'мая': '05',
  u'июня': '06',
  u'июля': '07',
  u'августа': '08',
  u'сентября': '09',
  u'октября': '10',
  u'ноября': '11',
  u'декабря': '12'
}
'''


class PageParser:
    def __init__(self, logger, httpUtils=common.HttpUtils(S.ENCODING_KINOPOISK_PAGE, USER_AGENT), isDebug=False):
        self.log = logger
        self.isDebug = isDebug
        self.httpUtils = httpUtils

    def fetchAndParseSearchResults(self, mediaName, mediaYear, mediaAltName=None):
        """ Searches for movie titles on KinoPoisk.
            @param mediaName Movie title parsed from a filename.
            @param mediaName Movie year parsed from a filename.
            @return Array of tuples: [kinoPoiskId, title, year, score]
        """
        self.log.Info('Quering kinopoisk...')
        results = self.queryKinoPoisk(mediaName, mediaYear)

        # Check media name is all ASCII characters, and if it is,
        # issue another query to KinoPoisk using a translified media name;
        # lastly, merge the scored results.
        if common.isAsciiString(mediaName):
            translifiedMediaName = translit.detranslify(mediaName)
            moreResults = self.queryKinoPoisk(translifiedMediaName, mediaYear)
            resultsMap = dict()
            for result in results:
                resultsMap[result[0]] = result
            results = []  # Recreate and repopulate the results array removing duplicates.
            for result in moreResults:
                currId = result[0]
                if currId in resultsMap.keys():
                    origResult = resultsMap[currId]
                    del resultsMap[currId]
                    if result[3] >= origResult[3]:
                        results.append(result)
                    else:
                        results.append(origResult)
                else:
                    results.append(result)
            results.extend(resultsMap.values())

        if mediaAltName:
            moreResults = self.queryKinoPoisk(mediaAltName, mediaYear)
            resultsMap = dict()
            for result in results:
                resultsMap[result[0]] = result
            results = []  # Recreate and repopulate the results array removing duplicates.
            for result in moreResults:
                currId = result[0]
                if currId in resultsMap.keys():
                    origResult = resultsMap[currId]
                    del resultsMap[currId]
                    if result[3] >= origResult[3]:
                        results.append(result)
                    else:
                        results.append(origResult)
                else:
                    results.append(result)
            results.extend(resultsMap.values())

        # Sort all results based on their score.
        results.sort(key=operator.itemgetter(3))
        results.reverse()
        if self.isDebug:
            self.log.Debug('Search produced %d results:' % len(results))
            index = -1
            for result in results:
                index += 1
                self.log.Debug(' ... %d: id="%s", name="%s", year="%s", score="%d".' %
                               (index, result[0], result[1], str(result[2]), result[3]))
        return results

    def queryKinoPoisk(self, mediaName, mediaYear):
        """ Ищет фильм на кинопоиске.
            Returns title results as they are returned (no sorting is done here!).
        """
        results = []
        try:
            encodedName = urllib.quote(mediaName.encode(S.ENCODING_KINOPOISK_PAGE))
        except:
            encodedName = urllib.quote(mediaName.encode('utf-8'))
        page = self.httpUtils.requestAndParseHtmlPage(S.KINOPOISK_SEARCH_SIMPLE % encodedName)
        if page is None:
            self.log.Warn(' ### nothing was found on kinopoisk for media name "%s"' % mediaName)
            return results

        # Страница получена, берем с нее перечень всех названий фильмов.
        self.log.Debug('**** Finding %s (%s) got a KinoPoisk...' % (mediaName, mediaYear))

        reobj = re.compile(r'<span><a href="http://m\.kinopoisk\.ru/movie/(\d+)/">(.+?)</a><br />(.+?)</span>')
        result = reobj.findall(page)

        # Inspect query results titles and score them.
        self.log.Debug('found %d results (div info tags)' % len(result))
        itemIndex = -1
        for itemKinoPoiskId, itemTitleitemYear, itemAltTitle in result:
            itemIndex = itemIndex + 1
            itemAltTitle = itemAltTitle.replace('&nbsp;', '')
            try:
                itemTitle, itemYear = re.compile('^(.+?), (\d\d\d\d)$').findall(itemTitleitemYear.strip())[0]
            except:
                itemYear = None
                itemTitle = itemTitleitemYear
            itemScore = common.scoreMediaTitleMatch(mediaName, mediaYear, itemTitle, itemAltTitle, itemYear, itemIndex)
            results.append([itemKinoPoiskId, itemTitle, itemYear, itemScore])

        return results
