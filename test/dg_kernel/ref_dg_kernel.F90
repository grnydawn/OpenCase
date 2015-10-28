!$opencase INCLUDE(cases.inc)

      Program Grad_Term_GPU
      use omp_lib

      Implicit None

      Integer, Parameter :: double=Selected_Real_Kind(p=14,r=100)

      Integer, Parameter :: nx=4      ! element order
      Integer, Parameter :: npts=nx*nx
      !Integer npts
      !parameter (npts=nx*nx)
      Integer, Parameter :: nel=50 ! was20    ! number of elements 
      Integer, Parameter :: nit=100   ! iteration count
      Integer, Parameter :: nelem=6*nel*nel
 
      Real(Kind=double), Parameter :: dt=.005D0 ! fake timestep
   
      Real(Kind=double) :: der(nx,nx)   ! Derivative matrix
      Real(Kind=double) :: delta(nx,nx) ! Kronecker delta function
      Real(Kind=double) :: gw(nx)       ! Gaussian wts
      Real(Kind=double) :: wl(nx)       ! element width
      Real(Kind=double), Dimension(nx*nx,nelem) :: flx,fly 
      Real(Kind=double), Dimension(nx*nx,nelem) :: grad     

      Real(Kind=double) :: s1, s2, a, b
      Real(Kind=double) :: zero, half, one
      Real(Kind=double) :: start_time, stop_time, elapsed_time

      Integer :: i, j, k, l, ii, ie, it

      zero = 0.0_double
      half = 0.5_double
      one = 1.0_double

      ! Init static matrices

      der(:,:)=one
      gw(:) = half
      wl(:) = half

      delta(:,:)=zero
      delta(1,1)=one
      delta(2,2)=one

      ! Load up some initial values

      flx(:,:) = one
      fly(:,:) = -one

      start_time = omp_get_wtime()


      do it=1,nit
!$omp parallel shared(flx,fly,grad)
!$omp do
30       do ie=1,nelem
40         do ii=1,npts
50            k=MODULO(ii-1,nx)+1
60            l=(ii-1)/nx+1
70            s2 = zero
80            do j = 1, nx
90               s1 = zero
100               do i = 1, nx
110                  s1 = s1 + (delta(l,j)*flx(i+(j-1)*nx,ie)*der(i,k) + delta(i,k)*fly(i+(j-1)*nx,ie)*der(j,l))*gw(i)
120               end do
130               s2 = s2 + s1*gw(j) 
140            end do
150            grad(ii,ie) = s2
160         end do
170      end do
!$omp end do
!$omp end parallel

!$omp parallel shared(flx,fly,grad)
!$omp do
220      do ie=1,nelem
230         do ii=1,npts
240            flx(ii,ie) = flx(ii,ie)+ dt*grad(ii,ie)
250            fly(ii,ie) = fly(ii,ie)+ dt*grad(ii,ie)
260         end do
270      end do
!$omp end do
!$omp end parallel

      end do

      stop_time = omp_get_wtime()

      elapsed_time = stop_time - start_time

        WRITE(*, *) "****************** RESULT ********************"
        WRITE(*, *)
        WRITE(*, "(A,I2,A,I2,A)") "DG_KERNEL VERSION (",0," ,",0," )"
        WRITE(*, *)
        WRITE(*, "(A, I1,A,I2,A,I10,A,I8)")  "TARGET = ",0,", NX = ",nx,", NELEM = ",nelem,", NIT = ", nit
        WRITE(*, "(A,E15.7)") "MAX(flx) = ", MAXVAL(flx)
        WRITE(*, "(A,E15.7)") "MIN(fly) = ", MINVAL(fly)
        WRITE(*, "(A,E15.7)") "SUM(flx) = ", SUM(flx(:10,1))
        WRITE(*, "(A,F7.2)") "Gflops   = ",(1.0d-9*nit*nelem*npts*(nx*nx*7.D0+2.D0*nx+4.0D0))/elapsed_time
        WRITE(*, "(A,F10.3,A)") 'completed in ', elapsed_time, ' seconds'

      End Program Grad_Term_GPU

