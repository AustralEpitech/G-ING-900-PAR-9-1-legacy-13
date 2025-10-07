#!/bin/bash -e
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ -z "$(docker image ls -q geneweb)" ]; then
    if ! [ -d geneweb/.git/ ]; then
        git submodule update --init geneweb/
    fi

    cd geneweb/
    docker build -t geneweb -f docker/Dockerfile .
fi

docker run --rm --user root \
    --network host \
    geneweb
