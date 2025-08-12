#!/usr/bin/env python3
"""
Automate bumping a Vcpkg port to a new version.

Usage:
    ./bump_vcpkg.py cpptrace 1.0.1

Steps:
- Create a new branch (e.g. jr/cpptrace-1.0.1)
- Update ports/<name>/vcpkg.json version
- Update ports/<name>/portfile.cmake SHA512 (auto-fetched)
- Clean installed state and rebuild the port
- Run `x-add-version` to regenerate the version DB
- Commit & push both changes
- Open a GitHub PR with standard title
"""

import argparse
import hashlib
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import json
import textwrap
from typing import Optional


def run(cmd: list[str] | str, *, check=True, shell=False):
    printable = cmd if isinstance(cmd, str) else " ".join(map(shlex.quote, cmd))
    print(f"[exec] {printable}")
    subprocess.run(cmd, shell=isinstance(cmd, str) or shell, check=check)


def fetch_tarball_sha512(url: str) -> str:
    import urllib.request
    print(f"[info] downloading {url}")
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    return hashlib.sha512(data).hexdigest()


def update_vcpkg_json(path: pathlib.Path, new_version: str):
    # content = path.read_text(encoding="utf-8")
    # updated = re.sub(r'("version"\s*:\s*")\d+\.\d+\.\d+(-[\w\d.]*)?("?)', fr'\1"{new_version}"\3', content)
    # path.write_text(updated, encoding="utf-8")
    # print(f"[edit] updated version in {path.relative_to(pathlib.Path.cwd())}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    old_version = data.get("version", "")
    data["version"] = new_version
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")  # match vcpkg's style
    print(f"[edit] updated version {old_version} → {new_version} in {path}")


def update_portfile_sha512(path: pathlib.Path, new_sha: str):
    content = path.read_text(encoding="utf-8")
    updated = re.sub(r'(SHA512)\s+[0-9a-fA-F]{128}', fr'\1 {new_sha}', content)
    path.write_text(updated, encoding="utf-8")
    print(f"[edit] updated SHA512 in {path}")


PR_TEMPLATE = textwrap.dedent(
    """\
    - [x] Changes comply with the [maintainer guide](https://github.com/microsoft/vcpkg-docs/blob/main/vcpkg/contributing/maintainer-guide.md).
    - [x] SHA512s are updated for each updated download.
    - [x] The "supports" clause reflects platforms that may be fixed by this new version.
    - [x] Any fixed [CI baseline](https://github.com/microsoft/vcpkg/blob/master/scripts/ci.baseline.txt) entries are removed from that file.
    - [x] Any patches that are no longer applied are deleted from the port's directory.
    - [x] The version database is fixed by rerunning `./vcpkg x-add-version --all` and committing the result.
    - [x] Only one version is added to each modified port's versions file.
    """
)


def main():
    p = argparse.ArgumentParser(description="Automate Vcpkg port version bumps.")
    p.add_argument("name")
    p.add_argument("version")
    p.add_argument("--prefix", default="jr", help="branch prefix (default: jr)")
    p.add_argument("--branch", help="explicit branch name")
    p.add_argument("--push-remote", default="origin")
    p.add_argument("--rebase-remote", default="upstream")
    args = p.parse_args()

    name = args.name
    version = args.version
    branch = args.branch or f"{args.prefix}/{name}-{version}"

    vcpkg_dir = pathlib.Path("ports") / name
    portfile = vcpkg_dir / "portfile.cmake"
    vcpkg_json = vcpkg_dir / "vcpkg.json"

    # Git setup
    run(["git", "checkout", "master"])
    run(["git", "fetch", args.rebase_remote])
    run(["git", "rebase", f"{args.rebase_remote}/master"])
    run(["git", "push"])
    run(["git", "checkout", "-b", branch])

    # Parse repo URL from portfile
    m = re.search(r'REPO\s+([\w\-/]+)', portfile.read_text())
    if not m:
        sys.exit("[error] Could not find REPO line in portfile.cmake")
    repo = m.group(1)
    url = f"https://github.com/{repo}/archive/refs/tags/v{version}.tar.gz"

    # Calculate new SHA512
    sha512 = fetch_tarball_sha512(url)

    # Make edits
    update_vcpkg_json(vcpkg_json, version)
    update_portfile_sha512(portfile, sha512)

    # Commit port update
    run(["git", "commit", "-am", f"[{name}] Bump to {version}"])

    # Rebuild and x-add-version
    run("rm -rf installed packages downloads", shell=True)
    run(["./vcpkg", "install", name])
    run(["./vcpkg", "x-add-version", name, "--overwrite-version"])
    run(["git", "commit", "-am", "x-add"])

    # Push
    run(["git", "push", "-u", args.push_remote, branch])

    # PR
    if shutil.which("gh"):
        title = f"[{name}] Bump to {version}"
        tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        tmp.write(PR_TEMPLATE)
        tmp.close()
        run(["gh", "pr", "create", "--fill", "--body-file", tmp.name, "--title", title])
        os.unlink(tmp.name)
    else:
        print("[warn] GitHub CLI not found – open a PR manually for branch", branch)


if __name__ == "__main__":
    main()
