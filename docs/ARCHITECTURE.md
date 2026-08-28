# Architecture

How a packet gets from the wire into a per-call `.pcap` file, and which
assumptions the code makes along the way. Written against the tree as it stands
in 1.2.0; if you change one of these paths, update this document with it.

## Source layout

| File | Responsibility |
| --- | --- |
| `pcapsipdump.cpp` | option parsing, the libpcap loop, protocol dispatch, SIP handling |
| `pcapsipdump_lib.cpp` | link-layer decoding, tunnel unwrapping, `-d` template expansion, `mkdir -p` |
| `pcapsipdump_strlib.cpp` | `gettag()` header/SDP scanner and `sdp_get_rtpmap_event()` |
| `calltable.cpp` | the call table: creation, RTP-flow lookup, IP-fragment tracking, expiry |
| `trigger.cpp` | `-t open:`/`-t close:` actions (`mv`, `exec`, `sh`) |
| `pcapsipdump_endian.h` | compile-time `HTONS()` so ethertype comparisons fold into constants |

## The packet path

```
pcap_next_ex()
      │
      ├─ every 15 s of capture time ──► calltable::do_cleanup()
      │
      ▼
link layer ── ethernet_get_header_ip()      Ethernet / 802.1Q / 802.1ad /
      │                                      Q-in-Q / PPPoE, or a raw offset
      │                                      for the non-Ethernet DLTs
      ▼
skip_tunnel_ip_header()                      IPv4-in-IPv6 (DS-Lite)
      │
      ├─ IPv4 with a non-zero fragment offset ─┐
      ├─ IPv6 fragment header, next = UDP ─────┤► calltable::get_ipfrag()
      │                                         │  and dump into the file that
      │                                         │  owns this (src,dst,id) tuple
      ▼
UDP (TCP only with -DUSE_TCP)
      │
      ├─ port matches a tracked RTP flow ──► dump into that call's file
      ├─ looks like RTCP for a tracked flow ► dump into that call's file
      └─ otherwise: treat as SIP
             │
             ├─ method matches -m  ─► calltable::add()  → open a new file
             │                        parse SDP → register the RTP ip:port
             └─ Call-ID already known ─► append; on BYE, flush
```

### Link layer

`ethernet_get_header_ip()` walks the ethertype chain by index rather than by a
loop, which keeps it branch-predictable and bounded. It understands untagged
IPv4/IPv6, one or two VLAN tags (`0x8100`, `0x9100`, `0x88a8`), and PPPoE
session-stage frames (`0x8864`) including PPPoE inside a VLAN. Anything else
returns `NULL` and the packet is dropped, with a diagnostic at `-v 4`.

Non-Ethernet link types (Linux cooked `DLT_LINUX_SLL`, raw IP) skip this and use
a fixed offset computed once from `pcap_datalink()`.

### Fragmentation

Only the *first* fragment carries the UDP header, so only that one can be
classified. When a call's file is opened, the `(saddr, daddr, ip_id)` tuple is
recorded in `calltable::ipfrags`; subsequent fragments are looked up by that
tuple and dumped into the same file. The entry is dropped when a fragment
arrives with the more-fragments bit clear.

For IPv6 the same idea applies through the fragment extension header, with the
128-bit addresses folded into 32 bits by `hsaddr()`/`hdaddr()` — an ad-hoc hash,
so an IPv6 collision is possible in principle and would mis-file a fragment.

### SIP

`get_method()` reads the leading token and requires it to be all upper-case,
which cheaply rejects RTP that happens to land on the signalling port.
`gettag()` is the only header scanner: it finds a tag at the start of a line —
the buffer start or immediately after CR/LF — skips leading spaces and returns a
pointer plus a length into the original buffer. Nothing is copied and nothing is
NUL-terminated, so every caller must respect the returned length.

