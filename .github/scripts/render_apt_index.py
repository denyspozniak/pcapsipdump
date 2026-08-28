#!/usr/bin/env python3
"""Render the landing page for the APT repository published to GitHub Pages.

Reads the generated dists/*/main/binary-amd64/Packages files so the page always
lists exactly what the repository actually serves.
"""

import argparse
import html
import pathlib
import sys

SUITE_LABEL = {
    "bookworm": "Debian 12",
    "trixie": "Debian 13",
    "jammy": "Ubuntu 22.04 LTS",
    "noble": "Ubuntu 24.04 LTS",
}


def read_packages(path: pathlib.Path):
    """Yield (package, version) for each stanza in a Packages file."""
    name = version = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("Package:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("Version:"):
            version = line.split(":", 1)[1].strip()
        elif not line.strip():
            if name and version:
                yield name, version
            name = version = None
    if name and version:
        yield name, version


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-dir", required=True)
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--signed", choices=["yes", "no"], default="no")
    args = ap.parse_args()

    root = pathlib.Path(args.repo_dir)
    base = args.base_url.rstrip("/")
    signed = args.signed == "yes"

    suites = sorted(p.name for p in (root / "dists").iterdir() if p.is_dir())
    if not suites:
        print("no suites found", file=sys.stderr)
        return 1

    opts = "" if signed else "[trusted=yes] "
    key_step = ""
    if signed:
        key_step = f"""
<h3>1. Import the signing key</h3>
<pre><code>curl -fsSL {base}/pcapsipdump.asc \\
  | sudo tee /etc/apt/keyrings/pcapsipdump.asc &gt; /dev/null</code></pre>
"""

    rows = []
    for suite in suites:
        packages = root / "dists" / suite / "main" / "binary-amd64" / "Packages"
        versions = ", ".join(sorted({v for _, v in read_packages(packages)})) or "—"
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(suite)}</code></td>"
            f"<td>{html.escape(SUITE_LABEL.get(suite, suite))}</td>"
            f"<td><code>{html.escape(versions)}</code></td>"
            "</tr>"
        )

    warning = "" if signed else """
<div class="warn">
  <strong>This repository is not signed.</strong>
  The <code>[trusted=yes]</code> option below tells apt to skip signature
  verification, so you are trusting GitHub Pages and your network path to
  deliver the right bytes. Use it at your own risk. If you would rather verify
  what you install, download the <code>.deb</code> from the
  <a href="https://github.com/denyspozniak/pcapsipdump/releases">releases page</a>
  and check it against <code>SHA256SUMS</code>.
</div>
"""

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>pcapsipdump APT repository</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    font: 16px/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
    max-width: 46rem; margin: 3rem auto; padding: 0 1.25rem;
  }}
  h1 {{ margin-bottom: .25rem; }}
  .sub {{ opacity: .7; margin-top: 0; }}
  pre {{
    background: rgba(127,127,127,.12); padding: .9rem 1rem;
    border-radius: .5rem; overflow-x: auto;
  }}
  code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ text-align: left; padding: .45rem .6rem; border-bottom: 1px solid rgba(127,127,127,.25); }}
  .warn {{
    border-left: 4px solid #d97706; background: rgba(217,119,6,.1);
    padding: .8rem 1rem; border-radius: .35rem; margin: 1.5rem 0;
  }}
  footer {{ margin-top: 3rem; font-size: .875rem; opacity: .7; }}
</style>
</head>
<body>

<h1>pcapsipdump</h1>
<p class="sub">APT repository — one <code>.pcap</code> file per SIP call.</p>

<p>Packages are built by GitHub Actions from
<a href="https://github.com/denyspozniak/pcapsipdump">denyspozniak/pcapsipdump</a>
and rebuilt into this repository on every release.</p>

<table>
  <thead><tr><th>Suite</th><th>Distribution</th><th>Version</th></tr></thead>
  <tbody>
    {"".join(rows)}
  </tbody>
</table>
{warning}
<h2>Install</h2>
{key_step}
<h3>{"2" if signed else "1"}. Add the repository</h3>
<p>Replace <code>$(lsb_release -cs)</code> with one of the suites above if your
system reports a codename that is not listed.</p>
<pre><code>echo "deb {opts}{base} $(lsb_release -cs) main" \\
  | sudo tee /etc/apt/sources.list.d/pcapsipdump.list</code></pre>

<h3>{"3" if signed else "2"}. Install</h3>
<pre><code>sudo apt update
sudo apt install pcapsipdump</code></pre>

<h2>Configure</h2>
<p>The daemon ships disabled on purpose — set the interface first:</p>
<pre><code>sudo editor /etc/default/pcapsipdump
sudo systemctl enable --now pcapsipdump</code></pre>

<h2>Remove the repository</h2>
<pre><code>sudo rm /etc/apt/sources.list.d/pcapsipdump.list
sudo apt update</code></pre>

<footer>
  GPL-2.0-or-later. Originally by the pcapsipdump team on SourceForge
  (<code>aexaey</code>, <code>andy0x</code>, <code>nording</code>).
  This fork is maintained with AI assistance; see the repository README.
</footer>

</body>
</html>
"""

    (root / "index.html").write_text(page, encoding="utf-8")
    # Keep Pages from running the output through Jekyll, which would drop the
    # dists/ and pool/ directories.
    (root / ".nojekyll").write_text("", encoding="utf-8")
    print(f"wrote index.html for suites: {', '.join(suites)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
