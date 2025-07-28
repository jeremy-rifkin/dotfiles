#!/usr/bin/env python3
"""
Utility script to automate version bumps for Conan Center Index-style recipes.

Typical manual workflow that this replaces:

    git checkout master
    git fetch upstream
    git rebase upstream/master
    git push
    source .venv/bin/activate
    git checkout -b jr/cpptrace-1.0.1
    cd recipes/cpptrace
    # edit conandata.yml
    conan create all/conanfile.py --version 1.0.1 --build=missing
    git commit -m "cpptrace: Bump to 1.0.1"
    git push -u origin jr/cpptrace-1.0.1
    gh pr create --fill # or open GitHub and create PR manually

This script performs all of those steps with sensible defaults while still letting
you override anything you need.  Use it from the root of your cloned
conan-center-index (or any similar) repository.

Usage
------------
    ./bump-conan.py <recipe> <new-version>
    # e.g.
    ./bump-conan.py cpptrace 1.0.1

Requirements
------------
- Python≥3.8
- **ruamel.yaml** (`pip install ruamel.yaml`) — round‑trip loader that keeps comments intact
- Optionally the GitHub CLI (`gh`) if you want automatic PR creation

"""

from __future__ import annotations

import copy
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
import textwrap
import urllib.request
import ssl
from typing import Optional

# ---------------------------------------------------------------------------
# YAML helper (round‑trip)
# ---------------------------------------------------------------------------
try:
    from ruamel.yaml import YAML
    from ruamel.yaml.scalarstring import DoubleQuotedScalarString
    from ruamel.yaml.comments import CommentedMap  # type: ignore
except ImportError:
    sys.stderr.write("[ERROR] ruamel.yaml is required (`pip install ruamel.yaml`).\n")
    raise

yaml_rt = YAML(typ="rt")  # keep comments
yaml_rt.preserve_quotes = True
yaml_rt.indent(mapping=2, sequence=4, offset=2)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd: list[str] | str, *, cwd: Optional[str] = None, check: bool = True):
    printable = cmd if isinstance(cmd, str) else " ".join(map(shlex.quote, cmd))
    print(f"[exec] {printable}")
    subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd, check=check)


def compute_sha256(url: str) -> str:
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx) as resp:
        data = resp.read()
    return hashlib.sha256(data).hexdigest()


# ────────────────────────────────────────────────────────────────────────────
# conandata.yml operations (comment‑safe)
# ────────────────────────────────────────────────────────────────────────────

def load_yaml(path_: pathlib.Path):
    with path_.open("r", encoding="utf-8") as f:
        return yaml_rt.load(f)


def save_yaml(path_: pathlib.Path, data):
    with path_.open("w", encoding="utf-8") as f:
        yaml_rt.dump(data, f)


def derive_tarball_url(data, new_version: str) -> str:
    """Return a source URL for *new_version* by cloning the first existing one.

    We swap **only** the version segment (handling an optional leading "v") and
    leave everything else – including the `.tar.gz`, `.zip`, or any other
    extension – untouched.
    """
    sources: CommentedMap = data.get("sources") or CommentedMap()
    if not sources:
        raise RuntimeError("Cannot infer repo URL – `conandata.yml` has no sources block")

    sample_url: str = next(iter(sources.values()))["url"]

    # Capture version fragment that precedes a standard archive suffix (tar.gz/zip/etc.)
    pattern = re.compile(r"(v?)(\d+\.\d+\.\d+(?:[A-Za-z0-9_-]*)?)(?=\.(?:tar\.gz|zip))")
    m = pattern.search(sample_url)
    if not m:
        # Fallback: stop at first dot that precedes the extension
        m = re.search(r"(v?)(\d+\.\d+\.\d+(?:[A-Za-z0-9_-]*)?)", sample_url)
    if not m:
        raise RuntimeError(f"Unrecognisable version pattern in URL: {sample_url}")

    prefix, suffix = sample_url[: m.start()], sample_url[m.end() :]
    leading_v = "v" if m.group(1) else ""
    return f"{prefix}{leading_v}{new_version}{suffix}"


def update_conandata(path_: pathlib.Path, version: str, url: str, sha256: str) -> bool:
    data = load_yaml(path_)
    sources: CommentedMap = data.setdefault("sources", CommentedMap())

    quoted_version = DoubleQuotedScalarString(version)
    if quoted_version in sources:
        print(f"[skip] {path_.name} already contains entry {version}")
        return False

    entry = CommentedMap({
        "url": DoubleQuotedScalarString(url),
        "sha256": sha256,
    })
    sources.insert(0, quoted_version, entry)
    save_yaml(path_, data)
    print(f"[info] Added {version} to {path_.relative_to(path_.parent.parent)} (comments preserved)")
    return True


