#!/bin/sh
# Run a live capture. Everything is overridable from the environment:
#   DEVICE=eth0 SPOOL=/srv/captures ./docker/run.sh
set -eu

name=${NAME:-pcapsipdump}
image=${IMAGE:-${name}:latest}
container=${CONTAINER:-${name}}
device=${DEVICE:-eth0}
spool=${SPOOL:-${PWD}/captures}

mkdir -p "${spool}"
docker rm -f "${container}" >/dev/null 2>&1 || true

# --net=host is needed to see the host's interfaces; NET_RAW/NET_ADMIN are what
# libpcap needs to open one in promiscuous mode.
exec docker run -d \
    --name "${container}" \
    --net=host \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    --restart unless-stopped \
    -v "${spool}:/var/spool/pcapsipdump" \
    "${image}" \
    -f -i "${device}" -d /var/spool/pcapsipdump
