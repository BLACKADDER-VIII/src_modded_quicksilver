import shutil, subprocess
from pathlib import Path

HERE = Path.cwd()
TARGET = Path("/home/exouser/Enzo_ND_Detect/data/sims")

subprocess.run(f"rm -rf {TARGET}/*", shell=True)

run_suffix = 0
while (HERE / f"runs_data/run_{run_suffix}").is_dir():
    payload = HERE / f"runs_data/run_{run_suffix}"
    dest = TARGET / f"sim_{run_suffix}"
    dest.mkdir(parents=True, exist_ok=True)

    graphml = payload / "event_graph.graphml"
    if graphml.is_file():
        shutil.move(str(graphml), str(dest / "event_graph.graphml"))
    trace_ooo = payload / "trace_ooo_per_process.txt"
    
    if trace_ooo.is_file():
        shutil.move(str(trace_ooo), str(dest / "trace_ooo_per_process.txt"))
    trace_total = payload / "trace_total_per_process.txt"
    if trace_total.is_file():
        shutil.move(str(trace_total), str(dest / "trace_total_per_process.txt"))
    for pattern in ("*.csmpi", "*.symtab"):
        for f in payload.glob(pattern):
            shutil.move(str(f), str(dest / f.name))

    print(f"Transferred run data for run {run_suffix}...")
    run_suffix += 1

print("Finished transferring")