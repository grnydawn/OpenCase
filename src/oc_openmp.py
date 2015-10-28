# oc_namechange.py

from oc_parse import SrcFile
from oc_utils import insert_content
from api import parse, walk

def openmp(inputfile, target_stmt, sentinel, directive, clauses, span):

    line = ''
    new_target_stmt = None
    for stmt, depth in walk(inputfile.tree, -1):
        if stmt.item.span==span:
            new_target_stmt = stmt
            if clauses:
                mapped_clauses = SrcFile.applymap(clauses[0])                
            else:
                mapped_clauses = ''
            line = '%s %s %s'%(SrcFile.applymap(sentinel[0]), SrcFile.applymap(directive[0]), mapped_clauses)
            break

    if line:
        parsed = parse(line, analyze=False, ignore_comments=False)
        if len(parsed.content)>0:
            #parsed.content[0].parent = target_stmt.parent
            #import pdb; pdb.set_trace()
            for stmt, depth in walk(parsed, -1): stmt.parse_f2003()
            insert_content(new_target_stmt, parsed.content, remove_olditem=True)
