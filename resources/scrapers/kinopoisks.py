# -*- coding: utf-8 -*-

import re
import time
import urllib

from net import HTTP
from cache import Cache
from html import Clear
import kinopoisk.LOGGER
import kinopoisk.pageparser
import kinopoisk.common

GENRE = {
    'anime': 1750,
    'biography': 22,
    'action': 3,
    'western': 13,
    'military': 19,
    'detective': 17,
    'children': 456,
    'for adults': 20,
    'documentary': 12,
    'drama': 8,
    'game': 27,
    'history': 23,
    'comedy': 6,
    'concert': 1747,
    'short': 15,
    'criminal': 16,
    'romance': 7,
    'music': 21,
    'cartoon': 14,
    'musical': 9,
    'news': 28,
    'adventures': 10,
    'realitytv': 25,
    'family': 11,
    'sports': 24,
    'talk shows': 26,
    'thriller': 4,
    'horror': 1,
    'fiction': 2,
    'filmnoir': 18,
    'fantasy': 5
}

COUNTRIES = (
    (0, u'Все'),
    (2, u'Россия'),
    (1, u'США'),
    (13, u'СССР'),
    (25, u'Австралия'),
    (57, u'Австрия'),
    (136, u'Азербайджан'),
    (120, u'Албания'),
    (20, u'Алжир'),
    (1026, u'Американские Виргинские острова'),
    (139, u'Ангола'),
    (159, u'Андорра'),
    (1044, u'Антарктида'),
    (1030, u'Антигуа и Барбуда'),
    (1009, u'Антильские Острова'),
    (24, u'Аргентина'),
    (89, u'Армения'),
    (175, u'Аруба'),
    (113, u'Афганистан'),
    (124, u'Багамы'),
    (75, u'Бангладеш'),
    (105, u'Барбадос'),
    (164, u'Бахрейн'),
    (69, u'Беларусь'),
    (173, u'Белиз'),
    (41, u'Бельгия'),
    (140, u'Бенин'),
    (109, u'Берег Слоновой кости'),
    (1004, u'Бермуды'),
    (148, u'Бирма'),
    (63, u'Болгария'),
    (118, u'Боливия'),
    (178, u'Босния'),
    (39, u'Босния-Герцеговина'),
    (145, u'Ботсвана'),
    (10, u'Бразилия'),
    (92, u'Буркина-Фасо'),
    (162, u'Бурунди'),
    (114, u'Бутан'),
    (1059, u'Вануату'),
    (11, u'Великобритания'),
    (49, u'Венгрия'),
    (72, u'Венесуэла'),
    (1043, u'Восточная Сахара'),
    (52, u'Вьетнам'),
    (170, u'Вьетнам Северный'),
    (127, u'Габон'),
    (99, u'Гаити'),
    (165, u'Гайана'),
    (1040, u'Гамбия'),
    (144, u'Гана'),
    (135, u'Гватемала'),
    (129, u'Гвинея'),
    (116, u'Гвинея-Бисау'),
    (3, u'Германия'),
    (60, u'Германия (ГДР)'),
    (18, u'Германия (ФРГ)'),
    (1022, u'Гибралтар'),
    (112, u'Гондурас'),
    (28, u'Гонконг'),
    (117, u'Гренландия'),
    (55, u'Греция'),
    (61, u'Грузия'),
    (142, u'Гуаделупа'),
    (1045, u'Гуам'),
    (4, u'Дания'),
    (1037, u'Демократическая Республика Конго'),
    (1028, u'Джибути'),
    (1031, u'Доминика'),
    (128, u'Доминикана'),
    (101, u'Египет'),
    (155, u'Заир'),
    (133, u'Замбия'),
    (104, u'Зимбабве'),
    (42, u'Израиль'),
    (29, u'Индия'),
    (73, u'Индонезия'),
    (154, u'Иордания'),
    (90, u'Ирак'),
    (48, u'Иран'),
    (38, u'Ирландия'),
    (37, u'Исландия'),
    (15, u'Испания'),
    (14, u'Италия'),
    (169, u'Йемен'),
    (146, u'Кабо-Верде'),
    (122, u'Казахстан'),
    (1051, u'Каймановы острова'),
    (84, u'Камбоджа'),
    (95, u'Камерун'),
    (6, u'Канада'),
    (1002, u'Катар'),
    (100, u'Кения'),
    (64, u'Кипр'),
    (1024, u'Кирибати'),
    (31, u'Китай'),
    (56, u'Колумбия'),
    (1058, u'Коморы'),
    (134, u'Конго'),
    (1014, u'Конго (ДРК)'),
    (156, u'Корея'),
    (137, u'Корея Северная'),
    (26, u'Корея Южная'),
    (1013, u'Косово'),
    (131, u'Коста-Рика'),
    (76, u'Куба'),
    (147, u'Кувейт'),
    (86, u'Кыргызстан'),
    (149, u'Лаос'),
    (54, u'Латвия'),
    (1015, u'Лесото'),
    (176, u'Либерия'),
    (97, u'Ливан'),
    (126, u'Ливия'),
    (123, u'Литва'),
    (125, u'Лихтенштейн'),
    (59, u'Люксембург'),
    (115, u'Маврикий'),
    (67, u'Мавритания'),
    (150, u'Мадагаскар'),
    (153, u'Макао'),
    (80, u'Македония'),
    (1025, u'Малави'),
    (83, u'Малайзия'),
    (151, u'Мали'),
    (1050, u'Мальдивы'),
    (111, u'Мальта'),
    (43, u'Марокко'),
    (102, u'Мартиника'),
    (1042, u'Масаи'),
    (17, u'Мексика'),
    (1041, u'Мелкие отдаленные острова США'),
    (81, u'Мозамбик'),
    (58, u'Молдова'),
    (22, u'Монако'),
    (132, u'Монголия'),
    (1034, u'Мьянма'),
    (91, u'Намибия'),
    (106, u'Непал'),
    (157, u'Нигер'),
    (110, u'Нигерия'),
    (12, u'Нидерланды'),
    (138, u'Никарагуа'),
    (35, u'Новая Зеландия'),
    (1006, u'Новая Каледония'),
    (33, u'Норвегия'),
    (119, u'ОАЭ'),
    (1019, u'Оккупированная Палестинская территория'),
    (1003, u'Оман'),
    (1052, u'Остров Мэн'),
    (1047, u'Остров Святой Елены'),
    (1007, u'острова Теркс и Кайкос'),
    (74, u'Пакистан'),
    (1057, u'Палау'),
    (78, u'Палестина'),
    (107, u'Панама'),
    (163, u'Папуа - Новая Гвинея'),
    (143, u'Парагвай'),
    (23, u'Перу'),
    (32, u'Польша'),
    (36, u'Португалия'),
    (82, u'Пуэрто Рико'),
    (1036, u'Реюньон'),
    (1033, u'Российская империя'),
    (2, u'Россия'),
    (103, u'Руанда'),
    (46, u'Румыния'),
    (121, u'Сальвадор'),
    (1039, u'Самоа'),
    (1011, u'Сан-Марино'),
    (158, u'Саудовская Аравия'),
    (1029, u'Свазиленд'),
    (1010, u'Сейшельские острова'),
    (65, u'Сенегал'),
    (1055, u'Сент-Винсент и Гренадины'),
    (1049, u'Сент-Люсия'),
    (177, u'Сербия'),
    (174, u'Сербия и Черногория'),
    (1021, u'Сиам'),
    (45, u'Сингапур'),
    (98, u'Сирия'),
    (94, u'Словакия'),
    (40, u'Словения'),
    (160, u'Сомали'),
    (13, u'СССР'),
    (167, u'Судан'),
    (171, u'Суринам'),
    (1, u'США'),
    (1023, u'Сьерра-Леоне'),
    (70, u'Таджикистан'),
    (44, u'Таиланд'),
    (27, u'Тайвань'),
    (130, u'Танзания'),
    (161, u'Того'),
    (1012, u'Тонго'),
    (88, u'Тринидад и Тобаго'),
    (1053, u'Тувалу'),
    (50, u'Тунис'),
    (152, u'Туркменистан'),
    (68, u'Турция'),
    (172, u'Уганда'),
    (71, u'Узбекистан'),
    (62, u'Украина'),
    (79, u'Уругвай'),
    (1008, u'Фарерские острова'),
    (1038, u'Федеративные Штаты Микронезии'),
    (166, u'Фиджи'),
    (47, u'Филиппины'),
    (7, u'Финляндия'),
    (8, u'Франция'),
    (1032, u'Французская Гвиана'),
    (1046, u'Французская Полинезия'),
    (85, u'Хорватия'),
    (141, u'ЦАР'),
    (77, u'Чад'),
    (1020, u'Черногория'),
    (34, u'Чехия'),
    (16, u'Чехословакия'),
    (51, u'Чили'),
    (21, u'Швейцария'),
    (5, u'Швеция'),
    (108, u'Шри-Ланка'),
    (96, u'Эквадор'),
    (87, u'Эритрея'),
    (53, u'Эстония'),
    (168, u'Эфиопия'),
    (30, u'ЮАР'),
    (19, u'Югославия'),
    (66, u'Югославия (ФР)'),
    (93, u'Ямайка'),
    (9, u'Япония')
)


