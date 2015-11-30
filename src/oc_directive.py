# oc_directive.py

from oc_parse import SrcFile
from oc_utils import insert_content
from api import parse, walk
from statements import Comment

def directive(inputfile, target_stmt, label, sentinel, directive, span):

    line = ''
    new_target_stmt = None
    for stmt, depth in walk(inputfile.tree, -1):
        if stmt.item.span==span:
            new_target_stmt = stmt
            line = '!%s$ %s'%(SrcFile.applymap(sentinel[0]), SrcFile.applymap(directive[0]))
            break

    if line:
        parsed = parse(line, analyze=False, ignore_comments=False)
        if len(parsed.content)>0:
            for stmt, depth in walk(parsed, 1):
                if isinstance(stmt, Comment):
                    stmt.label = int(label[0])
                else:
                    stmt.item.label = int(label[0])
                stmt.parse_f2003()

            insert_content(new_target_stmt, parsed.content, remove_olditem=True)
