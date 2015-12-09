# oc_loopmerge.py

from oc_utils import insert_content, remove_content, Logger
from block_statements import Do
from Fortran2003 import Nonlabel_Do_Stmt, Int_Literal_Constant

def loop_merge(from_stmts, to_stmts):

    for from_stmt in from_stmts:

        if not isinstance(from_stmt, Do):
            Logger.warn('From statment is not Do type: %s'%from_stmt.__class__)
            continue

        from_f2003 = from_stmt.f2003
        if isinstance(from_f2003, Nonlabel_Do_Stmt):
            from_loop_control = from_f2003.items[1]
            from_loop_var = from_loop_control.items[0].string.lower()
            from_start_idx = from_loop_control.items[1][0]
            from_end_idx = from_loop_control.items[1][1]
            if len(from_loop_control.items[1])==3:
                from_step = Int_Literal_Constant(str(1))
            else:
                from_step = loop_control.items[1][2]
        else: raise ProgramException('Not supported type: %s'%from_f2003.__class__)

        # collect loop controls through static analysis
        from_start_num = from_stmt.get_param(from_start_idx)
        from_end_num = from_stmt.get_param(from_end_idx)
        from_step_num = from_stmt.get_param(from_step)
        try: from_loop_indices = range(from_start_num, from_end_num+1, from_step_num)
        except: from_loop_indices = None

        for to_stmt in to_stmts:
            if not isinstance(to_stmt, Do):
                Logger.warn('To statment is not Do type: %s'%to_stmt.__class__)
                continue

            to_f2003 = to_stmt.f2003
            if isinstance(to_f2003, Nonlabel_Do_Stmt):
                to_loop_control = to_f2003.items[1]
                to_loop_var = to_loop_control.items[0].string.lower()
                to_start_idx = to_loop_control.items[1][0]
                to_end_idx = to_loop_control.items[1][1]
                if len(to_loop_control.items[1])==3:
                    to_step = Int_Literal_Constant(str(1))
                else:
                    to_step = to_loop_control.items[1][2]
            else: raise ProgramException('Not supported type: %s'%to_f2003.__class__)

            # collect loop controls through static analysis
            to_start_num = to_stmt.get_param(to_start_idx)
            to_end_num = to_stmt.get_param(to_end_idx)
            to_step_num = to_stmt.get_param(to_step)
            try: to_loop_indices = range(to_start_num, to_end_num+1, to_step_num)
            except: to_loop_indices = None


            if ( from_loop_indices and to_loop_indices and from_loop_indices==to_loop_indices ) or \
                ( from_loop_indices is None and to_loop_indices is None and from_loop_var==to_loop_var and \
                from_start_idx==to_start_idx and from_end_idx==to_end_idx and from_step==to_step ):

                insert_content(to_stmt.content[-1], from_stmt.content[:-1], remove_olditem=False)
                remove_content(from_stmt)
            else:
                Logger.warn('Can not merge due to different loop control')

