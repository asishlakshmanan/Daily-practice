#!/usr/bin/env python3
"""
daily_commit.py — append a timestamped note to a log file, then commit and push.

Usage:
    python daily_commit.py                 # normal run
    python daily_commit.py --dry-run       # write the note, skip all git commands
    python daily_commit.py --no-push       # commit locally, skip push

Configure REPO_PATH below (or set the DAILY_COMMIT_REPO environment variable).
"""

import argparse
import os
import random
import subprocess
import sys
from datetime import datetime

# ----------------------------- CONFIG -----------------------------
# Absolute path to your local git repository.
REPO_PATH = os.environ.get(
    "DAILY_COMMIT_REPO",
    r"C:\Users\Dell\Desktop\regular updates",
)

TARGET_FILE = "daily_log.txt"   # or "notes.md"
BRANCH = "main"
REMOTE = "origin"
PULL_FIRST = True               # rebase on the remote before committing
# ------------------------------------------------------------------

NOTES = [
    "Programs must be written for people to read, and only incidentally for machines to execute.",
    "Premature optimization is the root of all evil.",
    "Simplicity is the soul of efficiency.",
    "Make it work, make it right, make it fast.",
    "Any fool can write code a computer understands; good programmers write code humans understand.",
    "The best error message is the one that never shows up.",
    "Deleted code is debugged code.",
    "Weeks of coding can save you hours of planning.",
    "First, solve the problem. Then, write the code.",
    "Code is read far more often than it is written.",
    "Reviewed a concept today and wrote down one thing I did not understand before.",
    "Refactoring note: a function that needs a comment to explain its name needs a better name.",
    "Learning note: measure before you optimise — intuition about hot paths is usually wrong.",
    "Learning note: a failing test you can reproduce is worth ten hours of guessing.",
    "Learning note: small commits make bad days recoverable.",
    "Learning note: reading someone else's code is the fastest way to find your own bad habits.",
    "Learning note: naming is hard because it forces you to actually understand the thing.",
    "Learning note: if the fix took five minutes, the next ten go into writing down why.",
    "Learning note: version control is a time machine, not a backup.",
    "Learning note: automate the task you have now done manually three times.",
]


def log(message):
    """Print a timestamped line so scheduled runs leave a readable trail."""
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}", flush=True)


def run_git(args, repo, check=True):
    """Run a git command inside the repo and return the CompletedProcess."""
    result = subprocess.run(
        ["git"] + args,
        cwd=repo,
        capture_output=True,
        text=True,
    )
    printable = "git " + " ".join(args)
    if result.returncode == 0:
        log(f"OK   {printable}")
    else:
        log(f"FAIL {printable} (exit {result.returncode})")
        if result.stderr.strip():
            log(f"     {result.stderr.strip().splitlines()[0]}")
        if check:
            sys.exit(result.returncode)
    return result


def pick_note(path):
    """Choose a random note, avoiding an exact repeat of the previous entry."""
    previous = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            lines = [line for line in handle if line.strip()]
        if lines:
            previous = lines[-1]
    choices = [n for n in NOTES if n not in previous] or NOTES
    return random.choice(choices)


def update_log_file(repo, filename):
    """Append a timestamp and a random note to the target file."""
    path = os.path.join(repo, filename)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = pick_note(path)

    is_markdown = filename.lower().endswith(".md")
    new_file = not os.path.exists(path)

    with open(path, "a", encoding="utf-8") as handle:
        if new_file and is_markdown:
            handle.write("# Daily Log\n\n")
        if is_markdown:
            handle.write(f"- **{stamp}** — {note}\n")
        else:
            handle.write(f"[{stamp}] {note}\n")

    log(f"Updated {filename}: {note}")
    return stamp


def main():
    parser = argparse.ArgumentParser(description="Make a daily git commit.")
    parser.add_argument("--dry-run", action="store_true",
                        help="write the note but run no git commands")
    parser.add_argument("--no-push", action="store_true",
                        help="commit locally but do not push")
    parser.add_argument("--repo", default=None,
                        help="override the configured repository path")
    args = parser.parse_args()

    repo = os.path.abspath(os.path.expanduser(args.repo or REPO_PATH))

    if not os.path.isdir(os.path.join(repo, ".git")):
        log(f"ERROR: {repo} is not a git repository. Set REPO_PATH and try again.")
        sys.exit(1)

    log(f"Repository: {repo}")

    if PULL_FIRST and not args.dry_run:
        # Non-fatal: a fresh repo with no upstream will fail here, and that is fine.
        run_git(["pull", "--rebase", REMOTE, BRANCH], repo, check=False)

    stamp = update_log_file(repo, TARGET_FILE)

    if args.dry_run:
        log("Dry run — skipping git add/commit/push.")
        return

    run_git(["add", "."], repo)

    status = run_git(["status", "--porcelain"], repo)
    if not status.stdout.strip():
        log("Nothing staged to commit. Exiting.")
        return

    run_git(["commit", "-m", f"daily update: {stamp}"], repo)

    if args.no_push:
        log("Committed locally — push skipped (--no-push).")
        return

    push = run_git(["push", REMOTE, BRANCH], repo, check=False)
    if push.returncode != 0:
        log("Push failed. The commit is saved locally; check your credentials "
            "or network and push manually.")
        sys.exit(push.returncode)

    log("Done.")


if __name__ == "__main__":
    main()
