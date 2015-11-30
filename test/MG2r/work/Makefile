# Makefile for mg2

FC ?= ifort
FC_FLAGS ?= -O3 -fopenmp -ffree-line-length-none

OC := ../../../src/opencase.py
PWD := $(shell pwd)
WORKDIR := ${PWD}/work
OUTDIR := ${PWD}/output
REFDIR := ${PWD}/org
SRC := ${REFDIR}/micro_mg2_0.F90

test: 
	python ${OC} \
		--workdir ${WORKDIR} \
		--refdir ${REFDIR} \
		--outdir ${OUTDIR} \
		--timeout 10m \
		${SRC}

copy: ${SRC}.oc_org
	cp -f ${SRC}.oc_org ${SRC}


