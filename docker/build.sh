#!/bin/sh
# Build the image from the repository root, whatever directory this is run from.
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
name=${NAME:-pcapsipdump}
version=$(sed -n 's/.*PCAPSIPDUMP_VERSION "\(.*\)".*/\1/p' "${root}/pcapsipdump.h")

docker build -f "${root}/docker/Dockerfile" -t "${name}:${version}" "${root}"
docker tag "${name}:${version}" "${name}:latest"

echo "built ${name}:${version} (also tagged latest)"
