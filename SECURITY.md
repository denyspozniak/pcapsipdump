# Security policy

## Threat model

pcapsipdump parses packets straight off a network it does not control, usually
while running as root with `CAP_NET_RAW`. Every byte it touches after
`pcap_next_ex()` is attacker-controlled: ethertypes, VLAN tags, IP headers,
fragment offsets, SIP headers and SDP bodies. A memory-safety bug in the parsing
path is therefore remotely reachable by anyone who can put a packet on the
monitored segment.

Known sharp edges, none of them fixed upstream:

- Parsing is hand-rolled C-style pointer arithmetic over fixed-size buffers.
- Several fields (`call_id`, `caller`, `callee`, `fn_pcap`) are fixed-size and
  truncate rather than reject.
- `gettag()` returns an uncopied, non-NUL-terminated pointer plus length; a
  caller that ignores the length reads past the packet.

Treat the shipped systemd hardening (`CAP_NET_RAW`/`CAP_NET_ADMIN` only,
`NoNewPrivileges`, `ProtectSystem=full`, seccomp filter) as mitigation, not as a
substitute for the above.

## Supported versions

Only the latest release is supported. Fixes go into a new release rather than
being backported.

| Version | Supported |
| --- | --- |
| 1.2.x | yes |
| anything from SourceForge (≤ 0.2 / r157) | no — unmaintained since 2020 |
| other GitHub forks | no |

## Reporting a vulnerability

Please report privately through
[GitHub Security Advisories](https://github.com/denyspozniak/pcapsipdump/security/advisories/new)
rather than opening a public issue.

Include what a maintainer needs to reproduce it: the affected version, and
ideally a `.pcap` that triggers the behaviour or a script in the style of
`tests/smoke/make_sip_pcap.py` that generates one.

This is a spare-time project, not a vendor with an on-call rota. Expect an
acknowledgement within a couple of weeks. If a report goes unanswered for
90 days, publish it — a silent maintainer is not a reason to leave users
exposed.

## Scope

In scope: anything reachable by feeding pcapsipdump a crafted packet or capture
file, and anything in the packaging that escalates privilege on install.

Out of scope: the fact that the published APT repository is unsigned. That is a
[documented, deliberate trade-off](README.md#install) — `[trusted=yes]` disables
signature verification and the README says so. If you want verified packages,
download the release assets and check them against `SHA256SUMS`.
