# Makefile for dg_kernel

FC ?= gfortran
FC_FLAGS ?= -O3 -fopenmp -ffree-line-length-none

run:
	./dg_kernel.exe

build: dg_kernel.F90
	@${FC} ${FC_FLAGS} -o dg_kernel.exe $<

clean:
	rm -rf *.exe *.o *.mod
