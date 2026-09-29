#!/usr/bin/env python3
"""
serve_zrm.py -- cache.appcache sync helper (stable mode)

OLD behaviour (the instability): "always bump the manifest at startup so the
PS4 re-downloads." A restart then forces a FULL re-download; if the console's
browser closes or the network hiccups, the cache is left BROKEN and the host
looks "unstable in cache".

NEW behaviour: the manifest is rewritten ONLY when a listed file's content
actually changed (SHA-256 compared with the hashes stored in the manifest).
Same content -> same manifest -> the cache stays stable across restarts.
Missing files are dropped (a dead entry fails the whole cache in WebKit).

Usage:
    python3 serve_zrm.py              # sync once, print the result
    python3 -c "import serve_zrm; serve_zrm.auto_bump()"

host.py runs the same sync automatically at startup.
"""

import hashlib
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "cache.appcache")


def sha256_file(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 16), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def sync_manifest(manifest_path=MANIFEST):
    """Rewrite the manifest only when a listed file really changed.

    Returns True when the manifest was rewritten, False when already in sync."""
    if not os.path.isfile(manifest_path):
        return False
    root = os.path.dirname(os.path.abspath(manifest_path))
    try:
        with open(manifest_path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return False

    section = "CACHE"
    entries = []          # [url, old_hash_or_None]
    network = []
    fallback = []
    comments = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            if not s.startswith("# build"):
                comments.append(s)
            continue
        up = s.upper()
        if up == "CACHE:" or up == "CACHE MANIFEST":
            section = "CACHE"
            continue
        if up == "NETWORK:":
            section = "NETWORK"
            continue
        if up == "FALLBACK:":
            section = "FALLBACK"
            continue
        if section == "NETWORK":
            network.append(s)
        elif section == "FALLBACK":
            fallback.append(s)
        else:
            parts = s.split(None, 1)
            url = parts[0]
            old = None
            if len(parts) > 1 and parts[1].startswith("#"):
                old = parts[1][1:].strip()
            entries.append([url, old])

    changed = False
    drops = []
    out_lines = [
        "CACHE MANIFEST",
        "# build " + time.strftime("%Y%m%d-%H%M%S"),
    ]
    for c in comments:
        out_lines.append(c)
    out_lines.append("")

    for url, old in entries:
        fname = url.split("?", 1)[0]
        h = sha256_file(os.path.join(root, fname))
        if h is None:
            drops.append(url)
            changed = True
            continue
        if h != old:
            changed = True
        out_lines.append(url + " #" + h)

    if not network:
        network = ["*"]
    if not fallback:
        fallback = [
            "index.html index.html",
            "run_lapse.html run_lapse.html",
            "run_poops.html run_poops.html",
        ]

    out_lines.append("")
    out_lines.append("NETWORK:")
    out_lines.extend(network)
    out_lines.append("")
    out_lines.append("FALLBACK:")
    out_lines.extend(fallback)

    if not changed:
        return False

    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines) + "\n")
    except OSError:
        return False
    return True


def auto_bump():
    """Compatibility wrapper: sync-based bump for the zrm/ folder."""
    return sync_manifest(MANIFEST)


if __name__ == "__main__":
    changed = auto_bump()
    print("manifest " +
          ("REWRITTEN (content changed)" if changed
           else "in sync -- cache stays stable"))
