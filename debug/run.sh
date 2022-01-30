docker build --build-arg=VERSION=latest -t debug-latest .
docker build --build-arg=VERSION=rolling -t debug-rolling .
docker build --build-arg=VERSION=devel -t debug-devel .


echo ***LATEST***
docker run -it --rm -v $PWD:/debug debug-latest
echo ***ROLLING***
docker run -it --rm -v $PWD:/debug debug-rolling
echo ***DEVEL***
docker run -it --rm -v $PWD:/debug debug-devel
