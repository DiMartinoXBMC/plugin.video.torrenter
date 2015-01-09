# -*- coding: utf-8 -*-
#
# Global definitions for KinoPoiskRu plugin.
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

# Default plugin preferences. When modifying, please also change
# corresponding values in the ../DefaultPrefs.json file.
KINOPOISK_PREF_DEFAULT_MAX_POSTERS = 1
KINOPOISK_PREF_DEFAULT_MAX_ART = 2
KINOPOISK_PREF_DEFAULT_GET_ALL_ACTORS = False
KINOPOISK_PREF_DEFAULT_IMDB_SUPPORT = True
KINOPOISK_PREF_DEFAULT_IMDB_RATING = False
KINOPOISK_PREF_DEFAULT_KP_RATING = False

ENCODING_KINOPOISK_PAGE = 'cp1251'

# Разные страницы сайта.
KINOPOISK_SITE_BASE = 'http://www.kinopoisk.ru/'
KINOPOISK_RESOURCE_BASE = 'http://st.kinopoisk.ru/'
KINOPOISK_TITLE_PAGE_URL = KINOPOISK_SITE_BASE + 'film/%s/'
KINOPOISK_CAST_PAGE_URL = KINOPOISK_SITE_BASE + 'film/%s/cast/'
KINOPOISK_STUDIO_PAGE_URL = KINOPOISK_SITE_BASE + 'film/%s/studio/'
KINOPOISK_THUMBNAIL_BIG_URL = KINOPOISK_RESOURCE_BASE + 'images/film_big/%s.jpg'
KINOPOISK_THUMBNAIL_SMALL_URL = KINOPOISK_RESOURCE_BASE + 'images/film/%s.jpg'
KINOPOISK_POSTERS_URL = KINOPOISK_SITE_BASE + 'film/%s/posters/page/%d/'
KINOPOISK_STILLS_URL = KINOPOISK_SITE_BASE + 'film/%s/stills/page/%d/'

# Страница поиска.
KINOPOISK_SEARCH = KINOPOISK_SITE_BASE + 'index.php?first=no&kp_query=%s'
KINOPOISK_SEARCH_SIMPLE = 'http://m.kinopoisk.ru/search/%s/'