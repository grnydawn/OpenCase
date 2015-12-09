# oc_namechange.py

from oc_utils import insert_content
from api import parse, walk

def name_change(targets, switch, rename):

    for target_stmt in targets:
        list_switch = [ (pair.split(':')[0].strip(),  pair.split(':')[1].strip()) for pair in switch  if pair]
        list_rename = [ (pair.split(':')[0].strip(),  pair.split(':')[1].strip()) for pair in rename  if pair]
        lines = target_stmt.tooc(name_switch=list_switch, name_rename=list_rename)

        if lines:
            parsed = parse(lines, analyze=False)
            if len(parsed.content)>0:
                parsed.content[0].parent = target_stmt.parent
                for stmt, depth in walk(parsed, -1): stmt.parse_f2003()
                insert_content(target_stmt, parsed.content, remove_olditem=True)
