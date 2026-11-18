"""Run the Haiku extract on every batch with the headless claude CLI. Skips batches that already have output.

Usage: python3 -I scripts/run_extract.py data/batches prompts/extract.md [--context context.md] [--workers 6] [--only b000,b001]
Writes data/batches/out_bXXX.jsonl and BATCHDIR/err_bXXX.txt on failure.
"""
import argparse, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("batchdir"); ap.add_argument("prompt"); ap.add_argument("--workers", type=int, default=6)
ap.add_argument("--only", default=""); ap.add_argument("--model", default="sonnet"); ap.add_argument("--context", default=os.path.expanduser("~/mine-claude-data/context.md")); ap.add_argument("--extra-args", default="")
a = ap.parse_args()
d = Path(a.batchdir)
instr = Path(a.prompt).read_text()
if Path(a.context).exists():
    instr += "\n\n----- CONTEXT ABOUT ME -----\n" + Path(a.context).read_text()
only = set(x for x in a.only.split(",") if x)
todo = [f for f in sorted(d.glob("b*.txt")) if (not only or f.stem in only)
        and not ((d / f"out_{f.stem}.jsonl").exists() and (d / f"out_{f.stem}.jsonl").stat().st_size > 0)]
print(len(todo), "batches to run", flush=True)

CMD = ["claude", "-p", "--model", a.model, "--no-session-persistence", "--tools", "",
       "--setting-sources", "", "--strict-mcp-config", "--output-format", "text"] + a.extra_args.split()


def run(f):
    inp = instr + "\n\n----- INPUT -----\n\n" + f.read_text()
    for attempt in range(2):
        t0 = time.time()
        p = subprocess.run(CMD, input=inp, capture_output=True, text=True, timeout=900, cwd="/tmp")
        out = p.stdout.strip()
        if p.returncode == 0 and out:
            lines = [l for l in out.splitlines() if l.strip().startswith("{")]
            (d / f"out_{f.stem}.jsonl").write_text("\n".join(lines) + ("\n" if lines else "") if lines or out == "NONE" else "")
            if lines or out.strip() == "NONE":
                if out.strip() == "NONE":
                    (d / f"out_{f.stem}.jsonl").write_text("NONE\n")
                return f"{f.stem} ok {len(lines)} lines {time.time()-t0:.0f}s"
        (d / f"err_{f.stem}.txt").write_text(f"rc={p.returncode}\nSTDOUT:\n{out[:3000]}\nSTDERR:\n{p.stderr[:3000]}")
    return f"{f.stem} FAILED"


with ThreadPoolExecutor(a.workers) as ex:
    for r in ex.map(run, todo):
        print(r, flush=True)
