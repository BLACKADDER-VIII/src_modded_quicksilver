#!/usr/bin/env python3
"""Aggregate <prefix>_rank_*.tsv files into a per-process out-of-order count.

OOO is measured cross-source at each receiver exactly as in aggregate_ooo.py:
a receive is flagged out-of-order iff its SC (Lamport clock) is strictly less
than the max SC the receiver has already observed across any sender. Each OOO
receive is attributed to its *sender*.

Two plain .txt files are written, each one column, one row per process:
  <prefix>_ooo_per_process.txt   -> row i = OOO messages sent by process i
  <prefix>_total_per_process.txt -> row i = total messages sent by process i
For example, if process 5 sent 160 OOO messages, row 5 (0-indexed) of the OOO
file holds 160.

Usage:
  python3 process_ooo.py [trace_dir] [--prefix NAME] [--out FILE]

If [trace_dir] is omitted, uses the cwd. --prefix selects which trace channel
to aggregate (trace (default), gather, scatter). --out sets the OOO output path
(default: <prefix>_ooo_per_process.txt inside trace_dir); the total file is
written alongside it as <prefix>_total_per_process.txt.
"""
import argparse
import glob
import os
import re
import sys


def load_traces(trace_dir, prefix="trace"):
    paths = sorted(glob.glob(os.path.join(trace_dir, f"{prefix}_rank_*.tsv")))
    if not paths:
        sys.exit(f"no {prefix}_rank_*.tsv files in {trace_dir}")
    traces = {}
    for p in paths:
        m = re.search(rf"{re.escape(prefix)}_rank_(\d+)\.tsv$", p)
        rank = int(m.group(1))
        rows = []
        with open(p) as f:
            f.readline()  # skip header
            for line in f:
                line = line.strip()
                if not line:
                    continue
                s, c = line.split("\t")
                rows.append((int(s), int(c)))
        traces[rank] = rows
    return traces


def count_per_sender(traces):
    """Return (total, ooo) lists indexed by sender.

    total[i] = number of messages sent by process i.
    ooo[i]   = number of those that arrived out-of-order at their receiver.
    """
    # Size covers both observed receivers and sources.
    n = max(traces) + 1
    for rows in traces.values():
        for source, _ in rows:
            n = max(n, source + 1)
    total = [0] * n
    ooo = [0] * n
    for receiver, rows in traces.items():
        max_sc = 0
        for source, sc in rows:
            total[source] += 1
            if sc < max_sc:
                ooo[source] += 1
            if sc > max_sc:
                max_sc = sc
    return total, ooo


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("trace_dir", nargs="?", default=".",
                        help="directory holding the *_rank_*.tsv files (default: cwd)")
    parser.add_argument("--prefix", default="trace",
                        help="trace channel to aggregate: trace (default), gather, scatter")
    parser.add_argument("--out", default=None,
                        help="output .txt path (default: <prefix>_ooo_per_process.txt in trace_dir)")
    opts = parser.parse_args()

    traces = load_traces(opts.trace_dir, opts.prefix)
    total, ooo = count_per_sender(traces)

    ooo_out = opts.out or os.path.join(opts.trace_dir, f"{opts.prefix}_ooo_per_process.txt")
    total_out = os.path.join(os.path.dirname(ooo_out) or ".",
                             f"{opts.prefix}_total_per_process.txt")
    for path, counts in ((ooo_out, ooo), (total_out, total)):
        with open(path, "w") as f:
            for count in counts:
                f.write(f"{count}\n")

    print(f"loaded {len(traces)} ranks from {opts.trace_dir} (prefix={opts.prefix})")
    print(f"total messages: {sum(total)}, total OOO messages: {sum(ooo)}")
    print(f"wrote {ooo_out}")
    print(f"wrote {total_out}")


if __name__ == "__main__":
    main()
