"""Builds the mod-portal-shaped zip from git-tracked files.

The portal rejects any zip containing a file ending in exe/bat/ps1/sh/py --
it doesn't accept distributing executables, even dev-only ones like
tools/recolor.py or the test suite. Neither is loaded by data.lua, so leaving
them out changes nothing about how the mod runs; this script drops any
tracked file with one of those extensions and zips the rest under the
<name>_<version>/ folder the portal expects.

    python tools/build_release.py            # writes ../armored-belts_<version>.zip
    python tools/build_release.py -o path.zip # writes to an explicit path
"""

import argparse
import io
import json
import os
import subprocess
import sys
import zipfile

MOD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD_NAME = "armored-belts"

# Matches the mod portal's own rejection message verbatim.
BANNED_EXTENSIONS = {"exe", "bat", "ps1", "sh", "py"}


def tracked_files():
    out = subprocess.check_output(
        ["git", "ls-files"], cwd=MOD_DIR, text=True)
    return [line for line in out.splitlines() if line]


def mod_version():
    with io.open(os.path.join(MOD_DIR, "info.json"), encoding="utf-8") as f:
        return json.load(f)["version"]


def build(output_path):
    version = mod_version()
    base_name = "%s_%s" % (MOD_NAME, version)

    included, excluded = [], []
    for path in tracked_files():
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        (excluded if ext in BANNED_EXTENSIONS else included).append(path)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in included:
            zf.write(os.path.join(MOD_DIR, path),
                     "%s/%s" % (base_name, path))

    print("wrote %s (%d files)" % (output_path, len(included)))
    if excluded:
        print("excluded (banned by the mod portal -- dev tooling only):")
        for path in excluded:
            print("  - %s" % path)
    return included, excluded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", default=None,
                        help="output zip path (default: sibling of the mod folder)")
    args = parser.parse_args()

    output_path = args.output or os.path.join(
        os.path.dirname(MOD_DIR), "%s_%s.zip" % (MOD_NAME, mod_version()))

    included, excluded = build(output_path)

    leaked = [p for p in included
             if p.rsplit(".", 1)[-1].lower() in BANNED_EXTENSIONS]
    if leaked:
        print("BUG: banned extensions still made it into the zip:", leaked)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
