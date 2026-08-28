# Docker

Build from the repository root — the Dockerfile compiles the working tree, it
does not fetch anything from the network:

```bash
./docker/build.sh
# or: docker build -f docker/Dockerfile -t pcapsipdump .
```

Live capture (needs host networking and packet-capture capabilities):

```bash
DEVICE=eth0 SPOOL=/srv/captures ./docker/run.sh
docker logs -f pcapsipdump
```

Splitting a capture you already have needs no privileges:

```bash
docker run --rm -v "$PWD:/data" pcapsipdump -r /data/bulk.pcap -d /data/calls
```
