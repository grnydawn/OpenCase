# oc_loopsplit.py

from oc_utils import insert_content, Logger
from block_statements import Do
from api import parse, walk

def loop_split(stmts, add_stmt, before=True):

    for stmt in stmts:
        parent = stmt.parent

        if not isinstance(parent, Do):
            Logger.warn('Parent of statment is not Do type: %s'%parent.__class__)
            continue

        doblk1 = []
        doblk2 = []

        #if add_stmt: doblk1.append(add_stmt[0])
        doblk1.append(parent.tooc())

        if add_stmt: doblk2.append(add_stmt[0])
        doblk2.append(parent.tooc(remove_label=True))

        enddo_stmt = parent.content[-1]

        doblk = doblk1
        remove_label = False
        for childstmt, depth in walk(parent, -1):
            if childstmt not in [ parent, enddo_stmt]:
                if not before:
                    doblk.append(childstmt.tooc(remove_label=remove_label))
                if childstmt==stmt:
                    doblk = doblk2
                    remove_label = True
                if before:
                    doblk.append(childstmt.tooc(remove_label=remove_label))
            
        doblk1.append(enddo_stmt.tooc())
        doblk2.append(enddo_stmt.tooc(remove_label=True))

        if doblk1:
            parsed = parse('\n'.join(doblk1), analyze=False, ignore_comments=False)
            if len(parsed.content)>0:
                parsed.content[0].parent = parent.parent
                for stmt, depth in walk(parsed, -1): stmt.parse_f2003()
                insert_content(parent, parsed.content, remove_olditem=False)

        if doblk2:
            parsed = parse('\n'.join(doblk2), analyze=False, ignore_comments=False)
            if len(parsed.content)>0:
                parsed.content[0].parent = parent.parent
                for stmt, depth in walk(parsed, -1): stmt.parse_f2003()
                insert_content(parent, parsed.content, remove_olditem=True)
