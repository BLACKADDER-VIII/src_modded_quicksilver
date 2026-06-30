#!/bin/bash
# Plain Quicksilver run -- NO ANACIN-X tracing (no PnMPI LD_PRELOAD, no dumpi,
# no dumpi_to_graph, no event graph). QS's built-in Lamport instrumentation
# still writes the trace_rank_*.tsv files (the OOO source) because it is
# compiled into QS itself (src/MC_Particle_Buffer.cc), so process_ooo.py works
# exactly as before -- the run is just far cheaper without the trace stack.
#
# Topology + mesh + particle count come from env vars (collect_decomp.py sets
# them); -np is derived from the topology so xDom*yDom*zDom always == ranks.
# Seed stays FIXED via the .inp (seed: 1029384756) -- the variance under test
# comes from the decomposition shape, NOT from reseeding.
set -u

# Make the spack-built MPI available. loadAnacinSpack.sh uses paths relative to
# $HOME, so source it from there, then return to the run dir.
_OLD=$PWD; cd /home/exouser && source /home/exouser/loadAnacinSpack.sh; cd "$_OLD"

XDOM=${QS_XDOM:-4};  YDOM=${QS_YDOM:-2};  ZDOM=${QS_ZDOM:-2}
NX=${QS_NX:-16};     NY=${QS_NY:-16};     NZ=${QS_NZ:-16}
NPART=${QS_NPART:-100000}
NP=$((XDOM * YDOM * ZDOM))

rm -f trace_rank_*.tsv log.txt

# One OMP thread per rank -- otherwise 32 ranks each spawn N threads and badly
# oversubscribe the 32 cores.
export OMP_NUM_THREADS=1

mpirun -np "$NP" /home/exouser/Quicksilver/src/qs \
  -i /home/exouser/Quicksilver/Examples/Homogeneous/homogeneousProblem_v5_ts_large.inp \
  --lx=200 --ly=200 --lz=200 --nx="$NX" --ny="$NY" --nz="$NZ" \
  --xDom="$XDOM" --yDom="$YDOM" --zDom="$ZDOM" --nParticles="$NPART" >& log.txt
