#!/bin/sh

set -e

if [ -z "$1" ] ; then
    echo "Usage: install-tidy.sh VERSION"
    exit 1
fi

CMAKE_ARGS=""
if which apt-get ; then
  if [ "$1" = "os" ] ; then
    sudo apt-get install -y libtidy5deb1
    exit 0
  else
    sudo apt-get purge libtidy5deb1 tidy libtidy-dev
  fi
  CMAKE_ARGS="-DCMAKE_INSTALL_PREFIX=/usr"
fi

wget -O tidy.tar.gz https://github.com/htacg/tidy-html5/archive/$1.tar.gz
mkdir tidy-source
tar xvf tidy.tar.gz --strip-components=1 -C tidy-source
rm tidy.tar.gz
cd tidy-source/build/cmake/
cmake ../.. -DCMAKE_BUILD_TYPE=Release $CMAKE_ARGS
make
sudo make install
