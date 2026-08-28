#!/bin/sh
# End-to-end check: feed pcapsipdump a bulk capture holding two SIP calls and
# make sure it writes one readable .pcap file per call.
set -eu

here=$(cd "$(dirname "$0")" && pwd)
pcapsipdump=${PCAPSIPDUMP:-"${here}/../../pcapsipdump"}
workdir=$(mktemp -d)
trap 'rm -rf "${workdir}"' EXIT

if [ ! -x "${pcapsipdump}" ]; then
    echo "smoke: ${pcapsipdump} not built, run make first" >&2
    exit 1
fi

python3 "${here}/make_sip_pcap.py" "${workdir}/bulk.pcap"

mkdir -p "${workdir}/out"
"${pcapsipdump}" -f -r "${workdir}/bulk.pcap" -d "${workdir}/out" -v 1

echo "--- files written:"
find "${workdir}/out" -type f | sort

count=$(find "${workdir}/out" -name '*.pcap' -type f | wc -l)
if [ "${count}" -ne 2 ]; then
    echo "smoke: expected 2 per-call captures, got ${count}" >&2
    exit 1
fi

# Every file must be a non-empty, well-formed pcap.
find "${workdir}/out" -name '*.pcap' -type f | while read -r f; do
    if [ ! -s "${f}" ]; then
        echo "smoke: ${f} is empty" >&2
        exit 1
    fi
    magic=$(od -An -tx4 -N4 "${f}" | tr -d ' \n')
    case "${magic}" in
        a1b2c3d4|d4c3b2a1|a1b23c4d|4d3cb2a1) ;;
        *) echo "smoke: ${f} is not a pcap file (magic ${magic})" >&2; exit 1 ;;
    esac
done

echo "smoke tests OK (${count} calls split)"
