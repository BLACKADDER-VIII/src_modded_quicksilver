import subprocess, os, sys, statistics
from pathlib import Path

HERE = Path.cwd()

# Per-rank-count experiment configs. Each topology's factors multiply to NPROCS.
# nx=ny=nz is the LCM of all factors so every shape divides the cubic mesh
# evenly; NPART keeps >=~12 particles/cell (above the ~6/cell transport-collapse
# floor -- see quicksilver-ooo-variance memory). Topologies span pencil (1 split
# axis, fan-in 2) -> plane (2) -> 3D (3 split axes, fan-in up to 5).
CONFIGS = {
    16: dict(
        topos=[(16, 1, 1), (8, 2, 1), (4, 4, 1), (4, 2, 2), (2, 2, 4), (1, 4, 4)],
        nx=16, npart=100000),
    18: dict(  # 18=2*3^2 -> 4 shapes, full fan-in 2/3/4/5 ladder (2x3x3 -> 5)
        topos=[(1, 1, 18), (1, 2, 9), (1, 3, 6), (2, 3, 3)],
        nx=18, npart=90000),    # 18^3=5832 cells -> ~15.4/cell
    20: dict(  # 20=2^2*5 -> 4 shapes, fan-in caps at 4
        topos=[(1, 1, 20), (1, 2, 10), (1, 4, 5), (2, 2, 5)],
        nx=20, npart=120000),   # 20^3=8000 cells -> ~15/cell
    24: dict(
        topos=[(1, 1, 24), (1, 2, 12), (1, 3, 8), (1, 4, 6), (2, 2, 6), (2, 3, 4)],
        nx=24, npart=200000),   # 24^3=13824 cells -> ~14.5/cell
    27: dict(  # 27=3^3 -> 3 shapes; 3x3x3 is the ONLY fan-in-6 (fully 3D) topo
        topos=[(1, 1, 27), (1, 3, 9), (3, 3, 3)],
        nx=27, npart=300000),   # 27^3=19683 cells -> ~15/cell
    28: dict(  # 28=2^2*7 -> 4 shapes, fan-in caps at 4
        topos=[(1, 1, 28), (1, 2, 14), (1, 4, 7), (2, 2, 7)],
        nx=28, npart=330000),   # 28^3=21952 cells -> ~15/cell
    32: dict(
        topos=[(32, 1, 1), (16, 2, 1), (8, 4, 1), (8, 2, 2), (4, 4, 2), (2, 4, 4)],
        nx=32, npart=500000),   # 32^3=32768 cells -> ~15/cell
}

# Usage: python collect_decomp.py [NPROCS] [REPS]   (defaults: 32, 3)
NPROCS = int(sys.argv[1]) if len(sys.argv) > 1 else 32
REPS   = int(sys.argv[2]) if len(sys.argv) > 2 else 3
if NPROCS not in CONFIGS:
    sys.exit(f"no config for {NPROCS} ranks; choose from {sorted(CONFIGS)}")

cfg = CONFIGS[NPROCS]
TOPOS = cfg["topos"]
NX = NY = NZ = cfg["nx"]
NPART = cfg["npart"]

# Seed is FIXED (in the .inp), so replicates only expose the MPI-timing jitter
# floor -- the real signal is BETWEEN topologies.
STORE_DIR = HERE/f"decomp_runs_np{NPROCS}"
os.system(f"rm -rf {STORE_DIR}")  # Cleanup

PROCESS_OOO = "/home/exouser/mcb_test_app/process_ooo.py"

for (xd, yd, zd) in TOPOS:
    name = f"dom_{xd}x{yd}x{zd}"
    for r in range(REPS):
        run_dir = STORE_DIR/name/f"run_{r}"
        os.makedirs(run_dir)
        subprocess.run(["cp", HERE/"qs_decomp.sh", run_dir])
        env = os.environ.copy()
        env.update(QS_XDOM=str(xd), QS_YDOM=str(yd), QS_ZDOM=str(zd),
                   QS_NX=str(NX), QS_NY=str(NY), QS_NZ=str(NZ),
                   QS_NPART=str(NPART))
        subprocess.run(["bash", "qs_decomp.sh"], cwd=run_dir, env=env)
        subprocess.run(["python", PROCESS_OOO, str(run_dir)], cwd=run_dir)
        print(f"Finished {name} run {r}")

print("Finished all runs")

# ---- summary: OOO fraction per topology --------------------------------------
def col_sum(path):
    try:
        with open(path) as f:
            return sum(int(x) for x in f if x.strip())
    except FileNotFoundError:
        return 0

print(f"\n=== OOO by decomposition topology  (np={NPROCS}, nx={NX}, "
      f"nPart={NPART}, fixed seed -> reps = jitter floor) ===")
print(f"{'topology':12} {'fanin':>5} {'oooFrac':>9} {'sd':>7} {'msgs':>8}")
for (xd, yd, zd) in TOPOS:
    name = f"dom_{xd}x{yd}x{zd}"
    # max neighbor fan-in for an interior subdomain along each split axis
    fanin = sum(2 if d >= 3 else (1 if d == 2 else 0) for d in (xd, yd, zd))
    fracs, msgs = [], []
    for r in range(REPS):
        rd = STORE_DIR/name/f"run_{r}"
        o = col_sum(rd/"trace_ooo_per_process.txt")
        t = col_sum(rd/"trace_total_per_process.txt")
        if t > 0:
            fracs.append(o / t); msgs.append(t)
    if fracs:
        m = statistics.mean(fracs)
        sd = statistics.pstdev(fracs) if len(fracs) > 1 else 0.0
        print(f"{name:12} {fanin:5d} {m:9.4f} {sd:7.4f} {int(statistics.mean(msgs)):8d}")
    else:
        print(f"{name:12} {fanin:5d} {'no msgs':>9}")
