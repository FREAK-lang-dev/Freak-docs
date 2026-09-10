#!/usr/bin/env python3
"""Verify every documentation example against the real FREAK V3 compiler.

For each examples/*.fk the harness runs `freak build` (LLVM backend, the
shipping default) in an isolated working directory, then executes the produced
binary and records its stdout. Results land in examples/verified.json, which the
site generator embeds so every published snippet carries a real verdict.

Usage:
    python tools/verify.py --freak <path-to-freak.exe> [--jobs N] [--only NAME]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
OUT = EXAMPLES / "verified.json"

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI.sub("", text)


def run(cmd, cwd, timeout=180, stdin_text="", keep_ansi=False):
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    out = proc.stdout or ""
    err = proc.stderr or ""
    if keep_ansi:
        return proc.returncode, out, err
    return proc.returncode, strip_ansi(out), strip_ansi(err)


def diagnostics(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        low = line.lower()
        if low.startswith("error") or "error:" in low or low.startswith("type error"):
            lines.append(line)
    return lines[:6]


def verify_one(freak: Path, src: Path, run_args: list[str]) -> dict:
    started = time.time()
    result = {
        "name": src.stem,
        "file": src.name,
        "source": src.read_text(encoding="utf-8"),
        "compiled": False,
        "ran": False,
        "stdout": "",
        "errors": [],
        "backend": "llvm",
    }

    with tempfile.TemporaryDirectory(prefix="fkdocs_") as tmp:
        work = Path(tmp)
        target = work / src.name
        shutil.copy2(src, target)

        try:
            code, out, err = run([str(freak), "build", src.name], work)
        except subprocess.TimeoutExpired:
            result["errors"] = ["build timed out"]
            return result

        combined = out + "\n" + err
        if code != 0 or "BUILD SUCCESSFUL" not in combined:
            result["errors"] = diagnostics(combined) or ["build failed"]
            result["elapsed_ms"] = int((time.time() - started) * 1000)
            return result

        result["compiled"] = True

        binary = work / (src.stem + ".exe")
        if not binary.exists():
            binary = work / src.stem
        if binary.exists():
            try:
                rcode, rout, rerr = run([str(binary)] + run_args, work,
                                        timeout=60, keep_ansi=True)
                result["ran"] = rcode == 0
                result["exit_code"] = rcode
                result["stdout"] = rout.rstrip("\n")
                if rerr.strip():
                    result["stderr"] = rerr.strip()
            except subprocess.TimeoutExpired:
                result["errors"].append("execution timed out")

    result["elapsed_ms"] = int((time.time() - started) * 1000)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freak", required=True, help="path to the V3 freak binary")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    freak = Path(args.freak).resolve()
    if not freak.exists():
        print(f"compiler not found: {freak}", file=sys.stderr)
        return 2

    # Examples that want command-line arguments when executed.
    run_args = {"process_time": ["alpha", "bravo"]}

    sources = sorted(EXAMPLES.glob("*.fk"))
    if args.only:
        sources = [s for s in sources if s.stem == args.only]
    if not sources:
        print("no examples found", file=sys.stderr)
        return 2

    code, ver_out, _ = run([str(freak), "--version"], ROOT)
    compiler_version = ver_out.strip().splitlines()[0] if ver_out.strip() else "unknown"

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(verify_one, freak, src, run_args.get(src.stem, [])): src
            for src in sources
        }
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            results[res["name"]] = res
            mark = "PASS" if res["compiled"] else "FAIL"
            extra = "" if res["compiled"] else "  :: " + "; ".join(res["errors"])
            print(f"{mark}  {res['name']}{extra}", flush=True)

    ordered = {k: results[k] for k in sorted(results)}
    payload = {
        "compiler": compiler_version,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(ordered),
        "compiled": sum(1 for r in ordered.values() if r["compiled"]),
        "examples": ordered,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    failed = payload["total"] - payload["compiled"]
    print(f"\n{payload['compiled']}/{payload['total']} examples compiled "
          f"with {compiler_version}")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
