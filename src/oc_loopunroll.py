# oc_loopunroll.py

from oc_utils import Logger, ProgramException, UserException, show_tree, insert_content
from block_statements import Do, EndStatement
from Fortran2003 import Nonlabel_Do_Stmt, Int_Literal_Constant
from api import parse, walk

def _unroll(content, loop_var, factor, method, start_index=None):
    lines = []

    stmts = content
    if isinstance(content[-1], EndStatement):
        stmts = content[:-1]

    if method=='inc':
        if start_index:
            lines.append('%s = %d'%(loop_var, start_index))
        remove_label = False
        for i in range(factor):
            for stmt in stmts:
                lines.append(stmt.tooc(remove_label=remove_label))
            remove_label = True
            if i<factor-1:
                lines.append('%s = %s + 1'%(loop_var, loop_var))

    elif method=='const':
        if start_index:
            lines.append('%s = %d'%(loop_var, start_index))
        for i in range(factor):
            for stmt in stmts:
                lines.append(stmt.tooc(name_rename=[(loop_var, '%s+%d'%(loop_var, i))], remove_label=True))
    else: raise UserException('Unknown unroll method: %s'%method)

    return lines
    
def loop_unroll(targets, factor, method):
    for target_stmt in targets:
        if not isinstance(target_stmt, Do):
            Logger.warn('Target statment is not Do type: %s'%target_stmt.__class__)
            continue

        # collect loop control
        target_f2003 = target_stmt.f2003
        if isinstance(target_f2003, Nonlabel_Do_Stmt):
            loop_control = target_f2003.items[1]
            loop_var = loop_control.items[0].string.lower()
            start_idx = loop_control.items[1][0]
            end_idx = loop_control.items[1][1]
            if len(loop_control.items[1])==3:
                step = Int_Literal_Constant(str(1))
            else:
                step = loop_control.items[1][2]
        else: raise ProgramException('Not supported type: %s'%f2003obj.__class__)

        # collect loop controls through static analysis
        start_num = target_stmt.get_param(start_idx)
        end_num = target_stmt.get_param(end_idx)
        step_num = target_stmt.get_param(step)
        try: loop_indices = range(start_num, end_num+1, step_num)
        except: loop_indices = None

        # TODO: modify analysis if required
        lines = []
        if factor=='full':
            if loop_indices is not None:
                lines = _unroll(target_stmt.content, loop_var, len(loop_indices), method, start_index=start_num)
            else:
                Logger.warn('Loopcontrol is not collected')

            # save in tree
        elif factor.isdigit():
            factor_num = int(factor)
            if loop_indices is not None and len(loop_indices)==factor_num:
                lines = _unroll(target_stmt.content, loop_var, factor_num, method, start_index=start_num)
            else:
                # replace end and step
                newstep = '%s*%s'%(step.tofortran(), factor)
                newend = '%s-%s'%(end_idx.tofortran(), newstep)
                lines.append(target_stmt.tooc(do_end=newend, do_step=newstep))
                lines.extend(_unroll(target_stmt.content, loop_var, factor_num, method))
                lines.append(target_stmt.content[-1].tooc())
            
                # replace start
                newstart = loop_var
                lines.append(target_stmt.tooc(do_start=newstart, remove_label=True))
                lines.extend(_unroll(target_stmt.content, loop_var, 1, method))
                lines.append(target_stmt.content[-1].tooc(remove_label=True))
        else: raise UserException('Unknown unroll factor: %s'%factor)

        if lines:
            parsed = parse('\n'.join(lines), analyze=False)
            if len(parsed.content)>0:
                for stmt, depth in walk(parsed, -1):
                    stmt.parse_f2003() 
                insert_content(target_stmt, parsed.content)
