import subprocess, os, sys
from pathlib import Path

HERE = Path.cwd()
STORE_DIR = HERE/"runs_data"
os.system(f"rm -rf {STORE_DIR}")  # Cleanup

if len(sys.argv) < 2:
    print("Need Ranks size")
    exit()
NUM_RANKS = int(sys.argv[1])
NUM_RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 10

for r in range(NUM_RUNS):
    run_dir = STORE_DIR/f"run_{r}"
    os.makedirs(run_dir)
    if NUM_RANKS == 32:
        subprocess.run(["cp", HERE/"qs_32.sh", run_dir])
    elif NUM_RANKS == 64:
        subprocess.run(["cp", HERE/"qs_64.sh", run_dir])
    else:
        print("Need rank size to be 32 or 64")
        exit()
    subprocess.run(["cp", HERE/"default_glibc.json", run_dir])
    if NUM_RANKS == 32:
        subprocess.run(["bash", "qs_32.sh"], cwd=run_dir)
    elif NUM_RANKS == 64:
        subprocess.run(["bash", "qs_64.sh"], cwd=run_dir)
    else:
        print("Need ranks to be 32 or 64")
        exit()
    subprocess.run(["python", "/home/exouser/mcb_test_app/process_ooo.py", str(run_dir)], cwd=run_dir)
    print(f"Finished run {r}...")

print("Finished all runs")
