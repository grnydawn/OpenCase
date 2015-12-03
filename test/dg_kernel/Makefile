# Makefile for dg_kernel

FC ?= gfortran
FC_FLAGS ?= -O3 -fopenmp -ffree-line-length-none

OC := ../../src/opencase.py
PWD := $(shell pwd)
WORKDIR := ${PWD}/work
OUTDIR := ${PWD}/output
SRC := dg_kernel.F90

test: 
	python ${OC} \
		--workdir ${WORKDIR} \
		--outdir ${OUTDIR} \
		--timeout 10m \
		--debug logging.select.name=grad_term_gpu.nelem \
		${SRC}
