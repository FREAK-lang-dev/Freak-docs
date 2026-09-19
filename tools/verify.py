#!/usr/bin/env python3
"""Verify every documentation example against the real FREAK V3 compiler.

For each examples/*.fk the harness runs `freak build` (LLVM backend, the
shipping default) in an isolated working directory, then executes the produced
binary and records its stdout. Results land in examples/verified.json, which the
site generator embeds so every published snippet carries a real verdict.

Usage:
    python tools/verify.py --freak <path-to-freak.exe> --provenance <metadata.json> [--jobs N]
    # Partial debug runs also require --only NAME --output <separate-report.json>.
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

from evidence import expectations, file_hash, input_hash

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
OUT = EXAMPLES / "verified.json"

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI.sub("", text)


def decode(raw: bytes) -> str:
    """Decode child output without universal-newline translation.

    Text mode folds a lone carriage return into a newline, which destroys
    exactly the bytes a same-line-printing example is about. Only the
    platform CRLF pairing is normalised here; a standalone CR is content.
    """
    text = raw.decode("utf-8", errors="replace")
    return text.replace(chr(13) + chr(10), chr(10))


def scrub(text: str, work: Path) -> str:
    """Replace the throwaway build directory with a stable placeholder.

    An example that prints argv[0] would otherwise bake this machine's
    username and a random temp directory into published output, and produce
    a spurious diff on every run.
    """
    raw = str(work)
    for variant in (raw, raw.replace(chr(92), "/"), raw.replace("/", chr(92))):
        text = text.replace(variant, "/build")
    # The separator that followed the directory is still platform-native.
    return text.replace("/build" + chr(92), "/build/")


def run(cmd, cwd, timeout=180, stdin_text="", keep_ansi=False):
    environment = os.environ.copy()
    if keep_ansi:
        # Documentation captures the colour-enabled tutorial output regardless
        # of a developer terminal or CI runner's presentation preferences.
        environment.pop("NO_COLOR", None)
        environment.pop("FORCE_COLOR", None)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        input=stdin_text.encode() if stdin_text else None,
        capture_output=True,
        timeout=timeout,
        env=environment,
    )
    out = decode(proc.stdout or b"")
    err = decode(proc.stderr or b"")
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


def verify_one(freak: Path, src: Path, run_args: list[str], expectation: dict) -> dict:
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
        "passed": False,
    }

    with tempfile.TemporaryDirectory(prefix="fkdocs_") as tmp:
        work = Path(tmp)
        target = work / src.name
        shutil.copy2(src, target)

        try:
            code, out, err = run([str(freak), "build", src.name], work)
        except (subprocess.TimeoutExpired, OSError) as exc:
            result["errors"] = [f"build failed: {type(exc).__name__}"]
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
                result["stdout"] = scrub(rout, work).removesuffix("\n")
                if rcode != 0:
                    result["errors"].append(f"execution exited with status {rcode}")
                elif result["stdout"] not in expectation["stdout_any_of"]:
                    result["errors"].append("stdout differs from the reviewed expectation")
                if rerr.strip():
                    result["stderr"] = scrub(rerr, work).strip()
            except (subprocess.TimeoutExpired, OSError) as exc:
                result["errors"].append(f"execution failed: {type(exc).__name__}")
        else:
            result["errors"].append("compiler reported success but produced no executable")

    result["passed"] = result["compiled"] and result["ran"] and not result["errors"]
    result["elapsed_ms"] = int((time.time() - started) * 1000)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freak", required=True, help="path to the V3 freak binary")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--only", default=None)
    ap.add_argument("--output", type=Path, default=OUT)
    ap.add_argument("--provenance", type=Path, required=True,
                    help="compiler provenance from tools/fetch_compiler.py")
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("--jobs must be positive")
    if args.only and args.output.resolve() == OUT.resolve():
        ap.error("--only requires a separate --output; partial evidence must not replace the full report")
    expected = expectations(ROOT)
    provenance = json.loads(args.provenance.read_text(encoding="utf-8"))
    provenance.pop("binary", None)  # Do not publish local filesystem paths.

    freak = Path(args.freak).resolve()
    if not freak.exists():
        print(f"compiler not found: {freak}", file=sys.stderr)
        return 2
    if file_hash(freak) != provenance.get("compiler_sha256"):
        print("compiler does not match provenance", file=sys.stderr)
        return 2
    initial_input_hash = input_hash(ROOT)

    # Examples that want command-line arguments when executed.
    run_args = {"process_time": ["alpha", "bravo"]}

    sources = sorted(EXAMPLES.glob("*.fk"))
    if args.only:
        sources = [s for s in sources if s.stem == args.only]
    if not sources:
        print("no examples found", file=sys.stderr)
        return 2

    code, ver_out, _ = run([str(freak), "--version"], ROOT)
    if code != 0 or not ver_out.strip():
        print("compiler version probe failed", file=sys.stderr)
        return 2
    compiler_version = ver_out.strip().splitlines()[0] if ver_out.strip() else "unknown"
    if 'Maverick' not in compiler_version or provenance['release'].lstrip('v') not in compiler_version:
        print("release is not the matching V3 Maverick compiler; refusing to mix generations", file=sys.stderr)
        return 2

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(verify_one, freak, src, run_args.get(src.stem, []), expected[src.stem]): src
            for src in sources
        }
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            results[res["name"]] = res
            mark = "PASS" if res["passed"] else "FAIL"
            extra = "" if res["passed"] else "  :: " + "; ".join(res["errors"])
            print(f"{mark}  {res['name']}{extra}", flush=True)

    ordered = {k: results[k] for k in sorted(results)}
    payload = {
        "schema_version": 1,
        "generation": "v3",
        "channel": "release",
        "provenance": provenance,
        "input_sha256": initial_input_hash,
        "compiler": compiler_version,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total": len(ordered),
        "compiled": sum(1 for r in ordered.values() if r["compiled"]),
        "passed": sum(1 for r in ordered.values() if r["passed"]),
        "examples": ordered,
    }
    if input_hash(ROOT) != initial_input_hash:
        print("inputs changed during verification; refusing to save evidence", file=sys.stderr)
        return 2
    # Rechecking the same inputs should not open daily timestamp-only update PRs.
    # Keep previous evidence only after the fresh run has passed in full.
    if args.output.exists() and payload["passed"] == payload["total"]:
        previous = json.loads(args.output.read_text(encoding="utf-8"))
        from evidence import validate
        try:
            validate(previous, ROOT)
        except (ValueError, KeyError, TypeError):
            pass
        else:
            if previous.get("provenance") == provenance:
                print("Fresh verification passed; existing publication evidence is unchanged")
                return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    failed = payload["total"] - payload["passed"]
    print(f"\n{payload['passed']}/{payload['total']} examples compiled, ran, and matched expected output "
          f"with {compiler_version}")
    print(f"wrote {args.output}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
