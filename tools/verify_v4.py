#!/usr/bin/env python3
"""Verify the V4 notes against one pinned development snapshot of the compiler.

V4 ("Maverick", the 00-unit architecture) has no release. Every V4 claim in the
documentation is therefore pinned to a single Freak-lang commit, recorded in
v4-snapshot.txt, and checked by building the programs in examples-v4/ with
that commit's own `src/compiler/v4/build_v4.py`.

Two kinds of program live in examples-v4/:

* programs V4 must build and run, with reviewed output and exit code;
* programs V4 must reject, with the reviewed text of its diagnostic.

Results land in examples-v4/verified.json, labelled generation v4, channel
development. This report never certifies V3, and V3 evidence never certifies it.

Usage:
    python tools/verify_v4.py --checkout <path-to-Freak-lang-at-the-pinned-commit> [--jobs N]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evidence import pinned_snapshot, v4_expectations, v4_input_hash

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples-v4"
OUT = EXAMPLES / "verified.json"
REPOSITORY = "FREAK-lang-dev/Freak-lang"
BUILD_SCRIPT = Path("src/compiler/v4/build_v4.py")


def git(checkout: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(checkout), *arguments], encoding="utf-8").strip()


def diagnostic_lines(output: str) -> str:
    """The lines V4 itself reports: coded diagnostics and native contract errors."""
    kept = []
    for raw in output.splitlines():
        line = raw.strip()
        fields = line.split("|")
        coded = len(fields) >= 3 and fields[0].isdigit() and "@" in fields[1]
        if coded or line.startswith("v4-native-contract-error="):
            kept.append(line)
    return "\n".join(kept)


def verify_one(checkout: Path, src: Path, expectation: dict, compiler_opt: int) -> dict:
    started = time.time()
    result = {
        "name": src.stem,
        "file": src.name,
        "source": src.read_text(encoding="utf-8"),
        "built": False,
        "passed": False,
        "errors": [],
    }
    with tempfile.TemporaryDirectory(prefix="fkdocs_v4_") as tmp:
        work = Path(tmp)
        binary = work / src.stem
        command = [sys.executable, str(BUILD_SCRIPT), str(src), "-o", str(binary),
                   "--compiler-opt", str(compiler_opt)]
        try:
            build = subprocess.run(command, cwd=str(checkout), capture_output=True, timeout=900)
        except (subprocess.TimeoutExpired, OSError) as exc:
            result["errors"] = [f"build failed: {type(exc).__name__}"]
            return result
        output = (build.stdout + b"\n" + build.stderr).decode("utf-8", errors="replace")
        produced = binary.exists() or binary.with_suffix(".exe").exists()
        result["built"] = build.returncode == 0 and produced

        if "rejected_with" in expectation:
            result["diagnostic"] = diagnostic_lines(output)
            if result["built"]:
                result["errors"] = ["V4 accepted a program documented as rejected"]
            elif produced or build.returncode == 0:
                # A rejection leaves a failing status and no program behind.
                result["errors"] = ["the build reported failure but left an executable, or success without one"]
            elif "V4 compilation failed" not in output:
                # A crash or a toolchain failure is not a language rule.
                result["errors"] = ["the build did not end in an ordinary V4 rejection"]
            elif expectation["rejected_with"] not in result["diagnostic"]:
                result["errors"] = ["diagnostic is missing the reviewed text"]
        elif not result["built"]:
            result["diagnostic"] = diagnostic_lines(output)
            result["errors"] = ["V4 did not build a program documented as working"]
        else:
            target = binary if binary.exists() else binary.with_suffix(".exe")
            try:
                run = subprocess.run([str(target)], cwd=str(work), capture_output=True,
                                     timeout=60, stdin=subprocess.DEVNULL)
            except (subprocess.TimeoutExpired, OSError) as exc:
                result["errors"] = [f"execution failed: {type(exc).__name__}"]
            else:
                text = run.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
                result["exit_code"] = run.returncode
                result["stdout"] = text.removesuffix("\n")
                if run.returncode != expectation.get("exit_code", 0):
                    result["errors"].append(f"exit code {run.returncode} differs from the reviewed expectation")
                if result["stdout"] not in expectation["stdout_any_of"]:
                    result["errors"].append("stdout differs from the reviewed expectation")
    result["passed"] = not result["errors"]
    result["elapsed_ms"] = int((time.time() - started) * 1000)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--checkout", type=Path, required=True,
                    help="Freak-lang working tree checked out at the commit in v4-snapshot.txt")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--compiler-opt", type=int, choices=[0, 1, 2, 3], default=2,
                    help="optimization level of the bootstrap compiler (does not change semantics)")
    ap.add_argument("--output", type=Path, default=OUT)
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs must be positive")

    checkout = args.checkout.resolve()
    pin = pinned_snapshot(ROOT)
    try:
        head = git(checkout, "rev-parse", "HEAD")
        dirty = git(checkout, "status", "--porcelain", "--untracked-files=all", "--", "src", "freakc")
        commit_date = git(checkout, "show", "-s", "--format=%cI", "HEAD")
    except (subprocess.CalledProcessError, OSError):
        print(f"not a usable Freak-lang checkout: {checkout}", file=sys.stderr)
        return 2
    if head != pin:
        print(f"checkout is at {head}, but v4-snapshot.txt pins {pin}; refusing to mix snapshots", file=sys.stderr)
        return 2
    if dirty:
        print("checkout has modified or untracked compiler files; V4 evidence must come from the pinned commit",
              file=sys.stderr)
        return 2
    if not (checkout / BUILD_SCRIPT).exists():
        print("the pinned commit has no src/compiler/v4/build_v4.py", file=sys.stderr)
        return 2

    expected = v4_expectations(ROOT)
    initial = v4_input_hash(ROOT)
    sources = sorted(EXAMPLES.glob("*.fk"))
    if not sources:
        print("no V4 examples found", file=sys.stderr)
        return 2

    # Build the bootstrap compiler once before fanning out, so parallel jobs
    # share its cache instead of racing to create it.
    first = verify_one(checkout, sources[0], expected[sources[0].stem], args.compiler_opt)
    results = {first["name"]: first}
    print(f"{'PASS' if first['passed'] else 'FAIL'}  {first['name']}", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(verify_one, checkout, src, expected[src.stem], args.compiler_opt)
                   for src in sources[1:]]
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            results[res["name"]] = res
            extra = "" if res["passed"] else "  :: " + "; ".join(res["errors"])
            print(f"{'PASS' if res['passed'] else 'FAIL'}  {res['name']}{extra}", flush=True)

    ordered = {name: results[name] for name in sorted(results)}
    payload = {
        "schema_version": 1,
        "generation": "v4",
        "channel": "development",
        "snapshot": {"repository": REPOSITORY, "commit": pin, "commit_date": commit_date},
        "input_sha256": initial,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(ordered),
        "passed": sum(1 for r in ordered.values() if r["passed"]),
        "examples": ordered,
    }
    if v4_input_hash(ROOT) != initial:
        print("inputs changed during verification; refusing to save evidence", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    failed = payload["total"] - payload["passed"]
    print(f"\n{payload['passed']}/{payload['total']} V4 examples matched their reviewed expectation "
          f"at snapshot {pin[:10]} ({commit_date})")
    print(f"wrote {args.output}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
