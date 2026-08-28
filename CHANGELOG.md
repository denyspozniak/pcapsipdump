# Changelog

All notable changes to this fork are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

Upstream's own history up to SVN r157 lives in [`ChangeLog`](ChangeLog).

## [Unreleased]

### Added

- An APT repository published to GitHub Pages by `apt-repo.yml`, rebuilt from
  the `.deb` assets of every release so it can never drift out of sync with
  them. It is unsigned by default and documented as such; setting the
  `APT_GPG_PRIVATE_KEY` and `APT_GPG_PASSPHRASE` secrets switches signing on
  and publishes the public key alongside the indices.

### Fixed

- `SHA256SUMS` listed file names containing `~`, but GitHub rewrites `~` to `.`
  in release asset names, so `sha256sum -c SHA256SUMS` failed on everything a
  user actually downloaded. The rename now happens before checksumming.
- `-dbgsym` packages are no longer attached to releases: Debian emits them as
  `.deb` and Ubuntu as `.ddeb`, so the published set was lopsided.

## [1.2.0] - 2026-08-28

First release of this fork. Based on
[jchavanton/pcapsipdump](https://github.com/jchavanton/pcapsipdump) v1.1.1,
which is a clean import of upstream SVN r157 (2020-03-03, the final revision on
SourceForge).

### Added

- systemd units: `pcapsipdump.service` plus a `pcapsipdump-cleanup.timer` /
  `.service` pair that finally makes the long-documented `RETENTION` setting do
  something. The daemon unit ships disabled — capturing on the wrong interface
  is rarely what you want.
- `-h` and `-V`: the usage text was previously only reachable by omitting both
  `-i` and `-r`, and an unrecognised option was silently ignored. Unknown
  options now print usage and exit non-zero.
- `tests/smoke`: builds a synthetic two-call capture with no external
  dependencies, runs it through `pcapsipdump -r`, and asserts that two valid
  per-call `.pcap` files come out.
- GitHub Actions: `ci.yml` builds and tests on Debian 12/13 and Ubuntu
  22.04/24.04 with both gcc and clang, checks the staged install layout, and
  builds plus install-tests a `.deb` on every distribution.
- GitHub Actions: `release.yml` publishes `.deb` packages, a source tarball and
  `SHA256SUMS` for every `v*` tag, and refuses to build if the tag disagrees
  with `PCAPSIPDUMP_VERSION`.
- `CHANGELOG.md`, a rewritten `README.md`, and a `.gitignore`.

### Fixed

- `gettag()` never matched a tag at offset 0 of the buffer, because the search
  started at `ptr + 1` and unconditionally read `r[-1]`. The upstream unit test
  asserting `sdp_get_rtpmap_event("a=rtpmap:1 telephone-event/8000\r\n") == 1`
  had therefore been failing. The search now starts at `ptr` and treats the
  buffer start as a line start; the space-skipping loop is also bounded by the
  buffer end.
- `sdp_get_rtpmap_event()` accepted payload type 256, which does not fit the
  `uint8_t` return value and silently became 0. The bound is now 255.
- `tests/performance/calltable_benchmark.cpp` had not compiled for years: it
  called `calltable::add()` with three arguments instead of five, treated
  `calltable::table` (a `std::vector`) as a pointer, passed an `int*` where
  `find_ip_port_ssrc()` wants a `calltable_element**`, and had its `printf`
  arguments in the wrong order. It builds, links and runs again.
- `make install` created no directories, so a `DESTDIR` install failed unless
  the target tree already existed.

### Changed

- Debian packaging rebuilt on the `dh` sequencer with `debhelper-compat 13`,
  `Rules-Requires-Root: no` and `hardening=+all`, replacing `cdbs` and
  debhelper 5.
- `/etc/default/pcapsipdump` and `/etc/sysconfig/pcapsipdump` are now the same
  documented set of keys (`DEVICE`, `SPOOLDIR`, `RETENTION`, `OTHER_OPTS`), and
  the dead `PCAPSIDUMP_ENABLE` switch is gone.
- The RPM spec was modernised (`%autosetup`, `%make_build`, `%systemd_*`
  scriptlets, SPDX licence identifier). It is **not** built by CI.
- `docker/Dockerfile` is a two-stage build of the working tree; it previously
  cloned a hard-coded upstream URL, and `docker/run.sh` mounted a hard-coded
  home directory.

### Removed

- SysV init scripts are no longer installed. They are kept for reference under
  `contrib/sysvinit/`.
- `README.txt`, whose usage text had drifted out of date, folded into
  `README.md`.
- A `.svn/` working-copy directory that had been committed to git by accident.

[Unreleased]: https://github.com/denyspozniak/pcapsipdump/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/denyspozniak/pcapsipdump/releases/tag/v1.2.0
