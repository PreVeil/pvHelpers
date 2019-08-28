#!/bin/sh

set -e

eval $(docker-machine env)

DOCKERTAG=$(uuidgen | awk '{print tolower($0)}')
TEMPDIR="docker/$DOCKERTAG"
# LIBFIPS_CRYPTO_PATH="$1" && shift && OUT_DIR="$1" && shift && RUNARGS=$@

docker build -f docker/Dockerfile -t $DOCKERTAG . 2>&1
docker run --name $DOCKERTAG $DOCKERTAG 2>&1
docker rm -f $(docker ps -aqf ancestor=$DOCKERTAG) 2>&1 || true

mv $TEMPDIR/dist/* $OUT_DIR || true
rm -rf $TEMPDIR