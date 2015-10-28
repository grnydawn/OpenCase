# Makefile for dg_kernel

FC ?= gfortran
FC_FLAGS ?= -O3 -fopenmp -ffree-line-length-none

OC := ${HOME}/trepo/study/opencase/src/opencase.py
WORKDIR := `pwd`
OUTDIR := ${HOME}/trepo/temp/opencase/dg_kernel
SRC := dg_kernel.F90

test:
	python ${OC} \
		--workdir ${WORKDIR} \
		--outdir ${OUTDIR} \
		--timeout 2m \
		--debug logging.select.name=grad_term_gpu.nelem \
		${SRC}

run:
	./dg_kernel.exe

build: dg_kernel.F90
	@${FC} ${FC_FLAGS} -o dg_kernel.exe $<

recover: dg_kernel.F90.oc_org
	rm -f dg_kernel.F90
	ln -s $< dg_kernel.F90

ref_recover: ref_dg_kernel.F90
	rm -f dg_kernel.F90
	ln -s $< dg_kernel.F90

clean:
	rm -rf *.exe *.o *.mod
