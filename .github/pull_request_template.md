## What this changes

<!-- One or two sentences. If it fixes an issue, "Fixes #123". -->

## Why

<!-- For parsing changes especially: what was wrong before, not just what moved. -->

## How it was verified

- [ ] `make tests` passes locally
- [ ] For packaging changes: `dpkg-buildpackage -us -uc -b` and `lintian` are clean
- [ ] For parsing changes: a test in `tests/unit` or `tests/smoke` covers it
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`, if user-visible

<!-- Please do not mix reformatting with functional changes; see CONTRIBUTING.md. -->
