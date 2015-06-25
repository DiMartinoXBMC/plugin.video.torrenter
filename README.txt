Plugin helps you to watch videos from p2p torrent-networks, without full predownload (uses inner python-libtorrent) or Ace Stream. It also can add, control torrents and play downloaded files with external uTorrent, Transmission, Vuze of Deluge.
Official forum thread: http://forum.kodi.tv/showthread.php?tid=214366

[B]PYTHON-LIBTORRENT[/B]:
Official library`s website is http://www.rasterbar.com/products/libtorrent/
Plugin requires python binding

--- INSTALLATION ---

1. Windows
No installation required, will be downloaded with plugin from repository as module.

2. Linux
2.1 Run at console 'sudo apt-get install python-libtorrent'
2.2 Install addon and enjoy

or you could compile it:

sudo apt-get build-dep python-libtorrent
sudo apt-get install subversion
svn co https://libtorrent.svn.sourceforge.net/svnroot/libtorrent/trunk/ lt/
cd lt/
./autotool.sh
./configure --enable-python-binding
make
sudo make install
sudo ldconfig

________________________________________________________________________________________________________

Вебсайт библиотеки http://www.rasterbar.com/products/libtorrent/
Для работы плагина нужен её билд под python

--- ИНСТАЛЯЦИЯ ---

1. Windows
Все установится автоматически из репозитория

2. Linux
2.1 Выполняем в терминале sudo apt-get install python-libtorrent
2.2 Устанавливаем аддон в XBMC и пользуемся

или компилируем:

sudo apt-get build-dep python-libtorrent
sudo apt-get install subversion
svn co https://libtorrent.svn.sourceforge.net/svnroot/libtorrent/trunk/ lt/
cd lt/
./autotool.sh
./configure --enable-python-binding
make
sudo make install
sudo ldconfig
