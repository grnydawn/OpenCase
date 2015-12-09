# oc_namesearch.py

from oc_utils import Config, Logger, show_tree
import Fortran2003
from typedecl_statements import TypeDeclarationStatement
from block_statements import Type, TypeDecl, Function, Subroutine, Interface
from oc_extra import Intrinsic_Procedures

res_default = [ TypeDeclarationStatement ]
res_typedecl = [ TypeDeclarationStatement ]
res_derivedtype = [ Type, TypeDecl ] 
res_kind = [ TypeDeclarationStatement ] + res_derivedtype
res_typespec = [ TypeDeclarationStatement ] + res_derivedtype
res_value = [ TypeDeclarationStatement, Function, Interface ]
res_subroutine = [ Subroutine, Interface ]
res_function = [ Function, Interface ]
res_subprogram = [ Subroutine, Function, Interface ]
res_anything = res_typespec + res_subprogram

###############################################################################
################################### COMMON ####################################
###############################################################################

def is_except(name, stmt):
    if not name or not stmt: return False

    namelist = [a.name for a in stmt.ancestors()]
    namelist.append(name.string.lower())
    exceptlist = Config.search['except']

    for elist in exceptlist:
        elist_split = elist.split('.')
        same = True
        for i in range(min(len(namelist), len(elist_split))-1,-1,-1):
            if namelist[i]!=elist_split[i]:
                same = False
                break
        if same: return True

    return False

def f2003_search_unknowns(stmt, node, resolvers=None):
    if node is None: return

    # save in unknowns dict in stmt
    if not hasattr(stmt, 'unknowns'):
        stmt.unknowns = {}

    clsname = node.__class__.__name__

    if clsname=='Name':
        get_name(stmt, node, resolvers)
        return

    if clsname.endswith('_List'):
        _clsname = clsname[:-5]
        for item in node.items:
            if item is None: continue
            itemclsname = item.__class__.__name__
            if itemclsname=='Name':
                get_name(stmt, item, resolvers)
            else:
                exec('search_%s(stmt, item)' % itemclsname)
    elif clsname.startswith('End_'):
        pass
    else:
        exec('search_%s(stmt, node)' % clsname)

def get_name_or_defer(stmt, node, resolvers, defer=True):
    from oc_utils import OCName, pathname
    from oc_state import ResState

    if node is None: return

    if isinstance(node, Fortran2003.Name):
        # skip if intrinsic
        if node.string.lower() in Intrinsic_Procedures:
            if  Config.search['skip_intrinsic'] and not is_except(node, stmt):return
            elif not Config.search['skip_intrinsic'] and is_except(node, stmt): return

        ukey = OCName(pathname(stmt, node.string.lower()), node=node, stmt=stmt)

        if resolvers is None:
            stmt.unknowns[ukey] = ResState(ukey, stmt, res_default)
        else:
            stmt.unknowns[ukey] = ResState(ukey, stmt, resolvers)
        Logger.info('%s is saved as unknown' % node.string.lower(), name=ukey, stmt=stmt)

    elif defer:
        f2003_search_unknowns(stmt, node, resolvers)

def get_name(stmt, node, resolvers):
    get_name_or_defer(stmt, node, resolvers, defer=False)

def defer(stmt, node):
    if isinstance(node, Fortran2003.Name):
        raise Exception('%s can not be Name class' % str(node))
    f2003_search_unknowns(stmt, node)


def defer_items(stmt, node):
    if hasattr(node, 'items'):
        for item in node.items:
            if isinstance(item, Fortran2003.Name):
                raise Exception('%s can not be Name class' % str(item))
            f2003_search_unknowns(stmt, item)

###############################################################################
################################### SEARCH ####################################
###############################################################################

def search_Type_Declaration_Stmt(stmt, node):  
    defer_items(stmt, node)

def search_Intrinsic_Type_Spec(stmt, node): 
    defer(stmt, node.items[1])

def search_Kind_Selector(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_kind)

def search_Entity_Decl(stmt, node): 
    defer(stmt, node.items[1])
    get_name_or_defer(stmt, node.items[2], res_value)
    get_name_or_defer(stmt, node.items[3], res_value) 

