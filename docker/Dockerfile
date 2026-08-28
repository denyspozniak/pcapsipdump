# Build from the repository root:
#   docker build -f docker/Dockerfile -t pcapsipdump .
FROM debian:12-slim AS build

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential libpcap-dev libbsd-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .
RUN make clean && make


FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpcap0.8 libbsd0 \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /var/spool/pcapsipdump

COPY --from=build /src/pcapsipdump /usr/sbin/pcapsipdump

VOLUME ["/var/spool/pcapsipdump"]

# Capturing live traffic needs --net=host --cap-add=NET_RAW --cap-add=NET_ADMIN.
# Splitting an existing file (-r) needs no privileges at all.
ENTRYPOINT ["/usr/sbin/pcapsipdump"]
CMD ["-h"]
