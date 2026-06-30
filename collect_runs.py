import subprocess, os, sys
from pathlib import Path

HERE = Path.cwd()
STORE_DIR = HERE/"runs_data"
os.system(f"rm -rf {STORE_DIR}")  # Cleanup

NUM_RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 10

for r in range(NUM_RUNS):
    run_dir = STORE_DIR/f"run_{r}"
    os.makedirs(run_dir)
    subprocess.run(["cp", HERE/"qs_large.sh", run_dir])
    subprocess.run(["cp", HERE/"default_glibc.json", run_dir])
    subprocess.run(["bash", "qs_large.sh"], cwd=run_dir)
    subprocess.run(["python", "/home/exouser/mcb_test_app/process_ooo.py", str(run_dir)], cwd=run_dir)
    print(f"Finished run {r}...")

print("Finished all runs")
