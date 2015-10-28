# oc_promote.py

from oc_parse import SrcFile
from oc_utils import insert_content
from api import parse, walk
from statements import Comment
from block_statements import execution_part
from typedecl_statements import TypeDeclarationStatement

def promote(inputfile, target_stmt, names, dimensions, targets, allocate, span):

    for target in targets:
        for promote_pair in target.split(','):
            label, idxname = promote_pair.split(':')
            promote_stmt = inputfile.get_stmt(label)
            if promote_stmt:
                lines = []
                in_exepart = False
                for stmt, depth in walk(promote_stmt[0], -1):
                    if isinstance(stmt, TypeDeclarationStatement):
                        org_attrspec = stmt.attrspec
                        if any( [ name in stmt.entity_decls for name in names ] ):
                            entity_decls = []
                            name_decls = [] 
                            attrspec = stmt.attrspec
                            for entity in stmt.entity_decls:
                                if entity in names:
                                    name_decls.append(entity)
                                else:
                                    entity_decls.append(entity)
                            if len(stmt.entity_decls)>0:
                                stmt.entity_decls = entity_decls 
                                lines.append(stmt.tooc())
                            if allocate:
                                if 'allocatable' not in stmt.attrspec:
                                    stmt.attrspec.append('allocatable')
                                stmt.entity_decls = [ name_decl+dimensions[0] for name_decl in name_decls ]
                            else:
                                stmt.entity_decls = [ name_decl+allocate[0] for name_decl in name_decls ]
                            if len(stmt.entity_decls)>0:
                                lines.append(stmt.tooc())
                                stmt.entity_decls = entity_decls
                        else:
                            if len(stmt.entity_decls)>0:
                                lines.append(stmt.tooc())
                    elif not in_exepart and stmt.__class__ in execution_part:
                        renames = []
                        for name in names:
                            for dim in dimensions:
                                if allocate:
                                    lines.append('allocate(%s)'%(name+allocate[0]))
                                renames.append([name, name+idxname])
                        lines.append(stmt.tooc(name_rename=renames))
                        in_exepart = True
                    elif in_exepart:
                        renames = []
                        for name in names:
                            for dim in dimensions:
                                renames.append([name, name+idxname])
                        lines.append(stmt.tooc(name_rename=renames))
                    else:
                        lines.append(stmt.tooc())

                try:
                    parsed = parse('\n'.join(lines), analyze=False, ignore_comments=False)
                    if len(parsed.content)>0:
                        for stmt, depth in walk(parsed, -1): stmt.parse_f2003()
                        insert_content(promote_stmt[0], parsed.content, remove_olditem=True)                       
                except: pass

