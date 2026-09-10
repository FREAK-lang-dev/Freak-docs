#!/usr/bin/env python3
"""Sync the FREAK label taxonomy to GitHub repositories.

Source of truth is meta/labels.json. The script is idempotent: it creates
labels that are missing, updates colour/description where they drift, and
leaves everything else alone.

It is READ-ONLY by default. Nothing is written to GitHub unless you pass
--apply, and nothing is ever deleted unless you additionally pass --prune.

Usage:
    export GITHUB_TOKEN=ghp_...                     # needs `repo` scope

    python tools/sync_labels.py                     # plan for every repo
    python tools/sync_labels.py --repo owner/name   # plan for one
    python tools/sync_labels.py --apply             # create and update
    python tools/sync_labels.py --apply --prune     # also retire stock labels

`--prune` only ever removes labels listed under "retire" in labels.json, and
refuses to remove one that is still applied to an open issue unless you pass
--force-prune. Removing a label from GitHub removes it from every issue that
carries it, which is not undoable.

No third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "meta" / "labels.json"
API = "https://api.github.com"


# --------------------------------------------------------------------------
# GitHub plumbing
# --------------------------------------------------------------------------

def request(method: str, url: str, token: str | None, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "freak-label-sync")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read().decode()
            return resp.status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as e:
        payload = e.read().decode()
        try:
            return e.code, json.loads(payload)
        except json.JSONDecodeError:
            return e.code, {"message": payload[:200]}


def fetch_labels(repo: str, token: str | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    page = 1
    while True:
        status, body = request(
            "GET", f"{API}/repos/{repo}/labels?per_page=100&page={page}", token)
        if status != 200:
            raise RuntimeError(f"{repo}: {status} {body.get('message') if isinstance(body, dict) else body}")
        if not body:
            break
        for lab in body:
            out[lab["name"]] = lab
        if len(body) < 100:
            break
        page += 1
    return out


def label_in_use(repo: str, name: str, token: str | None) -> int:
    """How many open issues still carry this label."""
    q = urllib.parse.quote(name)
    status, body = request(
        "GET", f"{API}/repos/{repo}/issues?state=open&labels={q}&per_page=100", token)
    if status != 200 or not isinstance(body, list):
        return -1
    return len(body)


# --------------------------------------------------------------------------
# Planning
# --------------------------------------------------------------------------

def validate(spec: dict) -> list[str]:
    """Check the taxonomy is internally consistent and GitHub-legal."""
    errs: list[str] = []
    hexish = set("0123456789abcdef")

    for set_name, labs in spec["sets"].items():
        for lab in labs:
            colour = lab.get("color", "")
            if len(colour) != 6 or not set(colour.lower()) <= hexish:
                errs.append(f"{set_name}: bad colour {lab['name']}={colour!r}")
            if len(lab["name"]) > 50:
                errs.append(f"{set_name}: name over 50 chars: {lab['name']}")
            if len(lab.get("description", "")) > 100:
                errs.append(f"{set_name}: description over 100 chars: {lab['name']}")

    for repo, sets in spec["repos"].items():
        seen: dict[str, dict] = {}
        for set_name in sets:
            if set_name not in spec["sets"]:
                errs.append(f"{repo}: unknown set {set_name!r}")
                continue
            for lab in spec["sets"][set_name]:
                prev = seen.get(lab["name"])
                if prev and (prev["color"] != lab["color"]
                             or prev.get("description") != lab.get("description")):
                    errs.append(f"{repo}: conflicting definitions of {lab['name']}")
                seen[lab["name"]] = lab

    known = {lab["name"] for labs in spec["sets"].values() for lab in labs}
    for entry in spec.get("retire", []):
        if entry["replaced_by"] not in known:
            errs.append(f"retire {entry['name']}: unknown replacement "
                        f"{entry['replaced_by']!r}")
    return errs


def desired_for(spec: dict, repo: str) -> dict[str, dict]:
    """Merge the label sets assigned to one repo. Later sets win on conflict."""
    wanted: dict[str, dict] = {}
    for set_name in spec["repos"].get(repo, []):
        for lab in spec["sets"][set_name]:
            wanted[lab["name"]] = lab
    return wanted


def plan(repo: str, spec: dict, token: str | None, prune: bool):
    existing = fetch_labels(repo, token)
    wanted = desired_for(spec, repo)

    create, update, retire = [], [], []

    for name, lab in sorted(wanted.items()):
        cur = existing.get(name)
        if cur is None:
            create.append(lab)
        else:
            same_colour = cur["color"].lower() == lab["color"].lower()
            same_desc = (cur.get("description") or "") == lab.get("description", "")
            if not (same_colour and same_desc):
                update.append(lab)

    if prune:
        for entry in spec.get("retire", []):
            if entry["name"] in existing and entry["name"] not in wanted:
                retire.append(entry)

    extra = sorted(set(existing) - set(wanted)
                   - {e["name"] for e in spec.get("retire", [])})
    return create, update, retire, extra


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", action="append",
                    help="owner/name; repeatable. Defaults to every repo in labels.json")
    ap.add_argument("--apply", action="store_true", help="actually write to GitHub")
    ap.add_argument("--prune", action="store_true",
                    help="also delete the stock labels listed under 'retire'")
    ap.add_argument("--force-prune", action="store_true",
                    help="prune even labels still applied to open issues")
    ap.add_argument("--validate-only", action="store_true",
                    help="check labels.json for consistency and exit")
    args = ap.parse_args()

    spec = json.loads(SPEC.read_text(encoding="utf-8"))

    problems = validate(spec)
    if problems:
        print("labels.json is not valid:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 2
    if args.validate_only:
        names = {l["name"] for labs in spec["sets"].values() for l in labs}
        print(f"labels.json OK — {len(names)} distinct labels, "
              f"{len(spec['sets'])} sets, {len(spec['repos'])} repos")
        return 0

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    if args.apply and not token:
        print("--apply needs GITHUB_TOKEN (or GH_TOKEN) with `repo` scope",
              file=sys.stderr)
        return 2
    if not token:
        print("note: no token set — planning against the public API, "
              "which is rate limited\n")

    repos = args.repo or list(spec["repos"])
    unknown = [r for r in repos if r not in spec["repos"]]
    if unknown:
        print(f"not in labels.json: {', '.join(unknown)}", file=sys.stderr)
        return 2

    mode = "APPLY" if args.apply else "PLAN (no changes written)"
    print(f"FREAK label taxonomy — {mode}\n")

    failures = 0
    for repo in repos:
        try:
            create, update, retire, extra = plan(repo, spec, token, args.prune)
        except RuntimeError as e:
            print(f"{repo}\n  ERROR {e}\n")
            failures += 1
            continue

        total = len(create) + len(update) + len(retire)
        print(f"{repo}")
        if total == 0 and not extra:
            print("  up to date\n")
            continue

        for lab in create:
            print(f"  + create  {lab['name']}")
            if args.apply:
                status, body = request("POST", f"{API}/repos/{repo}/labels", token, {
                    "name": lab["name"], "color": lab["color"],
                    "description": lab.get("description", ""),
                })
                if status not in (200, 201):
                    print(f"      failed: {status} {body.get('message')}")
                    failures += 1

        for lab in update:
            print(f"  ~ update  {lab['name']}")
            if args.apply:
                name = urllib.parse.quote(lab["name"])
                status, body = request("PATCH", f"{API}/repos/{repo}/labels/{name}", token, {
                    "new_name": lab["name"], "color": lab["color"],
                    "description": lab.get("description", ""),
                })
                if status != 200:
                    print(f"      failed: {status} {body.get('message')}")
                    failures += 1

        for entry in retire:
            name = entry["name"]
            used = label_in_use(repo, name, token) if args.apply else -1
            if args.apply and used > 0 and not args.force_prune:
                print(f"  ! keep    {name} — still on {used} open issue(s); "
                      f"relabel first, or pass --force-prune")
                continue
            print(f"  - delete  {name}  (superseded by {entry['replaced_by']})")
            if args.apply:
                status, body = request(
                    "DELETE", f"{API}/repos/{repo}/labels/{urllib.parse.quote(name)}", token)
                if status not in (204, 404):
                    print(f"      failed: {status} {body.get('message') if body else ''}")
                    failures += 1

        for name in extra:
            print(f"  ? unknown {name} — not in the taxonomy, left alone")

        print()

    if not args.apply and not failures:
        print("Nothing was written. Re-run with --apply to make these changes.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