class KinoPoisk:
    """
    
    API:
        scraper  - скрапер
        movie    - профайл фильма
        search   - поиск фильма
        best     - поиск лучших фильмов
        person   - поиск персон
        work     - информация о работах персоны
        
    """

    def __init__(self, language='ru'):
        dbname = 'kinopoisk.%s.db' % language
        self.cache = Cache(dbname, 1.0)
        self.html = Clear()

        self.timeout = 60.0

        self.http = HTTP()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:10.0.2) Gecko/20100101 Firefox/10.0.2',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-ru,ru;q=0.8,en-us;q=0.5,en;q=0.3',
            'Cache-Control': 'no-cache',
            'Referer': 'http://www.kinopoisk.ru/level/7/'
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

    def movie(self, id):
        id = str(id)
        return self.cache.get('movie:' + id, self._movie, id)

    def search(self, search, year):
        return self._search_movie(search, year)

    def countries(self):
        return COUNTRIES

    def country(self, id, default=None):
        country = [x[1] for x in COUNTRIES if x[0] == id]
        return country[0] if country else default

    def _search_movie(self, search, year=None):
        parser = kinopoisk.pageparser.PageParser(kinopoisk.LOGGER, isDebug=True)
        orginalname = search[0]
        if len(search) > 1:
            name = search[1]
        else:
            name = None
        results = parser.fetchAndParseSearchResults(orginalname, year, name)
        if results and results[0][3] > 70:
            return results[0][0]

    def _scraper(self, search, year):
        timeout = True

        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if year and year > time.gmtime(time.time()).tm_year:
            timeout = 7 * 24 * 60 * 60 * 4  # 4 week

        movie_id = self._search_movie(search, year)

        if movie_id is None:
            # сохраняем пустой результат на 4 week
            return 7 * 24 * 60 * 60 * 4, None

        else:
            return timeout, movie_id

    def _movie(self, id):
        response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/', headers=self.headers,
                                   timeout=self.timeout)
        if response.error:
            return False, None

        html = response.body.decode('windows-1251')

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

        # имя, оригинальное имя, девиз, цензура, год, top250
        # runtime - длительность фильма (в отдельную переменную, иначе не видно размер файла)
        for tag, reg, cb in (
                ('title', '<title>(.+?)</title>', self.html.string),
                ('originaltitle', 'itemprop="alternativeHeadline">([^<]*)</span>', self.html.string),
                ('tagline', '<td style="color\: #555">&laquo;(.+?)&raquo;</td></tr>', self.html.string),
                ('mpaa', 'images/mpaa/([^\.]+).gif', self.html.string),
                ('runtime', '<td class="time" id="runtime">[^<]+<span style="color\: #999">/</span>([^<]+)</td>',
                 self.html.string),
                ('year', '<a href="/lists/m_act%5Byear%5D/([0-9]+)/"', int),
                ('top250', 'Топ250\: <a\shref="/level/20/#([0-9]+)', int)

        ):
            r = re.compile(reg, re.U).search(html)
            if r:
                value = r.group(1).strip()
                if value:
                    res['info'][tag] = cb(value)


        # режисеры, сценаристы, жанры
        for tag, reg in (
                ('director', u'<td itemprop="director">(.+?)</td>'),
                ('writer', u'<td class="type">сценарий</td><td[^>]*>(.+?)</td>'),
                ('genre', u'<span itemprop="genre">(.+?)</span>')
        ):
            r = re.compile(reg, re.U | re.S).search(html)
            if r:
                r2 = []
                for r in re.compile('<a href="[^"]+">([^<]+)</a>', re.U).findall(r.group(1)):
                    r = self.html.string(r)
                    if r and r != '...':
                        r2.append(r)
                if r2:
                    res['info'][tag] = u', '.join(r2)

        # актеры
        r = re.compile(u'<h4>В главных ролях:</h4>(.+?)</ul>', re.U | re.S).search(html)
        if r:
            actors = []
            for r in re.compile('<li itemprop="actors"><a [^>]+>([^<]+)</a></li>', re.U).findall(r.group(1)):
                r = self.html.string(r)
                if r and r != '...':
                    actors.append(r)
            if actors:
                res['info']['cast'] = actors[:]
                # res['info']['castandrole'] = actors[:]

        # описание фильма
        r = re.compile('<span class="_reachbanner_"><div class="brand_words" itemprop="description">(.+?)</div></span>',
                       re.U).search(html)
        if r:
            plot = self.html.text(r.group(1).replace('<=end=>', '\n'))
            if plot:
                res['info']['plot'] = plot

        # IMDB
        r = re.compile('IMDb: ([0-9.]+) \(([0-9\s]+)\)</div>', re.U).search(html)
        if r:
            res['info']['rating'] = float(r.group(1).strip())
            res['info']['votes'] = r.group(2).strip()


        # премьера
        r = re.compile(u'премьера \(мир\)</td>(.+?)</tr>', re.U | re.S).search(html)
        if r:
            r = re.compile(u'data\-ical\-date="([^"]+)"', re.U | re.S).search(r.group(1))
            if r:
                data = r.group(1).split(' ')
                if len(data) == 3:
                    i = 0
                    for mon in (
                            u'января', u'февраля', u'марта', u'апреля', u'мая', u'июня', u'июля', u'августа',
                            u'сентября',
                            u'октября', u'ноября', u'декабря'):
                        i += 1
                        if mon == data[1]:
                            mon = str(i)
                            if len(mon) == 1:
                                mon = '0' + mon
                            day = data[0]
                            if len(day) == 1:
                                day = '0' + day
                            res['info']['premiered'] = '-'.join([data[2], mon, day])
                            break


        # постер
        r = re.compile(u'onclick="openImgPopup\(([^\)]+)\)', re.U | re.S).search(html)
        if r:
            poster = r.group(1).replace("'", '').strip()
            if poster:
                res['thumbnail'] = res['icon'] = 'http://kinopoisk.ru' + poster

        menu = re.compile('<ul id="newMenuSub" class="clearfix(.+?)<!\-\- /menu \-\->', re.U | re.S).search(html)
        if menu:
            menu = menu.group(1)

            # фанарт
            if menu.find('/film/' + id + '/wall/') != -1:
                response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/wall/', headers=self.headers,
                                           timeout=self.timeout)
                if not response.error:
                    html = response.body.decode('windows-1251')
                    fanart = re.compile('<a href="/picture/([0-9]+)/w_size/([0-9]+)/">', re.U).findall(html)
                    if fanart:
                        fanart.sort(cmp=lambda (id1, size1), (id2, size2): cmp(int(size1), int(size2)))

                        # пробуем взять максимально подходящее
                        fanart_best = [x for x in fanart if int(x[1]) <= 1280]
                        if fanart_best:
                            fanart = fanart_best

                        response = self.http.fetch(
                            'http://www.kinopoisk.ru/picture/' + fanart[-1][0] + '/w_size/' + fanart[-1][1] + '/',
                            headers=self.headers, timeout=self.timeout)
                        if not response.error:
                            html = response.body.decode('windows-1251')
                            r = re.compile('id="image" src="([^"]+)"', re.U | re.S).search(html)
                            if r:
                                res['properties']['fanart_image'] = r.group(1).strip()


            # если нет фанарта (обоев), то пробуем получить кадры
            if not res['properties']['fanart_image'] and menu.find('/film/' + id + '/stills/') != -1:
                response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/stills/', headers=self.headers,
                                           timeout=self.timeout)
                if not response.error:
                    html = response.body.decode('windows-1251')
                    fanart = re.compile(
                        '<a href="/picture/([0-9]+)/"><img  src="[^<]+</a>[^<]+<b><i>([0-9]+)&times;([0-9]+)</i>',
                        re.U).findall(html)
                    if fanart:
                        fanart.sort(cmp=lambda (id1, size1, t1), (id2, size2, t2): cmp(int(size1), int(size2)))

                        # пробуем взять максимально подходящее
                        fanart_best = [x for x in fanart if int(x[1]) <= 1280 and int(x[1]) > int(x[2])]
                        if fanart_best:
                            fanart = fanart_best

                        response = self.http.fetch('http://www.kinopoisk.ru/picture/' + fanart[-1][0] + '/',
                                                   headers=self.headers, timeout=self.timeout)
                        if not response.error:
                            html = response.body.decode('windows-1251')
                            r = re.compile('id="image" src="([^"]+)"', re.U | re.S).search(html)
                            if r:
                                res['properties']['fanart_image'] = r.group(1).strip()


            # студии
            if menu.find('/film/' + id + '/studio/') != -1:
                response = self.http.fetch('http://www.kinopoisk.ru/film/' + id + '/studio/', headers=self.headers,
                                           timeout=self.timeout)
                if not response.error:
                    html = response.body.decode('windows-1251')
                    r = re.compile(u'<b>Производство:</b>(.+?)</table>', re.U | re.S).search(html)
                    if r:
                        studio = []
                        for r in re.compile('<a href="/lists/m_act%5Bstudio%5D/[0-9]+/" class="all">(.+?)</a>',
                                            re.U).findall(r.group(1)):
                            r = self.html.string(r)
                            if r:
                                studio.append(r)
                        if studio:
                            res['info']['studio'] = u', '.join(studio)

        timeout = True
        # если фильм свежий, то кладем в кэш НЕ на долго (могут быть обновления на сайте)
        if 'year' not in res['info'] or not res['properties']['fanart_image'] \
                or int(res['info']['year']) > time.gmtime(time.time()).tm_year:
            timeout = 7 * 24 * 60 * 60 * 4  # 4 week

        return timeout, res
