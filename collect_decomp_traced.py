import subprocess, os, sys
from pathlib import Path

# Paired (OOO, event-graph) data collection over (rank, topology) configs.
# Output follows the collect_runs.py convention: a flat runs_data/run_<i>/ tree.
# The RUNS_PER_CONFIG runs of each config are stored CONTIGUOUSLY, so downstream
# can group runs [0..4], [5..9], ... into (rank, topology) pairs. A
# config_manifest.csv records the exact run-block -> config mapping.

HERE = Path.cwd()
STORE_DIR = HERE/"runs_data"

RUNS_PER_CONFIG = 5   # downstream groups runs in contiguous blocks of this size

# Per-rank-count topology sets (validated healthy, ~15 particles/cell). Each
# topology's factors multiply to its rank count; nx=ny=nz=LCM(factors) so the
# cubic mesh divides evenly; npart stays above the ~6/cell transport-collapse
# floor. See the quicksilver-ooo-variance memory for the OOO-vs-fan-in results.
RANK_CONFIGS = {
    18: dict(topos=[(1, 1, 18), (1, 2, 9), (1, 3, 6), (2, 3, 3)],
             nx=18, npart=90000),
    24: dict(topos=[(1, 1, 24), (1, 2, 12), (1, 3, 8), (1, 4, 6), (2, 2, 6), (2, 3, 4)],
             nx=24, npart=200000),
    27: dict(topos=[(1, 1, 27), (1, 3, 9), (3, 3, 3)],
             nx=27, npart=300000),
    28: dict(topos=[(1, 1, 28), (1, 2, 14), (1, 4, 7), (2, 2, 7)],
             nx=28, npart=330000),
    32: dict(topos=[(32, 1, 1), (16, 2, 1), (8, 4, 1), (8, 2, 2), (4, 4, 2), (2, 4, 4)],
             nx=32, npart=500000),
}
RANK_ORDER = [18, 24, 27, 28, 32]   # collection order (defines run numbering)

PROCESS_OOO = "/home/exouser/mcb_test_app/process_ooo.py"

# Flatten to an ordered list of configs, one per (rank, topology).
configs = []
for nproc in RANK_ORDER:
    cfg = RANK_CONFIGS[nproc]
    for (xd, yd, zd) in cfg["topos"]:
        configs.append(dict(nproc=nproc, xd=xd, yd=yd, zd=zd,
                            nx=cfg["nx"], npart=cfg["npart"]))

# "plan" mode: write the manifest and print the mapping, run nothing.
PLAN = len(sys.argv) > 1 and sys.argv[1] == "plan"

if not PLAN:
    os.system(f"rm -rf {STORE_DIR}")  # Cleanup
os.makedirs(STORE_DIR, exist_ok=True)

# Manifest: contiguous run block -> (rank, topology). Written before any run so
# even a partial/aborted collection has a complete map.
def fanin_of(xd, yd, zd):
    return sum(2 if d >= 3 else (1 if d == 2 else 0) for d in (xd, yd, zd))

manifest = STORE_DIR/"config_manifest.csv"
with open(manifest, "w") as f:
    f.write("group,run_start,run_end,np,xDom,yDom,zDom,nx,nParticles,fanin\n")
    idx = 0
    for g, c in enumerate(configs):
        f.write(f"{g},{idx},{idx + RUNS_PER_CONFIG - 1},{c['nproc']},"
                f"{c['xd']},{c['yd']},{c['zd']},{c['nx']},{c['npart']},"
                f"{fanin_of(c['xd'], c['yd'], c['zd'])}\n")
        idx += RUNS_PER_CONFIG

total = len(configs) * RUNS_PER_CONFIG
print(f"{len(configs)} configs x {RUNS_PER_CONFIG} runs/config = {total} runs (run_0 .. run_{total-1})")
print(f"manifest -> {manifest}")
if PLAN:
    print("PLAN mode: manifest written, no runs executed.")
    sys.exit(0)

# Execute: flat, contiguous run_<i> dirs (collect_runs.py convention).
run_idx = 0
for c in configs:
    for _ in range(RUNS_PER_CONFIG):
        run_dir = STORE_DIR/f"run_{run_idx}"
        os.makedirs(run_dir)
        subprocess.run(["cp", HERE/"qs_decomp_traced.sh", run_dir])
        subprocess.run(["cp", HERE/"default_glibc.json", run_dir])
        env = os.environ.copy()
        env.update(QS_XDOM=str(c["xd"]), QS_YDOM=str(c["yd"]), QS_ZDOM=str(c["zd"]),
                   QS_NX=str(c["nx"]), QS_NY=str(c["nx"]), QS_NZ=str(c["nx"]),
                   QS_NPART=str(c["npart"]))
        subprocess.run(["bash", "qs_decomp_traced.sh"], cwd=run_dir, env=env)
        subprocess.run(["python", PROCESS_OOO, str(run_dir)], cwd=run_dir)
        print(f"Finished run {run_idx}  "
              f"(np={c['nproc']} {c['xd']}x{c['yd']}x{c['zd']})")
        run_idx += 1

print("Finished all runs")
