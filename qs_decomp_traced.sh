#!/bin/bash
# Per-run runner WITH ANACIN-X tracing. Produces BOTH:
#   - trace_rank_*.tsv     : QS's internal Lamport OOO source (compiled into QS)
#   - event_graph.graphml  : ANACIN-X event graph (for ND-node detection)
# i.e. the paired (OOO, ND) data for one run.
#
# Topology / mesh / particle count come from env vars (set by
# collect_decomp_traced.py); -np is DERIVED from the topology so
# xDom*yDom*zDom always == ranks. Seed stays FIXED via the .inp
# (seed: 1029384756) -- the variance comes from the decomposition shape.
#
# This mirrors qs_large.sh (PnMPI -> dumpi -> dumpi_to_graph) but parameterized.
set -u

# spack-built MPI + tracing libs. loadAnacinSpack.sh uses $HOME-relative paths,
# so source it from there, then return to the run dir.
_OLD=$PWD; cd /home/exouser && source /home/exouser/loadAnacinSpack.sh; cd "$_OLD"

XDOM=${QS_XDOM:-4};  YDOM=${QS_YDOM:-2};  ZDOM=${QS_ZDOM:-2}
NX=${QS_NX:-32};     NY=${QS_NY:-32};     NZ=${QS_NZ:-32}
NPART=${QS_NPART:-500000}
NP=$((XDOM * YDOM * ZDOM))

rm -f dumpi-*.bin dumpi-*.meta pluto_out*.txt trace_rank_*.tsv log.txt

# One OMP thread per rank (otherwise ranks each spawn N threads -> oversubscribe).
export OMP_NUM_THREADS=1
export CSMPI_CONFIG=default_glibc.json

LD_PRELOAD=/home/exouser/ANACIN-X/submodules/PnMPI/build/lib/libpnmpi.so \
PNMPI_LIB_PATH=/home/exouser/ANACIN-X/anacin-x/pnmpi/patched_libs \
PNMPI_CONF=/home/exouser/ANACIN-X/anacin-x/pnmpi/configs/dumpi_pluto_csmpi.conf \
mpirun -np "$NP" /home/exouser/Quicksilver/src/qs \
  -i /home/exouser/Quicksilver/Examples/Homogeneous/homogeneousProblem_v5_ts_large.inp \
  --lx=200 --ly=200 --lz=200 --nx="$NX" --ny="$NY" --nz="$NZ" \
  --xDom="$XDOM" --yDom="$YDOM" --zDom="$ZDOM" --nParticles="$NPART" >& log.txt &&
mpirun -np "$NP" --bind-to none \
  /home/exouser/ANACIN-X/submodules/dumpi_to_graph/build/dumpi_to_graph \
  /home/exouser/ANACIN-X/submodules/dumpi_to_graph/config/dumpi_and_csmpi.json . \
  >& dumpi_to_graph_output.txt

# Drop the heavy intermediates once the event graph is built. The rank_*.csmpi
# call-stack traces are the real disk hog (~2 GB/run) and are consumed during
# graph generation. KEEP the rank_*.symtab files -- downstream get_func_tree()
# reads them. Guarded on a non-empty graph so a FAILED dumpi_to_graph leaves the
# traces intact for re-processing.
if [ -s event_graph.graphml ]; then
    rm -f dumpi-*.bin dumpi-*.meta pluto_out*.txt *.csmpi
fi