def search_Explicit_Shape_Spec(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Dimension_Attr_Spec(stmt, node): 
    defer(stmt, node.items[1])

def search_Add_Operand(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[2], res_value)

def search_Mult_Operand(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[2], res_value)

def search_Attr_Spec(stmt, node): 
    defer_items(stmt, node)

def search_Initialization(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Part_Ref(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value) 
    get_name_or_defer(stmt, node.items[1], res_value) 

def search_Structure_Constructor_2(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Int_Literal_Constant(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_typedecl)

def search_Real_Literal_Constant(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_typedecl)

def search_Subroutine_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[3], res_typedecl)

def search_Comment(stmt, node): 
    pass

def search_Nonlabel_Do_Stmt(stmt, node): 
    if len(node.items)==3:
        defer(stmt, node.items[2])
    elif len(node.items)==2:
        if isinstance(node.items[0], str):
            defer(stmt, node.items[1])

def search_Loop_Control(stmt, node): 
    if len(node.items)==1:
        defer(stmt, node.items[0])
    else:
        get_name_or_defer(stmt, node.items[0], res_typedecl)
        if isinstance(node.items[1], list):
            for item in node.items[1]:
                get_name_or_defer(stmt, item, res_value)
        else:
            defer(stmt, node.items[1])

def search_Assignment_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_typedecl)
    get_name_or_defer(stmt, node.items[2], res_value)

def search_Level_2_Expr(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[2], res_value)

def search_Parenthesis(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_value)

def search_str(stmt, string):
    pass

def search_Function_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_derivedtype )
    get_name_or_defer(stmt, node.items[3], res_typedecl)

def search_Assumed_Shape_Spec(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Allocate_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_typespec)
    get_name_or_defer(stmt, node.items[1], res_typedecl)
    defer(stmt, node.items[2])

def search_Allocation(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_typedecl)
    if len(node.items)>1:
        defer_items(stmt, node.items[1:])

def search_Use_Stmt(stmt, node): 
    pass

def search_If_Then_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)

def search_Level_4_Expr(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[2], res_value)

def search_If_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Else_If_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Else_Stmt(stmt, node): 
    pass

def search_Level_2_Unary_Expr(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_value)


def search_Label_Do_Stmt(stmt, node): 
    defer(stmt, node.items[2])

def search_Array_Constructor(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_value) 

def search_Array_Section(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    defer(stmt, node.items[1])

def search_Substring_Range(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Select_Case_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)

def search_Case_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)

def search_Case_Selector(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)

def search_Call_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_subroutine)
    if isinstance(node.items[1], Fortran2003.Name):
        get_name_or_defer(stmt, node.items[1], res_value)
    else:
        defer(stmt, node.items[1])

def search_Char_Literal_Constant(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_typedecl)

def search_Length_Selector(stmt, node): 
    for item in node.items:
        get_name_or_defer(stmt, item, res_value)

def search_Type_Param_Value(stmt, node): 
    # NOTE: need to verify its content structure
    if node.item:
        get_name_or_defer(stmt, node.item, res_value)

def search_Write_Stmt(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Io_Control_Spec(stmt, node): 
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Stop_Stmt(stmt, node): 
    pass

def search_Contains_Stmt(stmt, node): 
    pass

def search_Subscript_Triplet(stmt, node): 
    get_name_or_defer(stmt, node.items[0], res_value) 
    get_name_or_defer(stmt, node.items[1], res_value) 
    get_name_or_defer(stmt, node.items[2], res_value) 

def search_Interface_Stmt(stmt, node):
    pass

def search_Procedure_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_subprogram)

def search_Prefix(stmt, node):
    for item in node.items:
        get_name_or_defer(stmt, node.items[0], res_anything)

def search_Prefix_Spec(stmt, node):
    if node.item or hasattr(node, 'items'):
        raise ProgramException('Unexpected item or items attr')

def search_Logical_Literal_Constant(stmt, node):
    get_name_or_defer(stmt, node.items[1], res_typedecl)

def search_Access_Spec(stmt, node):
    pass

def search_And_Operand(stmt, node):
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Equiv_Operand(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[2], res_value)

def search_Or_Operand(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[2], res_value)


def search_Where_Construct_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_value)

def search_Elsewhere_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Suffix(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Declaration_Type_Spec(stmt, node):
    get_name_or_defer(stmt, node.items[1], res_derivedtype)

def search_Data_Ref(stmt, node):
    from oc_utils import OCName
    from Fortran2003 import Name, Part_Ref

    parent = stmt.ancestors()[-1]
    if not hasattr(parent, 'datarefs'):
        parent.datarefs = []
    kgname = OCName(str(node))
    parent.datarefs.append(kgname)

    get_name_or_defer(stmt, node.items[0], res_value)

    for item in node.items[1:]:
        if isinstance(item, Name): pass
        elif isinstance(item, Part_Ref):
            get_name_or_defer(stmt, item.items[1], res_value)
        elif item is None: pass
        else: raise ProgramException('Unknown type: %s'%item.__class)

def search_Structure_Constructor(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_derivedtype)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Binary_Constant(stmt, node):
    pass

def search_Octal_Constant(stmt, node):
    pass

def search_Hex_Constant(stmt, node):
    pass

def search_Intrinsic_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[1], res_subprogram)

def search_Derived_Type_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[2], res_value)

def search_Access_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[1], res_anything)

def search_Function_Reference(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_function)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Return_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_function)

def search_Print_Stmt(stmt, node):
    get_name_or_defer(stmt, node.items[0], res_value)
    get_name_or_defer(stmt, node.items[1], res_value)

def search_Format(stmt, node):
    if hasattr(node, 'items') and len(node.items)>0:
        get_name_or_defer(stmt, node.items[0], res_value)
