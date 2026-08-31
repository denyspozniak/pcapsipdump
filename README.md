# pcapsipdump

[![ci](https://github.com/denyspozniak/pcapsipdump/actions/workflows/ci.yml/badge.svg)](https://github.com/denyspozniak/pcapsipdump/actions/workflows/ci.yml)
[![release](https://img.shields.io/github/v/release/denyspozniak/pcapsipdump?sort=semver)](https://github.com/denyspozniak/pcapsipdump/releases)
[![license](https://img.shields.io/badge/license-GPL--2.0--or--later-blue)](LICENSE)
![stand with ukraine](https://img.shields.io/badge/%F0%9F%87%BA%F0%9F%87%A6-Stand%20with%20Ukraine-005bbb)

**One `.pcap` file per SIP call.** `pcapsipdump` is a libpcap sniffer that
records SIP signalling together with the RTP/RTCP media that belongs to it, in
exactly the format `tcpdump -w` produces — but instead of one giant capture it
writes a separate, self-describing file for every call, even with thousands of
concurrent sessions.

That is the whole point of it. When a customer reports "the call I made at
14:32 to +49… had one-way audio", you open one small file in Wireshark instead
of filtering four gigabytes of mixed traffic.

```console
$ pcapsipdump -i eth0 -d '/var/spool/pcapsipdump/%Y%m%d/%H/%Y%m%d-%H%M%S-%f-%t-%i.pcap'
$ ls /var/spool/pcapsipdump/20260828/14/
20260828-143201-1001-4930123456-a7f3c1d5@pbx.example.net.pcap
20260828-143247-1002-4930987654-b81e0f22@pbx.example.net.pcap
```

It also works offline, which is how most people meet it — splitting a bulk
capture somebody handed you:

```console
$ pcapsipdump -r bulk.pcap -d /tmp/calls
```

---

## Table of contents

- [Why this fork exists](#why-this-fork-exists)
- [Install](#install)
  - [From the APT repository](#from-the-apt-repository)
  - [From a release download](#from-a-release-download)
- [Build from source](#build-from-source)
- [Running as a service](#running-as-a-service)
- [Usage](#usage)
- [File name templates](#file-name-templates)
- [Triggers](#triggers)
- [Docker](#docker)
- [Tests](#tests)
- [Releases](#releases)
- [Documentation](#documentation)
- [Credits](#credits)
- [Maintenance and AI assistance](#maintenance-and-ai-assistance)
- [License](#license)

---

## Why this fork exists

The original project lives on SourceForge and stopped receiving commits on
**2020-03-03 at SVN r157**. The code still works and is still the cleanest tool
for this specific job, but nothing around it aged well: SysV init scripts,
`debhelper` compat level 5, `cdbs`, a spec file from the CentOS 5 era, and no
CI at all. Several GitHub forks exist; most either reformat the whole tree or
diverge onto Windows.

This fork keeps the upstream code and rebuilds everything around it:

| | Upstream r157 (2020) | This fork |
| --- | --- | --- |
| Service management | SysV init | systemd units (+ retention timer) |
| Debian packaging | `cdbs`, debhelper 5 | `dh` sequencer, debhelper-compat 13, `hardening=+all` |
| Builds | manual `make` | GitHub Actions on Debian 12/13, Ubuntu 22.04/24.04, gcc + clang |
| Packages | built by hand | `.deb` attached to every tagged release, with `SHA256SUMS` |
| Tests | unit tests failing, benchmark not compiling | unit + end-to-end smoke + benchmark, all green in CI |

Lineage, so nothing is hidden:

```
SourceForge SVN r157 (2020-03-03, final upstream revision)
  └── github.com/jchavanton/pcapsipdump  v1.1.1 (2025) — pcap_dump_flush() on
      │   BYE and on cleanup, per-call packet counters, better logging
      └── github.com/denyspozniak/pcapsipdump (this repo) — packaging, CI,
          release automation, test-suite repairs
```

## Install

### From the APT repository

Every release is republished as an APT repository on GitHub Pages, so upgrades
arrive through `apt upgrade` like any other package:

```bash
echo "deb [trusted=yes] https://denyspozniak.github.io/pcapsipdump $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/pcapsipdump.list
sudo apt update
sudo apt install pcapsipdump
```

> [!WARNING]
> **The repository is not GPG-signed.** `[trusted=yes]` tells apt to skip
> signature verification entirely, so you are trusting GitHub Pages and your
> network path to hand you the right bytes — use it at your own risk. If that
> is not acceptable, use the release downloads below and verify them against
> `SHA256SUMS`.
>
> Signing is wired up already: set the `APT_GPG_PRIVATE_KEY` and
> `APT_GPG_PASSPHRASE` repository secrets and the next run signs `Release`,
> publishes `pcapsipdump.asc`, and the `[trusted=yes]` option can be dropped.

Suites: `bookworm` (Debian 12), `trixie` (Debian 13), `jammy` (Ubuntu 22.04),
`noble` (Ubuntu 24.04). Landing page:
[denyspozniak.github.io/pcapsipdump](https://denyspozniak.github.io/pcapsipdump).

To undo:

```bash
sudo rm /etc/apt/sources.list.d/pcapsipdump.list && sudo apt update
```

### From a release download

Grab a package from the [latest release](https://github.com/denyspozniak/pcapsipdump/releases/latest):

```bash
# pick the file matching your distribution
sudo apt install ./pcapsipdump_1.2.0.ubuntu2404_amd64.deb
```

| File | Target |
| --- | --- |
| `pcapsipdump_<ver>.debian12_amd64.deb` | Debian 12 (bookworm) |
| `pcapsipdump_<ver>.debian13_amd64.deb` | Debian 13 (trixie) |
| `pcapsipdump_<ver>.ubuntu2204_amd64.deb` | Ubuntu 22.04 LTS |
| `pcapsipdump_<ver>.ubuntu2404_amd64.deb` | Ubuntu 24.04 LTS |

The package version inside each file is `<ver>~<dist>`; GitHub rewrites the `~`
to a `.` in the asset name.

Every release also carries a source tarball and a `SHA256SUMS` file:

```bash
sha256sum -c SHA256SUMS
```

RPM users: `redhat/pcapsipdump.spec` is kept up to date and should build with
`rpmbuild -bb`, but it is **not** exercised by CI — treat it as community
support rather than a shipped artifact.

## Build from source

```bash
sudo apt install build-essential libpcap-dev   # Debian/Ubuntu
make
sudo make install
```

Optional dependencies picked up automatically when present:

- `libbsd-dev` — uses `strlcpy`/`strlcat` from `bsd/string.h` instead of the
  bundled fallbacks.

Useful knobs:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CXX` | `g++` | compiler; `clang++` is tested in CI |
| `DESTDIR` | — | staging root for packaging |
| `PREFIX` | `/usr` | install prefix |
| `SPOOLDIR` | `/var/spool/pcapsipdump` | capture directory created by `make install` |
| `DEFS` | — | extra `-D` flags, e.g. `-DUSE_CALLTABLE_CACHE` |

FreeBSD and other BSDs: use `make -f BSDmakefile`.
Solaris: see [`README.solaris`](README.solaris).

## Running as a service

The package installs three systemd units:

| Unit | Enabled on install | What it does |
| --- | --- | --- |
| `pcapsipdump.service` | no | the capture daemon |
| `pcapsipdump-cleanup.timer` | yes | runs the cleanup daily |
| `pcapsipdump-cleanup.service` | (timer-driven) | deletes captures older than `RETENTION` days |

The daemon ships **disabled on purpose** — capturing everything on the wrong
interface is rarely what you want. Configure it first:

```bash
sudo editor /etc/default/pcapsipdump     # /etc/sysconfig/pcapsipdump on RHEL-likes
sudo systemctl enable --now pcapsipdump
```

```ini
DEVICE=eth0
SPOOLDIR=/var/spool/pcapsipdump
RETENTION=7
OTHER_OPTS=-U -B 64MiB -R rtp+rtcp
```

The unit runs with `CAP_NET_RAW`/`CAP_NET_ADMIN` only, plus
`NoNewPrivileges`, `ProtectSystem=full`, `ProtectHome`, a syscall filter and a
restricted address-family set — everything else is dropped.

## Usage

```
pcapsipdump [-fpUhV] [-i interface | -r file] [-d output_directory] [-P pid_file]
            [-v level] [-R filter] [-m filter] [-n filter] [-l filter]
            [-B size] [-T limit] [-t trigger:action:param] [expression]
```

Full reference: `man 8 pcapsipdump`, or `pcapsipdump -h`.

| Option | Meaning |
| --- | --- |
| `-h`, `-V` | usage / version, then exit 0 |
| `-i <iface>` | capture from an interface (`any` works) |
| `-r <file>` | read a `.pcap` file instead — offline splitting |
| `-d <template>` | output directory or file-name template (see below) |
| `-f` | stay in the foreground (what the systemd unit uses) |
| `-P <file>` | PID file when forking; default `/var/run/pcapsipdump.pid` |
| `-p` | do **not** put the interface into promiscuous mode |
| `-U` | packet-buffered writes: slower, but a half-written file is always readable |
| `-v <level>` | verbosity; higher is noisier |
| `-B <size>` | kernel capture buffer, e.g. `-B 64MiB`. Raise it to stop drops under load |
| `-R <filter>` | what to record besides SIP: `rtp+rtcp` (default), `rtp`, `rtpevent`, `t38`, `none` |
| `-m <regex>` | which SIP methods open a new file; default `^(INVITE\|OPTIONS\|REGISTER)$` |
| `-n <regex>` | only record calls to/from numbers matching the expression |
| `-l <N>` | sample: record only every N-th call |
| `-T <seconds>` | force-close a call still active after this long — useful against peers that keep sending RTP forever |
| `-t <trigger>` | run something when a file is opened or closed (see below) |
| *trailing args* | a [`pcap-filter(7)`](https://man7.org/linux/man-pages/man7/pcap-filter.7.html) expression, applied to signalling **and** media |

## File name templates

`-d` accepts a `strftime(3)` template plus three extras, so captures can be
sorted into directories as they are written:

| Code | Expands to |
| --- | --- |
| `%f` | caller (from) |
| `%t` | callee (to) |
| `%i` | Call-ID |
| `%Y %m %d %H %M %S …` | call start time, via `strftime(3)` |

```bash
pcapsipdump -i eth0 \
  -d '/var/spool/pcapsipdump/%Y%m%d/%H/%Y%m%d-%H%M%S-%f-%t-%i.pcap'
```

## Triggers

`-t <when>:<action>:<parameter>` hooks into the capture lifecycle. `when` is
`open` or `close`; the parameter goes through the same `%`-expansion as `-d`.

| Action | Effect |
| --- | --- |
| `mv:<dir>` | move the finished file elsewhere with `/bin/mv` |
| `exec:"/bin/prog args"` | fork and exec a program |
| `sh:"shell code"` | fork and run `/bin/sh -c` |

```bash
# hand every finished call to a post-processing script
pcapsipdump -i eth0 -d /var/spool/pcapsipdump \
  -t 'close:exec:/usr/local/bin/archive-call.sh %i'
```

## Docker

The image is a two-stage build of the working tree — it compiles what is
checked out, it does not fetch anything:

```bash
./docker/build.sh                                     # or:
docker build -f docker/Dockerfile -t pcapsipdump .

DEVICE=eth0 SPOOL=/srv/captures ./docker/run.sh       # or:
docker run --rm --net=host --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v "$PWD/captures:/var/spool/pcapsipdump" \
  pcapsipdump -f -i eth0 -d /var/spool/pcapsipdump
```

Splitting a file you already have needs no privileges at all:

```bash
docker run --rm -v "$PWD:/data" pcapsipdump -r /data/bulk.pcap -d /data/calls
```

## Tests

```bash
make tests
```

| Suite | What it covers |
| --- | --- |
| `tests/unit` | `gettag()` / `sdp_get_rtpmap_event()` SIP and SDP parsing |
| `tests/smoke` | builds a synthetic two-call capture and asserts pcapsipdump splits it into two valid `.pcap` files |
| `tests/performance` | `calltable::find_ip_port_ssrc()` lookup cost as the table grows |

`tests/segfaults` is left out of the default run: it needs a
`packet-size.prepare` generator that upstream never committed.

## Releases

Versioning is semantic and driven by [`bump2version`](https://github.com/c4urself/bump2version);
`pcapsipdump.h` is the single source of truth and the release workflow refuses
to build if a tag disagrees with it.

```bash
bumpversion patch          # or minor / major — edits, commits and tags
git push --follow-tags
```

Pushing a `v*` tag runs [`release.yml`](.github/workflows/release.yml), which
builds a `.deb` for each supported distribution, install-tests each one,
generates `SHA256SUMS` and publishes a GitHub release. Publishing that release
then triggers [`apt-repo.yml`](.github/workflows/apt-repo.yml), which rebuilds
the APT repository on GitHub Pages from the assets of *every* release — so the
repository is regenerated from scratch each time and cannot drift.

For the Pages deployment to work, the repository's
*Settings → Pages → Build and deployment → Source* must be set to
**GitHub Actions**.

See [CHANGELOG.md](CHANGELOG.md).

## Documentation

| Document | What is in it |
| --- | --- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | the packet path from `pcap_next_ex()` to a per-call file, the call table, the fixed-size fields that bite, and where the performance goes |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | how to build, test and submit a change; why the core parsing code is touched conservatively |
| [`SECURITY.md`](SECURITY.md) | the threat model — this parses hostile input as root — and how to report a vulnerability |
| [`CHANGELOG.md`](CHANGELOG.md) | what changed in each release, and why |
| `man 8 pcapsipdump` | the full option reference |
| [`ChangeLog`](ChangeLog) | upstream's own history, up to r157 |

## Credits

`pcapsipdump` is not new work — it is a well-aged tool that deserved a
maintained home. Credit belongs to the people who wrote it:

- **The original SourceForge team** — `aexaey`, `andy0x` and `nording` —
  who built and maintained
  [pcapsipdump](https://sourceforge.net/projects/pcapsipdump/) from 2006 to
  2020. Everything in `*.cpp` and `*.h` is fundamentally their work.
- **[Julien Chavanton](https://github.com/jchavanton)**, whose 2025 fork this
  repository is based on, for the `pcap_dump_flush()` correctness fixes, the
  per-call packet counters and the improved logging.
- **Bjoern Boschman** and the Debian VoIP team, who wrote the original Debian
  packaging that this repository's `debian/` directory descends from.

Upstream remains readable at
[svn.code.sf.net/p/pcapsipdump/code](https://sourceforge.net/p/pcapsipdump/code/HEAD/tree/trunk/)
(final revision r157).

## Maintenance and AI assistance

This fork is maintained with heavy use of AI tooling — the packaging
modernisation, the CI and release workflows, the systemd units, the smoke-test
harness and this README were produced with an AI coding assistant
(Claude Code), then reviewed and verified by a human before merging.

What that means in practice:

- **Every change is verified, not just generated.** The build, the unit tests,
  the end-to-end smoke test and a real `.deb` install run in CI on four
  distributions before anything is tagged.
- **Core capture logic is touched conservatively.** Changes to `*.cpp` stay
  minimal and are justified in the commit message; the two so far are a
  `gettag()` fix that makes a failing upstream unit test pass, and a repair of
  the benchmark, which had not compiled against the current `calltable` API for
  years.
- **Review the diff, not the prose.** If something here looks wrong, it may
  well be — issues and pull requests are welcome.

## License

GPL-2.0-or-later, unchanged from upstream. See [LICENSE](LICENSE).

---

*Parts of this repository's documentation and tooling were generated with Claude AI — please review before relying on them in production.*
