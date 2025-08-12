#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
from pathlib import Path

EXCLUDES = [
    ".venv",
    "node_modules",
    "build*",
    "out"
]

def find_project_root(start_path):
    """Walk up from start_path until we find a .git directory."""
    path = Path(start_path).resolve()
    for parent in [path] + list(path.parents):
        if (parent / ".git").is_dir():
            return parent
    raise FileNotFoundError("Could not find .git directory in any parent folder.")

def build_rsync_command(local_path, remote_path):
    cmd = [
        "rsync",
        "-avz",
        "--checksum"
    ]
    for pattern in EXCLUDES:
        cmd.append(f"--exclude={pattern}")
    cmd.append(f"{local_path}/")  # ensure trailing slash to copy contents
    cmd.append(remote_path)
    return cmd

def remote_is_dir(remote_host, remote_dir):
    """Check if a path is a directory on the remote host."""
    check_cmd = ["ssh", remote_host, f"test -d {remote_dir}"]
    return subprocess.call(check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def run_remote_command(remote, command):
    ssh_cmd = ["ssh", remote, command]
    return subprocess.call(ssh_cmd)

def main():
    parser = argparse.ArgumentParser(description="Sync project to remote and optionally run a command.")
    parser.add_argument("remote_path", help="Remote destination in form user@host:/path/to/project or user@host:/path/")
    parser.add_argument("--run", help="Command to run on remote after sync", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
    args = parser.parse_args()

    try:
        project_root = find_project_root(os.getcwd())
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    project_name = project_root.name
    print(f"Project root: {project_root}")

    if ":" not in args.remote_path:
        print("Remote path must be in form host:/path", file=sys.stderr)
        sys.exit(1)

    remote_host, remote_dir = args.remote_path.split(":", 1)

    # Decide whether to append project name
    append_needed = False
    if remote_dir.endswith("/"):
        append_needed = True
    elif "." not in os.path.basename(remote_dir):
        append_needed = True
    elif remote_is_dir(remote_host, remote_dir):
        append_needed = True

    if append_needed:
        remote_dir = os.path.join(remote_dir, project_name)

    remote_full = f"{remote_host}:{remote_dir}"
    rsync_cmd = build_rsync_command(str(project_root), remote_full)

    if args.dry_run:
        print("Rsync command:", " ".join(rsync_cmd))
        if args.run:
            print(f"Remote run command: cd {remote_dir} && {args.run}")
        sys.exit(0)

    print("Running:", " ".join(rsync_cmd))
    result = subprocess.call(rsync_cmd)
    if result != 0:
        print("Rsync failed", file=sys.stderr)
        sys.exit(result)

    if args.run:
        print(f"Running remote command on {remote_host}: {args.run}")
        run_result = run_remote_command(remote_host, f"cd {remote_dir} && {args.run}")
        sys.exit(run_result)

if __name__ == "__main__":
    main()
