# oc_source.py

from oc_utils import Config, UserException, ProgramException, case_filename
from oc_parse import SrcFile
from oc_state import State
from shutil import copyfile
from oc_loopunroll import loop_unroll
from oc_loopmerge import loop_merge
from oc_loopsplit import loop_split
from oc_loopinterchange import loop_interchange
from oc_namechange import name_change
from oc_openmp import openmp
from oc_insertstmt import insert_stmt
from oc_removestmt import remove_stmt
from oc_promote import promote
from oc_directive import directive

def flat_items(items):
    if isinstance(items[0], str):
            return [ SrcFile.applymap(t) for t in items ]
    elif isinstance(items[0], tuple):
            return [ SrcFile.applymap(t[0]) for t, _ in items]
    else: raise ProgramException('Unknown type: %s'%items[0].__class__)

def generate_source(casenum, srcgens):
    srcfileids = []

    # handle insert_stmt first
    for srcgen, inputfileid, stmt, span in srcgens:
        for gentype, attrs in srcgen:
            if gentype[0].lower()=='insert_stmt':
                if inputfileid not in srcfileids:
                    srcfileids.append(inputfileid)
                if len(gentype)>1:
                    raise ProgramException('More than one gentype: %s'%gentype)
                transform_source(gentype[0], attrs, State.inputfile[inputfileid], stmt, span)

    # non insert_stmt type
    for srcgen, inputfileid, stmt, span in srcgens:
        for gentype, attrs in srcgen:
            if not gentype[0].lower()=='insert_stmt':
                if inputfileid not in srcfileids:
                    srcfileids.append(inputfileid)
                if len(gentype)>1:
                    raise ProgramException('More than one gentype: %s'%gentype)
                transform_source(gentype[0], attrs, State.inputfile[inputfileid], stmt, span)

    for srcfileid in srcfileids:
        #relpath = case_filename(State.inputfile[srcfileid].relpath, casenum)
        State.inputfile[srcfileid].write_to_file(Config.path['workdir']+'/'+State.inputfile[srcfileid].relpath)

    return srcfileids

