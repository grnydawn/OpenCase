# oc_extra.py

rdtsc = \
"""         .file   "rdtsc.s"
         .text
.globl rdtsc_
         .type   rdtsc_, @function
rdtsc_:
         rdtsc
         movl %eax,%ecx
         movl %edx,%eax
         shlq $32,%rax
         addq %rcx,%rax
         ret
         .size   rdtsc_, .-rdtsc_"""

Intrinsic_Procedures = [ \
# numeric functions \
'abs','aimag','aint','anint','ceiling','cmplx','conjg','dble','dim','dprod','floor','int','max','min','mod','modulo','nint','real','sign', \
# mathematical functions \
'acos','asin','atan','atan2','cos','cosh','exp','log','log10','sin','sinh','sqrt','tan','tanh', \
# character functions \
'achar','adjustl','adjustr','char','iachar','ichar','index','len_trim','lge','lgt','lle','llt','max','min','repeat','scan','trim','verify', \
# kind functions \
'kind','selected_char_kind','selected_int_kind','selected_real_kind', \
# miscellaneous type conversion functions \
'logical', 'transfer', \
# numeric inquiry functions \
'digits','epsilon','huge','maxexponent','minexponent','precision','radix','range','tiny', \
# array inquiry functions \
'lbound','shape','size','ubound', \
# other inquiry functions \
'allocated','associated','bit_size','extends_type_of','len','new_line','present','same_type_as', \
# bit manipulation procedures \
'btest','iand','ibclr','ibits','ibset','ieor','ior','ishft','ishftc','mvbits','not', \
# vector and matrix multiply functions \
'exponent','fraction','nearest','rrspacing','scale','set_exponent','spacing','dot_product','matmul', \
# array reduction functions \
'all' ,'any' ,'count' ,'maxval' ,'minval' ,'product' ,'sum', \
# array construction functions \
'cshift','eoshift','merge','pack','reshape','spread','transpose','unpack', \
# array location functions \
'maxloc','minloc', \
# null function \
'null', \
# allocation transfer procedure \
'move alloc', \
# random number subroutines \
'random_number','random_seed', \
# system environment procedures \
'command_argument_count','cpu_time','date_and_time','get_command','get_command_argument','get_environment_variable','is_iostat_end','is_iostat_eor','system_clock', \
# specific names \
'alog','alog10','amax0','amax1','amin0','amin1','amod','cabs','ccos','cexp','clog','csin','csqrt','dabs','dacos','dasin','datan','dcos','dcosh','ddim','dexp','dint','dlog','dlog10','dmax1','dmin1','dmod','dnint','dsign','dsin','dsinh','dsqrt','dtan','dtanh','float','iabs','idim','idint','idnint','ifix','isign','max0','max1','min0','min1' \
]
