# oc_parse.py 
from oc_utils import TAB, Config, Logger, ProgramException
from oc_state import State
from oc_casesearch import generate_searchtree
from api import parse, walk
from statements import Comment

global_directs = ['refcase', 'prerun', 'postrun', 'clean', 'build', 'execute', 'measure', 'verify', 'rank', 'casegen']
local_directs = ['srcgen']
spacegen_directs = [ 'srcgen', 'clean', 'build', 'prerun', 'postrun', 'execute', 'casegen' ]

class SrcFile(object):
    strmap = {}
    strmapid = 0

    def _strmap(self, line):
        cur_quote = ''
        is_inquote = False
        direct = ''
        quote = ''
        for c in line:
            if is_inquote:
                if c==cur_quote:
                    cur_quote = ''
                    is_inquote = False
                    strid = 'OC_STRMAP_%d'%self.strmapid
                    self.strmapid += 1
                    self.strmap[strid] = quote[:]
                    direct += strid
                    quote = ''
                else: quote += c
            else:
                if c=='"' or c=="'":
                    cur_quote = c
                    is_inquote = True
                else: direct += c

        return direct

    @classmethod
    def applymap(cls, obj):
        if obj is None: return

        newobj = None
        if isinstance(obj, str):
            newobj = obj[:]
            for key, value in cls.strmap.iteritems():
                newobj = newobj.replace(key, value)
        elif isinstance(obj, dict):
            newobj = {}
            for key, value in obj.iteritems():
                newobj[cls.applymap(key)] = cls.applymap(value)
        elif isinstance(obj, list):
            newobj = []
            for item in obj:
                newobj.append(cls.applymap(item))
        elif isinstance(obj, tuple):
            listobj = list(obj)
            newobj = tuple(cls.applymap(listobj))
        else: raise ProgramException('Unknonw type: %s'%obj.__class__)
        
        return newobj
 
    def __init__(self, srcpath):
        import re
        import os.path
        from oc_utils import exec_cmd

        # set default values
        self.prep = None
        self.tree = None
        self.srcpath = srcpath
        self.filename = os.path.basename(self.srcpath)
        self.abspath = os.path.abspath(self.srcpath)
        self.relpath = os.path.relpath(self.abspath, Config.path['refdir'])
        self.searchtree = []
        self.direct = {}

        # prepare include paths and macro definitions
        path_src = []
        macros_src = ''
        if Config.include['file'].has_key(self.abspath):
            path_src = Config.include['file'][self.abspath]['path']
            macros_src = ' '.join([ '-D%s=%s'%(k,v) for k, v in Config.include['file'][self.abspath]['macro'].iteritems() ])
        includes = '-I'+' -I'.join(Config.include['path']+path_src+['.'])
        macros = ' '.join([ '-D%s=%s'%(k,v) for k, v in Config.include['macro'].iteritems() ]) + ' ' + macros_src

        # execute preprocessing
        Logger.info('Reading %s'%self.srcpath, stdout=True)
        prep = Config.bin['pp']
        if prep.endswith('fpp'): flags = Config.bin['fpp_flags']
        elif prep.endswith('cpp'): flags = Config.bin['cpp_flags']
        else: raise UserException('Preprocessor is not either fpp or cpp')
        output = exec_cmd('%s %s %s %s %s' % (prep, flags, includes, macros, self.abspath))

        # convert the preprocessed for fparser
        self.prep = map(lambda l: '!__OPENCASE_COMMENT'+l if l.startswith('#') else l, output.split('\n'))

        # fparse
        self.tree = parse('\n'.join(self.prep), ignore_comments=False, analyze=True, isfree=True, isstrict=False, \
            include_dirs=None, source_only=None )

        # parse f2003
        lineno = 0
        linediff = 0
        pending_directs = []
        for stmt, depth in walk(self.tree, -1):
            if isinstance(stmt, Comment) and stmt.item.comment.startswith('!__OPENCASE_COMMENT#'):
                comment_split = stmt.item.comment.split(' ')
                lineno = int(comment_split[1])
                stmt.item.span = ( 0, 0 )
            else:
                if lineno>0:
                    linediff = stmt.item.span[0] - lineno
                    lineno = 0
                stmt.item.span = ( stmt.item.span[0]-linediff, stmt.item.span[1]-linediff )

                if isinstance(stmt, Comment): 
                    match = re.match(r'\$opencase\s*(\w+)\s*([\(\{\[\<])(.+)([\)\}\]\>]\s*\*?\+?\d?)', stmt.content, re.I)
                    if match:
                        name = match.group(1).lower()
                        value = match.group(3)
                        if name=='include':
                            if value:
                                casefile = value.strip()
                                if casefile[0]=='/':
                                    inc_path = os.path.abspath(casefile)
                                else:
                                    inc_path = os.path.join(os.path.dirname(self.abspath), value)
                                if os.path.exists(inc_path):
                                    finc = open(inc_path, 'r')
                                    inc_directs = re.findall(r'(\!?)\s*(\w+)\s*([\(\{\[\<])(.+)([\)\}\]\>]\s*\*?\+?\d?)\s*\n', finc.read(), re.I)
                                    finc.close()
                                    for direct in inc_directs:
                                        if direct[0]: continue
                                        direct_line = ''.join(direct)
                                        direct_name = direct[1].lower()

                                        direct_tree = generate_searchtree(self._strmap(direct_line))
                                        assert len(direct_tree)==1, 'Only one element is allowed in direct_tree'
                                        self.searchtree.extend(direct_tree)

                                        if direct_name in global_directs:
                                            if not State.direct.has_key(direct_name):
                                                State.direct[direct_name] = []
                                            State.direct[direct_name].append((direct_tree[0], stmt, stmt.item.span))
                                        elif direct_name in local_directs: 
                                            if not self.direct.has_key(direct_name):
                                                self.direct[direct_name] = []
                                            self.direct[direct_name].append((direct_tree[0], stmt, stmt.item.span))
                                else:
                                    raise UserException('Can not find caes file: %s'%inc_path)
                        else:
                            direct_line = match.group(0)
                            direct_tree = generate_searchtree(self._strmap(direct_line[10:]))
                            self.searchtree.extend(direct_tree)

                            if name in global_directs:
                                if not State.direct.has_key(name):
                                    State.direct[name] = []
                                State.direct[name].append((direct_tree[0], stmt, stmt.item.span))
                            elif name in local_directs: 
                                if not self.direct.has_key(name):
                                    self.direct[name] = []
                                self.direct[name].append((direct_tree[0], stmt, stmt.item.span))

                            #if match.group(1).lower() in ['refcase']:
                            #    State.direct[match.group(1).lower()] = direct_tree
            stmt.parse_f2003()

        # rename reader.id
        self.tree.reader.id = self.abspath

    def reset_parsing(self):
        # fparse
        readerid = self.tree.reader.id
        self.tree = parse('\n'.join(self.prep), ignore_comments=False, analyze=True, isfree=True, isstrict=False, \
            include_dirs=None, source_only=None )
        self.tree.reader.id = readerid

        # f2003 parse
        for stmt, depth in walk(self.tree, -1):
            if isinstance(stmt, Comment) and stmt.item.comment.startswith('!__OPENCASE_COMMENT#'):
                comment_split = stmt.item.comment.split(' ')
                lineno = int(comment_split[1])
                stmt.item.span = ( 0, 0 )
            else:
                if lineno>0:
                    linediff = stmt.item.span[0] - lineno
                    lineno = 0
                stmt.item.span = ( stmt.item.span[0]-linediff, stmt.item.span[1]-linediff )
            stmt.parse_f2003()

    def write_to_file(self, filepath):
        with open(filepath, 'wb') as f:
            #for stmt, depth in walk(self.tree, -1):
            #    f.write(TAB*depth+stmt.tooc()+'\n')
            f.write(self.tree.tofortran())

    def get_stmt(self, targets):
        outputs = []

        if isinstance(targets, str):
            if targets:
                if targets.isdigit():
                    stmt = self.stmt_by_label(int(targets))
                    if stmt: outputs.append(stmt)
                elif targets.lower()[0]=='l':
                    stmt = self.stmt_by_lineno(int(targets[1:]))
                    if stmt: outputs.append(stmt)
                else: raise ProgramException('Syntax error: %s'%targets)
        elif isinstance(targets, int):
            stmt = self.stmt_by_label(targets)
            if stmt: outputs.append(stmt)
        elif isinstance(targets, list) or isinstance(targets, list):
            for target in targets:
                outputs.extend(self.get_stmt(target))
        else: raise ProgramException('Unknown type: %s'%targets.__class__)

        return outputs

    def stmt_by_lineno(self, lineno):
        for stmt, depth in walk(self.tree, -1):
            if stmt.item.span[0]==lineno:
                return stmt
        return

    def stmt_by_label(self, label):
        for stmt, depth in walk(self.tree, -1):
            if isinstance(stmt, Comment):
                if hasattr(stmt, 'label') and stmt.label==label:
                    return stmt
            else:
                if stmt.item.label==label:
                    return stmt
                #print stmt.item.name, stmt.item.label, stmt.item.span
        return

    def stmt_by_name(self, name, cls=None, lineafter=-1):

        _stmt = None
        _expr = None

        for stmt, depth in walk(self.tree, -1):
            if isinstance(cls, list):
                if not stmt.__class__ in cls: continue

            if lineafter>0:
                if stmt.item.span[1]<=lineafter: continue
                if isinstance(stmt, Comment): continue

            expr = stmt.expr_by_name(name, stmt.f2003)
            if lineafter>0 or expr is not None:
                _stmt = stmt
                _expr = expr
                break

        return _stmt, _expr