def transform_source(gentype, attrs, inputfile, stmt, span):
    if gentype.lower()=='loop_unroll':
        if attrs.has_key('target') and len(attrs['target'])>0:
            _targets = flat_items(attrs['target'])
            targets = inputfile.get_stmt(_targets)
            if targets:
                factor = flat_items(attrs.get('factor', ['']))
                if len(factor)>1: raise ProgramException('More than one element: %s'%factor)
                method = flat_items(attrs.get('method', ['']))
                if len(method)>1: raise ProgramException('More than one element: %s'%method)

                loop_unroll(targets, factor[0], method[0])

    elif gentype.lower()=='loop_merge':
        if attrs.has_key('from') and len(attrs['from'])>0 and \
            attrs.has_key('to') and len(attrs['to'])>0:
            _from = flat_items(attrs['from'])
            _to = flat_items(attrs['to'])
            from_stmts = inputfile.get_stmt(_from)
            to_stmts = inputfile.get_stmt(_to)

            if from_stmts and to_stmts:
                loop_merge(from_stmts, to_stmts)

    elif gentype.lower()=='loop_split':
        if attrs.has_key('add_stmt') and len(attrs['add_stmt'])>0:
            add_stmt = flat_items(attrs['add_stmt'])
        else:
            add_stmt = None

        if attrs.has_key('before') and len(attrs['before'])>0:
            _before = flat_items(attrs['before'])
            before_stmts = inputfile.get_stmt(_before)

            if before_stmts and before_stmts:
                loop_split(before_stmts, add_stmt=add_stmt, before=True)
        elif attrs.has_key('after') and len(attrs['after'])>0:
            _after = flat_items(attrs['after'])
            after_stmts = inputfile.get_stmt(_after)

            if after_stmts and after_stmts:
                loop_split(after_stmts, add_stmt=add_stmt, before=False)

    elif gentype.lower()=='loop_interchange':
        if attrs.has_key('outer') and len(attrs['outer'])>0 and \
            attrs.has_key('inner') and len(attrs['inner'])>0:
            _outer = flat_items(attrs['outer'])
            _inner = flat_items(attrs['inner'])
            outer_stmts = inputfile.get_stmt(_outer)
            inner_stmts = inputfile.get_stmt(_inner)

            if outer_stmts and inner_stmts:
                loop_interchange(outer_stmts, inner_stmts)

    elif gentype.lower()=='name_change':
        if attrs.has_key('target') and len(attrs['target'])>0:
            _targets = flat_items(attrs['target'])
            targets = inputfile.get_stmt(_targets)
            if targets:
                switch = flat_items(attrs.get('switch', ['']))
                rename = flat_items(attrs.get('rename', ['']))

                name_change(targets, switch, rename)

    elif gentype.lower()=='openmp':
        if attrs.has_key('sentinel') and len(attrs['sentinel'])>0 and \
            attrs.has_key('directive') and len(attrs['directive'])>0:
            _sentinel = attrs.get('sentinel', None)
            if _sentinel: sentinel = flat_items(_sentinel)
            else: sentinel = None
            _direct = attrs.get('directive', None)
            if _direct: direct = flat_items(_direct)
            else: direct = None
            _clauses = attrs.get('clauses', None)
            if _clauses: clauses = flat_items(_clauses)
            else: clauses = None
            
            openmp(inputfile, stmt, sentinel, direct, clauses, span)

    elif gentype.lower()=='insert_stmt':
        if attrs.has_key('label') and len(attrs['label'])>0 and \
            attrs.has_key('stmt') and len(attrs['stmt'])>0:
            _label = attrs.get('label', None)
            if _label: label = flat_items(_label)
            else: label = None
            _stmt = attrs.get('stmt', None)
            if _stmt: stmt_line = flat_items(_stmt)
            else: stmt_line = None
            
            insert_stmt(inputfile, stmt, label, stmt_line, span)

    elif gentype.lower()=='remove_stmt':
        if attrs.has_key('target') and len(attrs['target'])>0:
            _targets = flat_items(attrs['target'])
            targets = inputfile.get_stmt(_targets)
            if targets:
                remove_stmt(inputfile, stmt, targets, span)

    elif gentype.lower()=='promote':
        if attrs.has_key('name') and len(attrs['name'])>0 and \
            attrs.has_key('dimension') and len(attrs['dimension'])>0 and \
            attrs.has_key('target') and len(attrs['target'])>0:
            _name = attrs.get('name', None)
            if _name: name = flat_items(_name)
            else: name = None
            _dimension = attrs.get('dimension', None)
            if _dimension: dimension = flat_items(_dimension)
            else: dimension = None
            _target = attrs.get('target', None)
            if _target: target = flat_items(_target)
            else: target = None
            _allocate = attrs.get('allocate', None)
            if _allocate: allocate = flat_items(_allocate)
            else: allocate = None
           
            promote(inputfile, stmt, name, dimension, target, allocate, span)

    elif gentype.lower()=='directive':
        if attrs.has_key('label') and len(attrs['label'])>0 and \
            attrs.has_key('sentinel') and len(attrs['sentinel'])>0 and \
            attrs.has_key('directive') and len(attrs['directive'])>0:
            _label = attrs.get('label', None)
            if _label: label = flat_items(_label)
            else: label = None
            _sentinel = attrs.get('sentinel', None)
            if _sentinel: sentinel = flat_items(_sentinel)
            else: sentinel = None
            _direct = attrs.get('directive', None)
            if _direct: direct = flat_items(_direct)
            else: direct = None
            
            directive(inputfile, stmt, label, sentinel, direct, span)

    else: raise UserException('Not implemented: %s'%gentype)

