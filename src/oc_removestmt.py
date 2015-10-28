# oc_removestmt.py

from oc_parse import SrcFile
from oc_utils import insert_content
from api import parse, walk

def remove_stmt(inputfile, target_stmt, targets, span):
    for target in targets:
        if target:
            parsed = parse('!'+str(target), analyze=False, ignore_comments=False)
            if len(parsed.content)>0:
                for stmt, depth in walk(parsed, 1):
                    stmt.parse_f2003()
                insert_content(target, parsed.content, remove_olditem=True)
