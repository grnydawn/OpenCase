# oc_loopinterchange.py

from oc_utils import insert_content, Logger
from block_statements import Do
from api import parse, walk

def loop_interchange(outer_stmts, inner_stmts):

    for outer_stmt in outer_stmts:

        if not isinstance(outer_stmt, Do):
            Logger.warn('Outer statment is not Do type: %s'%outer_stmt.__class__)
            continue

        for inner_stmt in inner_stmts:
            if not isinstance(inner_stmt, Do):
                Logger.warn('Inner statment is not Do type: %s'%inner_stmt.__class__)
                continue

            lines = []
            for stmt, depth in walk(outer_stmt, -1):
                if stmt is outer_stmt:
                    lines.append(inner_stmt.tooc())
                elif stmt is inner_stmt:
                    lines.append(outer_stmt.tooc())
                elif stmt is inner_stmt.content[-1]:
                    lines.append(outer_stmt.content[-1].tooc())
                elif stmt is outer_stmt.content[-1]:
                    lines.append(inner_stmt.content[-1].tooc())
                else:
                    lines.append(stmt.tooc())

            if lines:
                parsed = parse('\n'.join(lines), analyze=False)
                if len(parsed.content)>0:
                    parsed.content[0].parent = outer_stmt.parent
                    for stmt, depth in walk(parsed, -1): stmt.parse_f2003() 
                    insert_content(outer_stmt, parsed.content)

