KGEN_HOME := /glade/u/home/dennis/software/KGen/kgen
KGEN := $(KGEN_HOME)/kgen.py

SRC := /glade/p/work/dennis/cesm/cesm1_4_beta07/components/cam/src/physics/cam/micro_mg_cam.F90
OUTPUT_DIR := /glade/p/work/dennis/generate-kernels/MG2r

test:
	python ${KGEN} \
		-i ./include.ini \
		--outdir ${OUTPUT_DIR} \
		--invocation 1 \
		--mpi ranks=0,header=/ncar/opt/intel/psxe-2015_update3/impi/5.0.3.048/intel64/include/mpif.h \
		--kernel-compile FC=ifort,FC_FLAGS=' -O2 -fp-model source -convert big_endian -assume byterecl -ftz -traceback -assume realloc_lhs  -xAVX' \
		${SRC}

#		${SRC}:atm_time_integration.atm_srk3.atm_recover_large_step_variables
#		${SRC}:atm_time_integration.atm_srk3.atm_compute_dyn_tend
#		${SRC}:atm_time_integration.atm_srk3.atm_set_smlstep_pert_variables
#		${SRC}:atm_time_integration.atm_srk3.atm_advance_scalars

#		--state-build cmds="cd ${RRTMG_HOME};./buildRrtmg.sh -b" \
#		--state-run cmds="cd ${RRTMG_HOME};module load intel/15.0.3;bsub < runRrtmg.sh" \
