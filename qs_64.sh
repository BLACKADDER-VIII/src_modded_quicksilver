# Larger-event-graph Quicksilver run for ANACIN-X tracing.
#
# Graph nodes come from MPI events, not from compute. In QS the dominant
# source is the per-cycle "while(!done)" communication-round loop in main.cc:
# each round does the particle-exchange Isend/Irecv/Test plus one Test_Done_New
# (Allreduce/Iallreduce) across all ranks. So:
#
#     nodes ~= nSteps * (comm-rounds/cycle) * (MPI ops/round * ranks)
#
# More particles/cells only make each message BIGGER, not more numerous, which
# is why 4M->16M + 20^3->40^3 barely moved the node count. The real lever is the
# number of cross-domain hand-off rounds per cycle, driven by how far particles
# travel each timestep:
#   - dt 1e-08 -> 1e-06 : ~100x longer flight per cycle, so particles cross many
#                         domain boundaries (reflect BC makes them ricochet and
#                         keep crossing) => many Test_Done rounds per cycle.
#   - nSteps 10 -> 60   : linear multiplier on top of the per-cycle rounds.
# 64 MPI procs: xDom*yDom*zDom = 4*4*4 = 64. Quicksilver asserts one
# domain per rank (initMC.cc:273), so -np must equal the product.
#
# NOTE: getParameters() parses the input file AFTER the command line, so .inp
# values OVERRIDE CLI flags. dt and nSteps live in the .inp, so they must be set
# there -- hence the dedicated homogeneousProblem_v5_ts_large.inp (dt=1e-06,
# nSteps=60). nParticles is absent from the .inp, so the CLI flag still applies.
rm -f dumpi-*.bin dumpi-*.meta pluto_out*.txt
export CSMPI_CONFIG=default_glibc.json
OMP_NUM_THREADS=1 LD_PRELOAD=/home/exouser/ANACIN-X/submodules/PnMPI/build/lib/libpnmpi.so PNMPI_LIB_PATH=/home/exouser/ANACIN-X/anacin-x/pnmpi/patched_libs PNMPI_CONF=/home/exouser/ANACIN-X/anacin-x/pnmpi/configs/dumpi_pluto_csmpi.conf mpirun -np 64 /home/exouser/src_modded_quicksilver/src/qs -i /home/exouser/Quicksilver/Examples/Homogeneous/homogeneousProblem_v5_ts_large.inp --lx=200 --ly=200 --lz=200 --nx=20 --ny=20 --nz=20 --xDom=4 --yDom=4 --zDom=4 --nParticles=100000>& log.txt &&
mpirun -np 64 --bind-to none /home/exouser/ANACIN-X/submodules/dumpi_to_graph/build/dumpi_to_graph /home/exouser/ANACIN-X/submodules/dumpi_to_graph/config/dumpi_and_csmpi.json . >& dumpi_to_graph_output.txt
