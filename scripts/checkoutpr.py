#!/usr/bin/env python3

"""
Automate “checkout-fix-push” on an external PR.

Example:
    # set things up
    ./checkoutpr.py mcourteaux main

    # ...edit, commit..

    # push
    ./checkoutpr.py mcourteaux main --push

    # clean up remote when you're finished
    ./checkoutpr.py mcourteaux main --cleanup
"""

import argparse
import subprocess
import sys
import re
from pathlib import Path


# def sh(*cmd: str, **kw):
#     """Run command, bubble up errors with nice context."""
#     try:
#         print(f"[checkoutpr] ➕ Running command:\n  {' '.join(cmd)}")
#         return subprocess.run(cmd, check=True, text=True, capture_output=True, **kw).stdout.strip()
#     except subprocess.CalledProcessError as e:
#         print(f"\n[checkoutpr] ❌ Command failed:\n  {' '.join(cmd)}")
#         sys.exit(e.returncode)

def sh(*cmd: str, **kw):
    """Run a command, echo all its output, return stdout, exit on error."""
    print(f"[checkoutpr] ➕ Running command:\n  {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,  # keep output for returning
            check=True,           # raises on non-zero exit
            **kw
        )
        # Echo everything we captured
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Make sure any captured output is shown before exiting
        if e.stdout:
            sys.stdout.write(e.stdout)
        if e.stderr:
            sys.stderr.write(e.stderr)
        print(f"\n[checkoutpr] ❌ Command failed:\n  {' '.join(cmd)}")
        sys.exit(e.returncode)


def infer_repo_name() -> str:
    try:
        url = sh("git", "remote", "get-url", "origin")
        # Match owner/repo.git from various formats
        match = re.search(r'[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(\.git)?$', url)
        if not match:
            raise ValueError(f"Cannot extract repo name from: {url}")
        return match.group("repo")
    except Exception as e:
        sys.exit(f"[checkoutpr] ❌ Failed to determine current repo name: {e}")


def remote_url(user: str) -> str:
    return f"git@github.com:{user}/{REPO}.git"


def ensure_remote(user: str, repo: str):
    remotes = sh("git", "remote").splitlines()
    if user not in remotes:
        print(f"[checkoutpr] ➕ Adding remote '{user}'")
        sh("git", "remote", "add", user, f"git@github.com:{user}/{repo}.git")
    else:
        print(f"[checkoutpr] ✓ Remote '{user}' already exists")


# def setup_branch(user: str, branch: str, local_branch: str):
#     """Create a local branch that tracks user/branch."""
#     # 1. Fetch (no refspec yet, just make sure we have up-to-date refs)
#     print(f"[checkoutpr] ⬇️  fetching {user}/{branch}")
#     sh("git", "fetch", user, branch)

#     # 2. Create + switch to local branch that tracks the remote branch.
#     #    If it already exists locally, just switch to it.
#     existing = subprocess.check_output(["git", "branch", "--list", local_branch]).decode().strip()
#     if existing:
#         print(f"[checkoutpr] ↪️  switching to existing local branch '{local_branch}'")
#         sh("git", "switch", local_branch)
#     else:
#         print(f"[checkoutpr] 🌱 creating local branch '{local_branch}' tracking {user}/{branch}")
#         sh("git", "switch", "-c", local_branch, "--track", f"{user}/{branch}")


def setup_branch(user: str, branch: str, local_branch: str):
    """Fetch and checkout a local branch from a contributor's remote branch."""
    print(f"[checkoutpr] ⬇️  fetching {user}/{branch} into {local_branch}")
    sh("git", "fetch", user, f"{branch}:{local_branch}")

    print(f"[checkoutpr] ↪️  checking out '{local_branch}'")
    sh("git", "checkout", local_branch)


def push_to_remote(user: str, branch: str):
    print(f"[checkoutpr] 🚀 pushing HEAD to {user}/{branch}")
    sh("git", "push", user, f"HEAD:{branch}")


# def cleanup_remote(user: str, local_branch: str):
#     """Delete the temporary remote."""
#     print(f"[checkoutpr] 🧹 removing branch '{user}'")
#     sh("git", "branch", "-d", local_branch)
#     print(f"[checkoutpr] 🧹 removing remote '{user}'")
#     sh("git", "remote", "remove", user)

def cleanup_remote(user: str, local_branch: str):
    """
    Delete the temporary local branch and remote.

    • If HEAD is on `local_branch`, switch to main/master first.
    • Falls back gracefully if the repo uses “master” instead of “main”.
    """
    # What branch are we on?
    head_branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD")

    if head_branch == local_branch:
        print(f"[checkoutpr] 🏃 Switching off '{local_branch}' before deletion")
        for fallback in ("main", "master"):
            # Does this fallback branch exist?
            exists = sh("git", "branch", "--list", fallback)
            if exists:
                sh("git", "checkout", fallback)
                break
        else:
            sys.exit(
                "[checkoutpr] ❌ Neither 'main' nor 'master' exists – "
                "please checkout another branch manually before cleanup."
            )

    print(f"[checkoutpr] 🧹 removing branch '{local_branch}'")
    sh("git", "branch", "-D", local_branch)

    print(f"[checkoutpr] 🧹 removing remote '{user}'")
    sh("git", "remote", "remove", user)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check out a contributor's PR branch for local edits"
    )
    parser.add_argument("user", help="GitHub username of contributor (remote name)")
    parser.add_argument("branch", help="Branch name on contributor's fork (usually the PR branch)")
    parser.add_argument("--local", help="Optional local branch name (default: <user>-<branch>)")
    parser.add_argument("--push", action="store_true", help="Push local HEAD to the contributor's branch")
    parser.add_argument("--cleanup", action="store_true", help="Remove the remote after use")
    args = parser.parse_args()

    # Guard: ensure we’re inside a git repo
    if not (Path(".") / ".git").exists():
        sys.exit("[checkoutpr] ❌ Not inside a Git repository")

    repo = infer_repo_name()
    local_branch = args.local or f"{args.user}-{args.branch}"

    if args.push and args.cleanup:
        sys.exit("[checkoutpr] ❌ Please specify only one action at once")

    if args.push:
        push_to_remote(args.user, args.branch)

    elif args.cleanup:
        cleanup_remote(args.user, local_branch)
        print("[checkoutpr] ✨ Remote removed (tracking info stays in this branch).")

    else:
        ensure_remote(args.user, repo)
        setup_branch(args.user, args.branch, local_branch)

        print(
            f"\n[checkoutpr] ✅ All set!\n"
            f"  • You are now on '{local_branch}', tracking '{args.user}/{args.branch}'.\n"
            f"  • Make your edits, commit, then simply run:  git push\n"
            f"    (Git will push to {args.user}/{args.branch} automatically.)\n"
        )


if __name__ == "__main__":
    main()
