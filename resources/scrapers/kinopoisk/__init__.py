# -*- coding: utf-8 -*-
#
# Russian metadata plugin for Plex, which uses http://www.kinopoisk.ru/ to get the tag data.
# Плагин для обновления информации о фильмах использующий КиноПоиск (http://www.kinopoisk.ru/).
# Copyright (C) 2012  Yevgeny Nyden
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# @author zhenya (Yevgeny Nyden)
# @version 1.52
# @revision 148

import common
import pageparser
import LOGGER
import pluginsettings as S
from translit import provide_unicode


IS_DEBUG = True  # TODO - DON'T FORGET TO SET IT TO FALSE FOR A DISTRO.

# Plugin preferences.
# When changing default values here, also update the DefaultPrefs.json file.
PREFS = common.Preferences(
    ('kinopoisk_pref_max_posters', S.KINOPOISK_PREF_DEFAULT_MAX_POSTERS),
    ('kinopoisk_pref_max_art', S.KINOPOISK_PREF_DEFAULT_MAX_ART),
    ('kinopoisk_pref_get_all_actors', S.KINOPOISK_PREF_DEFAULT_GET_ALL_ACTORS),
    ('kinopoisk_pref_imdb_support', S.KINOPOISK_PREF_DEFAULT_IMDB_SUPPORT),
    (None, None),
    ('kinopoisk_pref_imdb_rating', S.KINOPOISK_PREF_DEFAULT_IMDB_RATING),
    ('kinopoisk_pref_kp_rating', S.KINOPOISK_PREF_DEFAULT_KP_RATING))


def Start():
    LOGGER.Info('***** START ***** %s' % common.USER_AGENT)
    PREFS.readPluginPreferences()


def ValidatePrefs():
    LOGGER.Info('***** updating preferences...')
    PREFS.readPluginPreferences()


class KinoPoiskRuAgent():
    name = 'KinoPoiskRu'
    primary_provider = True
    fallback_agent = False
    accepts_from = ['com.plexapp.agents.localmedia']
    contributes_to = None
    parser = pageparser.PageParser(
        LOGGER, common.HttpUtils(S.ENCODING_KINOPOISK_PAGE, pageparser.USER_AGENT), IS_DEBUG)


    # #############################################################################
    ############################# S E A R C H ####################################
    ##############################################################################
    def search(self, results, media, lang, manual=False):
        """ Searches for matches on KinoPoisk using the title and year
            passed via the media object. All matches are saved in a list of results
            as MetadataSearchResult objects. For each results, we determine a
            page id, title, year, and the score (how good we think the match
            is on the scale of 1 - 100).
        """
        LOGGER.Debug('SEARCH START <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        try:
            mediaName = media['name'].decode('utf-8')
        except:
            mediaName = media['name']
        mediaYear = media['year']
        LOGGER.Debug('searching for name="%s", year="%s"...' %
                     (mediaName, str(mediaYear)))

        # Look for matches on KinoPisk (result is returned as an array of tuples [kinoPoiskId, title, year, score]).
        titleResults = KinoPoiskRuAgent.parser.fetchAndParseSearchResults(mediaName, mediaYear)
        for titleResult in titleResults:
            results.append((titleResult[0], titleResult[1], titleResult[2], lang, titleResult[3]))

        # Sort results according to their score (Сортируем результаты).
        LOGGER.Debug('SEARCH END <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
        return results

        #k=KinoPoiskRuAgent()

        #print str(k.search([],{'name':'Django Unchained','year':'2012'},'English'))