#!/usr/bin/env python3
"""Generate a tiny pcap holding two complete SIP calls over UDP.

Used by tests/smoke to check that pcapsipdump still splits a bulk capture into
one file per call. Deliberately dependency-free: no scapy, no tcpdump.
"""

import struct
import sys

PCAP_MAGIC = 0xA1B2C3D4
LINKTYPE_ETHERNET = 1

SRC_MAC = bytes.fromhex("020000000001")
DST_MAC = bytes.fromhex("020000000002")


def ip_checksum(header: bytes) -> int:
    if len(header) % 2:
        header += b"\x00"
    total = 0
    for i in range(0, len(header), 2):
        total += (header[i] << 8) | header[i + 1]
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def udp_datagram(src_ip: str, dst_ip: str, src_port: int, dst_port: int, payload: bytes) -> bytes:
    udp_len = 8 + len(payload)
    # checksum 0 means "not computed", which is legal for IPv4/UDP
    udp = struct.pack("!HHHH", src_port, dst_port, udp_len, 0) + payload

    total_len = 20 + udp_len
    src = bytes(int(o) for o in src_ip.split("."))
    dst = bytes(int(o) for o in dst_ip.split("."))
    header = struct.pack(
        "!BBHHHBBH4s4s",
        0x45,        # version 4, IHL 5
        0x00,        # DSCP/ECN
        total_len,
        0x0000,      # identification
        0x4000,      # don't fragment
        64,          # TTL
        17,          # UDP
        0,           # checksum placeholder
        src,
        dst,
    )
    header = header[:10] + struct.pack("!H", ip_checksum(header)) + header[12:]

    return DST_MAC + SRC_MAC + struct.pack("!H", 0x0800) + header + udp


def sip_call(call_id: str, caller: str, callee: str, rtp_port: int, base_ts: int):
    """Yield (timestamp, payload) tuples for one INVITE/200/ACK/BYE/200 call."""
    caller_ip, callee_ip = "192.0.2.10", "192.0.2.20"
    common = (
        f"Via: SIP/2.0/UDP {caller_ip}:5060;branch=z9hG4bK{call_id[:8]}\r\n"
        f"From: <sip:{caller}@example.net>;tag=aaa{call_id[:4]}\r\n"
        f"To: <sip:{callee}@example.net>\r\n"
        f"Call-ID: {call_id}\r\n"
        f"Contact: <sip:{caller}@{caller_ip}:5060>\r\n"
        f"Max-Forwards: 70\r\n"
    )
    sdp = (
        "v=0\r\n"
        f"o=- 1 1 IN IP4 {caller_ip}\r\n"
        "s=-\r\n"
        f"c=IN IP4 {caller_ip}\r\n"
        "t=0 0\r\n"
        f"m=audio {rtp_port} RTP/AVP 0 101\r\n"
        "a=rtpmap:0 PCMU/8000\r\n"
        "a=rtpmap:101 telephone-event/8000\r\n"
    )

    invite = (
        f"INVITE sip:{callee}@example.net SIP/2.0\r\n"
        + common
        + "CSeq: 1 INVITE\r\n"
        + "Content-Type: application/sdp\r\n"
        + f"Content-Length: {len(sdp)}\r\n\r\n"
        + sdp
    )
    ok = (
        "SIP/2.0 200 OK\r\n"
        + common
        + "CSeq: 1 INVITE\r\n"
        + "Content-Length: 0\r\n\r\n"
    )
    ack = (
        f"ACK sip:{callee}@example.net SIP/2.0\r\n"
        + common
        + "CSeq: 1 ACK\r\nContent-Length: 0\r\n\r\n"
    )
    bye = (
        f"BYE sip:{callee}@example.net SIP/2.0\r\n"
        + common
        + "CSeq: 2 BYE\r\nContent-Length: 0\r\n\r\n"
    )
    bye_ok = (
        "SIP/2.0 200 OK\r\n" + common + "CSeq: 2 BYE\r\nContent-Length: 0\r\n\r\n"
    )

    forward = (caller_ip, callee_ip, 5060, 5060)
    backward = (callee_ip, caller_ip, 5060, 5060)

    yield base_ts + 0, udp_datagram(*forward, invite.encode())
    yield base_ts + 1, udp_datagram(*backward, ok.encode())
    yield base_ts + 1, udp_datagram(*forward, ack.encode())

    # A couple of RTP packets so the RTP-following code path is exercised too.
    rtp = struct.pack("!BBHII", 0x80, 0x00, 1, 160, 0xDEADBEEF) + b"\x00" * 160
    yield base_ts + 2, udp_datagram(caller_ip, callee_ip, rtp_port, rtp_port, rtp)
    yield base_ts + 2, udp_datagram(callee_ip, caller_ip, rtp_port, rtp_port, rtp)

    yield base_ts + 3, udp_datagram(*forward, bye.encode())
    yield base_ts + 3, udp_datagram(*backward, bye_ok.encode())


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <output.pcap>", file=sys.stderr)
        return 2

    packets = []
    packets += list(sip_call("call-one-0001@example.net", "1001", "2001", 20000, 1700000000))
    packets += list(sip_call("call-two-0002@example.net", "1002", "2002", 20002, 1700000010))
    packets.sort(key=lambda p: p[0])

    with open(sys.argv[1], "wb") as fh:
        fh.write(struct.pack("<IHHiIII", PCAP_MAGIC, 2, 4, 0, 0, 65535, LINKTYPE_ETHERNET))
        for ts, data in packets:
            fh.write(struct.pack("<IIII", ts, 0, len(data), len(data)))
            fh.write(data)

    print(f"wrote {len(packets)} packets to {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