def parse_srcfiles():

    # Fortran parsing of input files
    for inputfile in Config.inputfile:
        State.inputfile.append(SrcFile(inputfile))

    # pack directs
    directs = {}

    casesize = 1

    # collect global directs
    for direct_name, direct_list in State.direct.iteritems():
        directs[direct_name] = []
        for direct_tree, stmt, span in direct_list:
            casesize *= direct_tree.size
            directs[direct_name].append([direct_tree, -1, stmt, span])

     # collect local directs
    for i, inputfile in enumerate(State.inputfile):
        for direct_name, direct_list in inputfile.direct.iteritems():
            directs[direct_name] = []
            for direct_tree, stmt, span in direct_list:
                casesize *= direct_tree.size
                directs[direct_name].append([direct_tree, i, stmt, span])

    State.direct['packed'] = directs
    State.cases['size'] = casesize

def get_directs(selectfunc, prefunc, postfunc, **kwargs):
    casenumseq = []
    directs = {} 
    objs = []

    for direct_name, direct_list in State.direct['packed'].iteritems():
        for direct_tree, inputfileid, stmt, span in direct_list:
            if any( [ direct_tree.name.lower().startswith(d) for d in spacegen_directs ] ):
                elems = []
                direct_tree.walk(casenumseq, selectfunc, prefunc, postfunc, elems=elems, objs=objs, **kwargs)
                directs[direct_tree.name] = ( elems, inputfileid, stmt, span )

    casenum = 0
    cursize = 1
    for idx, node in casenumseq:
        casenum += cursize*idx
        cursize *= len(node.cases)
    #print casenum, casenumseq, directs

    return casenum, casenumseq, directs, objs

