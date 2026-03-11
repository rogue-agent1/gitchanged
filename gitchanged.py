#!/usr/bin/env python3
"""gitchanged - Show changed files across git repos with status summary.

Single-file, zero-dependency CLI.
"""

import sys
import argparse
import os
import subprocess


def find_repos(base, depth=3):
    repos = []
    for root, dirs, files in os.walk(base):
        d = root[len(base):].count(os.sep)
        if d >= depth: dirs.clear(); continue
        if ".git" in dirs:
            repos.append(root)
            dirs.remove(".git")
        dirs[:] = [x for x in dirs if x not in {"node_modules", "__pycache__", ".venv"}]
    return sorted(repos)


def repo_status(path):
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=path, text=True, stderr=subprocess.DEVNULL)
        return out.strip().split("\n") if out.strip() else []
    except subprocess.CalledProcessError:
        return []


def cmd_scan(args):
    repos = find_repos(args.path, args.depth)
    dirty = 0
    for repo in repos:
        changes = repo_status(repo)
        if changes:
            name = os.path.basename(repo)
            added = sum(1 for c in changes if c.startswith("A") or c.startswith("??"))
            modified = sum(1 for c in changes if c.startswith(" M") or c.startswith("M"))
            deleted = sum(1 for c in changes if c.startswith(" D") or c.startswith("D"))
            print(f"  📁 {name:25s}  +{added} ~{modified} -{deleted}  ({len(changes)} changes)")
            if args.verbose:
                for c in changes[:5]:
                    print(f"       {c}")
                if len(changes) > 5:
                    print(f"       ... and {len(changes)-5} more")
            dirty += 1
    clean = len(repos) - dirty
    print(f"\n  {dirty} dirty, {clean} clean ({len(repos)} repos)")


def cmd_unpushed(args):
    repos = find_repos(args.path, args.depth)
    for repo in repos:
        try:
            ahead = subprocess.check_output(
                ["git", "rev-list", "--count", "@{upstream}..HEAD"],
                cwd=repo, text=True, stderr=subprocess.DEVNULL
            ).strip()
            if int(ahead) > 0:
                name = os.path.basename(repo)
                print(f"  ⬆️  {name:25s}  {ahead} unpushed commits")
        except subprocess.CalledProcessError:
            pass


def main():
    p = argparse.ArgumentParser(prog="gitchanged", description="Git repo change scanner")
    p.add_argument("-p", "--path", default="."); p.add_argument("-d", "--depth", type=int, default=3)
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("scan", aliases=["s"], help="Scan for dirty repos")
    s.add_argument("-v", "--verbose", action="store_true")
    sub.add_parser("unpushed", aliases=["u"], help="Find unpushed commits")
    args = p.parse_args()
    if not args.cmd: args.cmd = "s"; args.verbose = False
    cmds = {"scan": cmd_scan, "s": cmd_scan, "unpushed": cmd_unpushed, "u": cmd_unpushed}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