def update_config(path_: pathlib.Path, version: str) -> bool:
    if not path_.exists():
        print(f"[warn] {path_} not found — skipping config.yml update")
        return False

    with path_.open("r", encoding="utf-8") as f:
        data = yaml_rt.load(f)

    versions: CommentedMap = data.setdefault("versions", CommentedMap())
    quoted_version = DoubleQuotedScalarString(version)

    if quoted_version in versions:
        print(f"[skip] config.yml already contains version {version}")
        return False

    if not versions:
        print(f"[warn] config.yml has no existing versions — skipping")
        return False

    # Use the first (most recent) version's value as a template
    most_recent_key = next(iter(versions))
    most_recent_val = versions[most_recent_key]
    most_recent_val = copy.deepcopy(versions[most_recent_key])

    versions.insert(0, quoted_version, most_recent_val)

    with path_.open("w", encoding="utf-8") as f:
        yaml_rt.dump(data, f)

    print(f"[info] Added {version} to config.yml (copied from {most_recent_key})")
    return True


PR_TEMPLATE = textwrap.dedent(
    """\
    ### Summary
    Changes to recipe:  **{recipe}/{version}**

    I'm the author, new release

    ---
    - [x] Read the [contributing guidelines](https://github.com/conan-io/conan-center-index/blob/master/CONTRIBUTING.md)
    - [x] Checked that this PR is not a duplicate: [list of PRs by recipe](https://github.com/conan-io/conan-center-index/discussions/24240)
    - [x] Tested locally with at least one configuration using a recent version of Conan
    """
)


def main():
    ap = argparse.ArgumentParser(description="Automate version bumps for Conan recipes (comment‑safe)")
    ap.add_argument("recipe", help="recipe directory, e.g. cpptrace")
    ap.add_argument("version", help="new semantic version, e.g. 1.0.1")
    ap.add_argument("--repo-url", help="Override base repo URL if inference fails")
    ap.add_argument("--prefix", default="jr", help="branch prefix (default: jr)")
    ap.add_argument("--branch", help="explicit branch name")
    ap.add_argument("--no-build", action="store_true", help="skip `conan create` build step")
    ap.add_argument("--no-pr", action="store_true", help="skip GitHub PR creation")
    ap.add_argument("--push-remote", default="origin", help="remote to push to (default: origin)")
    ap.add_argument("--rebase-remote", default="upstream", help="remote to rebase against (default: upstream)")
    args = ap.parse_args()

    # recipe_dir = pathlib.Path("recipes") / args.recipe
    # conandata = recipe_dir / "all" / "conandata.yml"
    # if not conandata.exists():
    #     sys.exit(f"[error] {conandata} not found – bad recipe?")

    recipe_dir = pathlib.Path("recipes") / args.recipe
    # ────────────────────────────────────────────────────────────────────
    # Figure out the sub‑folder that holds the recipe files (CCI “folder”)
    # ────────────────────────────────────────────────────────────────────
    def detect_folder() -> str:
        cfg = recipe_dir / "config.yml"
        if not cfg.exists():
            return "all"

        cfg_data = load_yaml(cfg)
        versions = cfg_data.get("versions") or {}
        if not versions:
            return "all"

        first_key = next(iter(versions))          # keep CCI’s “most‑recent‑first” order
        return versions[first_key].get("folder", "all")

    folder: str = detect_folder()
    conan_subdir = recipe_dir / folder
    conandata = conan_subdir / "conandata.yml"

    if not conandata.exists():
        sys.exit(f"[error] {conandata} not found – bad recipe or wrong folder?")

    # Figure out tarball URL
    if args.repo_url:
        tarball_url = f"{args.repo_url.rstrip('/')}/archive/refs/tags/v{args.version}.tar.gz"
    else:
        data = load_yaml(conandata)
        tarball_url = derive_tarball_url(data, args.version)

    print(f"[info] Using tarball url {tarball_url}")

    sha256 = compute_sha256(tarball_url)

    branch = args.branch or f"{args.prefix}/{args.recipe}-{args.version}"

    # Git flow
    run(["git", "checkout", "master"])
    run(["git", "fetch", args.rebase_remote])
    run(["git", "rebase", f"{args.rebase_remote}/master"])
    run(["git", "push"])
    run(["git", "checkout", "-b", branch])

    # Patch YAML
    if not update_conandata(conandata, args.version, tarball_url, sha256):
        print("[info] Nothing to commit; exiting.")
        return

    configyml = recipe_dir / "config.yml"
    update_config(configyml, args.version)

    # Optional build
    if not args.no_build:
        run(f"conan create {conan_subdir}/conanfile.py --version {args.version} --build=missing")

    # Commit & push
    commit_msg = f"{args.recipe}: Bump to {args.version}"
    run(["git", "add", str(conandata), str(configyml)])
    run(["git", "commit", "-m", commit_msg])

    run(["git", "push", "-u", args.push_remote, branch])

    # PR
    if args.no_pr:
        return
    if shutil.which("gh"):
        tmp = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        tmp.write(PR_TEMPLATE.format(recipe=args.recipe, version=args.version))
        tmp.close()
        run(["gh", "pr", "create", "--fill", "--body-file", tmp.name])
        os.unlink(tmp.name)
    else:
        print("[warn] GitHub CLI not found — open a PR manually for branch", branch)


if __name__ == "__main__":
    main()
