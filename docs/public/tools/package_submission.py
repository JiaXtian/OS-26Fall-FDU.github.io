#!/usr/bin/env python3
"""Export only this lab's committed changes, including merge resolutions."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile


def git(*args, check=True):
    return subprocess.run(["git", *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=check)


def resolve(ref):
    return git("rev-parse", "--verify", ref + "^{commit}").stdout.decode().strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", required=True)
    parser.add_argument("--student", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--submit", required=True)
    parser.add_argument("--framework", required=True,
                        help="Exact framework commit used at the start, not a moving branch")
    parser.add_argument("--previous", help="Previous submitted commit merged into this framework")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    root = Path(git("rev-parse", "--show-toplevel").stdout.decode().strip())
    os.chdir(root)
    if git("status", "--porcelain").stdout:
        raise ValueError("Working tree is not clean. Commit source changes; keep build outputs ignored.")
    start, submit, framework = map(resolve, (args.start, args.submit, args.framework))
    previous = resolve(args.previous) if args.previous else None
    if git("merge-base", "--is-ancestor", start, submit, check=False).returncode:
        raise ValueError("Start must be an ancestor of the submitted commit.")
    if git("merge-base", "--is-ancestor", framework, start, check=False).returncode:
        raise ValueError("Framework must be an ancestor of start.")
    auto_tree = git("rev-parse", framework + "^{tree}").stdout.decode().strip()
    if previous:
        if git("merge-base", "--is-ancestor", previous, start, check=False).returncode:
            raise ValueError("Previous submission must be an ancestor of start.")
        merged = git("merge-tree", "--write-tree", framework, previous, check=False)
        if merged.returncode not in (0, 1):
            raise ValueError("git merge-tree failed; use Git 2.38+ and the recorded commits.\n" +
                             merged.stderr.decode())
        # A conflicted automatic tree is useful: differing resolved files must be included.
        auto_tree = merged.stdout.splitlines()[0].decode()
        git("cat-file", "-e", auto_tree + "^{tree}")
    # Comparing to the automatic merge also captures edits made before the start tag.
    paths = git("diff", "--name-only", "--no-renames", "-z", auto_tree, submit).stdout.split(b"\0")
    paths = [p.decode("utf-8") for p in paths if p]
    files, deleted = [], []
    payloads = {}
    for path in paths:
        p = PurePosixPath(path)
        if p.is_absolute() or ".." in p.parts or ".git" in p.parts:
            raise ValueError("Unsafe path: " + path)
        if any(x in {"build", "node_modules", "__pycache__", ".venv"} for x in p.parts) or p.suffix in {".o", ".img", ".pyc", ".log"}:
            raise ValueError("Generated output is tracked; remove it from the submission commit: " + path)
        entry = git("ls-tree", "-z", submit, "--", path).stdout
        if not entry:
            deleted.append(path)
            continue
        mode = entry.split(b" ", 1)[0].decode()
        if mode not in {"100644", "100755"}:
            raise ValueError("Changed symlink/submodule is unsupported; submit through Git: " + path)
        payloads[path] = (git("show", submit + ":" + path).stdout, mode)
        files.append(path)
    manifest = {
        "format": 1, "lab": args.lab, "student": args.student,
        "framework_commit": framework, "previous_submission_commit": previous,
        "start_commit": start, "submission_commit": submit,
        "submission_tree": git("rev-parse", submit + "^{tree}").stdout.decode().strip(),
        "comparison": "automatic merge of framework and previous, including conflict resolutions",
        "files": files, "deleted": deleted,
        "file_modes": {p: payloads[p][1] for p in files},
        "git_version": git("--version").stdout.decode().strip(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Refuse to replace a previous submission silently.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("submission.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        archive.writestr("deleted.txt", "\n".join(deleted) + ("\n" if deleted else ""))
        archive.writestr("README.txt", "Apply files/ after merging the recorded framework and previous submission.\n"
                         "Delete only paths listed in deleted.txt; restore file_modes from submission.json.\n"
                         "Check git write-tree against submission_tree after staging.\n"
                         "This archive is incremental and requires earlier submissions when previous is set.\n")
        for path, (data, mode) in payloads.items():
            info = zipfile.ZipInfo("files/" + path)
            info.create_system = 3
            info.external_attr = (int(mode, 8) << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    print(f"Created {output}: {len(files)} files, {len(deleted)} deletions")
    print(f"Submission: {submit}\nTree: {manifest['submission_tree']}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, subprocess.CalledProcessError, FileExistsError) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
