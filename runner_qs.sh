rm -f dumpi-*.bin dumpi-*.meta pluto_out*.txt
export CSMPI_CONFIG=default_glibc.json
OMP_NUM_THREADS=1 LD_PRELOAD=/home/exouser/ANACIN-X/submodules/PnMPI/build/lib/libpnmpi.so PNMPI_LIB_PATH=/home/exouser/ANACIN-X/anacin-x/pnmpi/patched_libs PNMPI_CONF=/home/exouser/ANACIN-X/anacin-x/pnmpi/configs/dumpi_pluto_csmpi.conf mpirun -np 16 /home/exouser/Quicksilver/src/qs -i /home/exouser/Quicksilver/Examples/Homogeneous/homogeneousProblem_v5_ts.inp --lx=200 --ly=200 --lz=200 --nx=20 --ny=20 --nz=20 --xDom=4 --yDom=2 --zDom=2 --nParticles=4000000>& log.txt &&
mpirun -np 16 --bind-to none /home/exouser/ANACIN-X/submodules/dumpi_to_graph/build/dumpi_to_graph /home/exouser/ANACIN-X/submodules/dumpi_to_graph/config/dumpi_and_csmpi.json . >& dumpi_to_graph_output.txt