A packet whose method matches `-m` (default `^(INVITE|OPTIONS|REGISTER)$`)
creates a call-table entry keyed by Call-ID. The SDP body is parsed for the
media address and port, which are registered as an RTP flow for that call, and
for `a=rtpmap:<pt> telephone-event/…` so that `-R rtpevent` can pick out DTMF.

### RTP association

RTP is matched by `(address, port, SSRC)`, not by a 5-tuple, because the media
path frequently does not match what SDP advertised. Each call holds up to
`calltable_max_ip_per_call` (4) flows.

`find_ip_port_ssrc()` is a linear scan over the table, so lookup cost grows with
the number of concurrent calls — `tests/performance` measures exactly this and
it is the first thing to look at if a busy box starts dropping packets. Building
with `-DUSE_CALLTABLE_CACHE` adds `std::map` indices over `(addr,port)` and
Call-ID; the cache handles SSRC changes inside a live call and invalidates the
entry when the port is reused after a BYE.

### Expiry and file lifetime

`do_cleanup()` runs at most once per 15 s of *capture* time — not wall-clock,
so replaying a file behaves the same as live capture. An entry is closed when it
has been idle for 300 s, or when `-T` says the whole call has run too long.
Closing flushes and closes the dumper, fires the `close` trigger, and zeroes the
slot for reuse; with `-R t38` a call that never carried T.38 has its file
unlinked instead.

Slots are reused by scanning for `is_used == 0` before appending, so the vector
grows to the high-water mark of concurrent calls and stays there.

## Fixed-size fields

These are worth knowing before you feed the tool something unusual:

| Field | Size | Consequence when exceeded |
| --- | --- | --- |
| `call_id` | 32 bytes | a longer Call-ID is truncated; two calls sharing a 32-byte prefix collide |
| `caller`, `callee` | 16 bytes each | long numbers or user parts are truncated in the file name |
| `fn_pcap` | 128 bytes | limits how deep a `-d` template can nest |
| `ip[]`, `port[]`, `ssrc[]` | 4 entries | a 5th media flow in one call is not followed |

## Known portability constraint: unaligned header access

An IPv4 header starts at offset 14 of an Ethernet frame, and the code reads it
by casting that address to `struct iphdr *`. 14 is not a multiple of 4, so every
header field access is a misaligned load — UBSan reports it immediately:

```
pcapsipdump_lib.cpp:203: runtime error: member access within misaligned
address 0x... for type 'struct ipv6hdr', which requires 4 byte alignment
```

This is not one bug but the shape of the whole parser, and it is why
`analysis.yml` runs UBSan with `-fno-sanitize=alignment`: switching the check on
would bury every other finding under thousands of alignment reports.

In practice this is fine on x86-64 and on AArch64, which both permit unaligned
loads. It is *not* fine on a strict-alignment target, where these accesses would
trap or be silently fixed up by the kernel at enormous cost. Fixing it properly
means copying each header into an aligned local, or reading fields through
`memcpy`, throughout the parser — a large change to the most safety-critical
code in the tree, and not one to make casually.

## Performance notes

- `-B` sets the kernel ring buffer. The default is small; a busy box needs
  several MiB or the kernel drops packets before pcapsipdump ever sees them.
- `-U` flushes after every packet. It makes a half-written file readable at any
  moment and costs a `write(2)` per packet — fine for a few calls, not for a
  loaded SBC.
- The trailing pcap-filter expression is evaluated in the kernel and is by far
  the cheapest way to cut volume, but it applies to signalling *and* media: a
  filter that excludes the RTP ports silently produces signalling-only captures.

## Testing

| Suite | Scope |
| --- | --- |
| `tests/unit` | `gettag()` and `sdp_get_rtpmap_event()` against a real SIP/SDP body |
| `tests/smoke` | generates a two-call capture, runs the binary, asserts two valid per-call files |
| `tests/performance` | `find_ip_port_ssrc()` cost from 5 to 50 000 calls |

`tests/segfaults` is not wired into `make tests`: it needs a
`packet-size.prepare` generator that upstream never committed.
