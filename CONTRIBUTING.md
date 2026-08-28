# Contributing

Bug reports, packaging fixes and small focused patches are all welcome.

## Before you start

Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). It describes the packet
path and, more usefully, the fixed-size fields and assumptions that make
"obvious" changes break in non-obvious ways.

## Build and test

```bash
sudo apt install build-essential libpcap-dev libbsd-dev python3
make
make tests
```

`make tests` runs the unit tests, the end-to-end smoke test and the benchmark.
All three must pass before a change is worth reviewing. CI runs the same thing
on Debian 12/13 and Ubuntu 22.04/24.04 with both gcc and clang, so a patch that
only builds on your distribution will be caught.

To reproduce a CI environment exactly:

```bash
docker run --rm -v "$PWD:/src" -w /src debian:12 sh -c \
  'apt-get update && apt-get install -y build-essential libpcap-dev python3 && make tests'
```

## What a good change looks like

**Core capture code (`*.cpp`, `*.h`) is touched conservatively.** This tool has
run in production for nearly two decades; the bar for changing how a packet is
parsed is higher than for changing packaging or CI. If you change parsing:

- Add or extend a test in `tests/unit` for pure functions, or in `tests/smoke`
  when the change is visible end to end. `tests/smoke/make_sip_pcap.py`
  generates its capture from scratch with no dependencies — extend it rather
  than committing a binary `.pcap`.
- Say in the commit message *why* the old behaviour was wrong, not just what
  you changed. "Fix parsing" tells a future reader nothing.
- Respect the fixed-size buffers. `gettag()` returns a pointer and a length into
  a buffer that is neither copied nor NUL-terminated.

**Match the surrounding style.** The tree is upstream's, warts and all: tabs and
spaces are mixed, brace placement is inconsistent. Do not reformat code you are
not otherwise changing — a whitespace-only diff buries the real change and makes
every future `git blame` useless.

## Packaging changes

Anything under `debian/` or `systemd/` should be verified by building the
package, not just by reading it:

```bash
dpkg-buildpackage -us -uc -b
lintian ../pcapsipdump_*.deb
sudo apt install ../pcapsipdump_*.deb
```

`redhat/pcapsipdump.spec` is kept current but is not built by CI. If you touch
it, say in the pull request how you tested it.

## Releases

The version lives in exactly one place, `PCAPSIPDUMP_VERSION` in
`pcapsipdump.h`, and is moved with [`bump2version`](https://github.com/c4urself/bump2version):

```bash
bumpversion patch          # or minor / major
git push --follow-tags
```

The release workflow refuses to build when a tag disagrees with the source, so
hand-written tags fail loudly rather than shipping a mislabelled package.

Update `CHANGELOG.md` under `## [Unreleased]` as part of the change that needs
it, not in a separate sweep before a release.

## Licence

By contributing you agree that your work is released under GPL-2.0-or-later,
the same terms as the rest of the project.
