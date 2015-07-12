Plugin helps you to watch videos from p2p torrent-networks, without full predownload (uses inner python-libtorrent) or Ace Stream. It also can add, control torrents and play downloaded files with external uTorrent, Transmission, Vuze or Deluge.
Official forum thread: http://forum.kodi.tv/showthread.php?tid=214366

[B]PYTHON-LIBTORRENT[/B]:
Official library`s website is http://www.rasterbar.com/products/libtorrent/
Plugin requires python binding

--- INSTALLATION ---

1. Windows, Linux x86, OS X, Android ARM
No installation required, will be downloaded with plugin from repository as module.

2. OpenELEC
Use this build (or patch)
http://openelec.tv/forum/128-addons/75885-openelec-with-support-acestream-libtorrent

3. Linux x86_64
3.1 Run at console 'sudo apt-get install python-libtorrent'
3.2 Install addon and enjoy

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