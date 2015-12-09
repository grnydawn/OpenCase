# oc_searchspace.py

# add path to lex
import os
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append('%s/../external'%script_dir)

from oc_utils import TAB, _DEBUG, ProgramException
import itertools as it
import ply.lex as lex
import ply.yacc as yacc

(COMB, ACCUM_COMB, PERM, ACCUM_PERM) = range(4)

class SearchSpace(object):
    pass

# each elements seperated by ";"
class SearchSubSubSpace(SearchSpace):

    def __init__(self, elempart):

        self.case = None
        self.items = elempart[0]
        self.attrs = elempart[1]

        self.default_items = [] # no parenthesis
        ssobj_items = [] # in parenthesis
        if self.items is not None:
            for item in self.items:
                if isinstance(item, SearchSubSpace):
                    ssobj_items.append(item)
                else:
                    self.default_items.append(item)

        self.default_attrs = {} # no parenthesis
        ssobj_attrs = {} # in parenthesis
        if self.attrs is not None:
            for key, attr in self.attrs.iteritems():
                if isinstance(attr, SearchSubSpace):
                    ssobj_attrs[key] = attr
                else:
                    self.default_attrs[key] = attr

        self.size = 1
        # if there is no parenthesis
        if len(ssobj_items)==0 and len(ssobj_attrs)==0:
            self.case = ( ( tuple(self.default_items), self.default_attrs ), self.size )
        # if there is parenthesis in attrs
        elif len(ssobj_items)==0:
            attrs = dict(self.default_attrs)
            for key, ssobj_attr in ssobj_attrs.iteritems():
                attrs[key] = ssobj_attr
                self.size *= ssobj_attr.size
            self.case = ( ( tuple(self.default_items), attrs ), self.size )
        # if there is parenthesis in items
        elif len(ssobj_attrs)==0:
            items = list(self.default_items)
            for ssobj_elem in ssobj_items:
                items += [ ssobj_elem ]
                self.size *= ssobj_elem.size
            self.case = ( ( tuple(items), self.default_attrs ), self.size )
        # if there are parenthesis in both of items and attrs
        else:
            items = list(self.default_items)
            for ssobj_elem in ssobj_items:
                items += [ ssobj_elem ]
                attrs = dict(self.default_attrs)
                for key,ssobj_attr in ssobj_attrs.iteritems():
                    attrs[key] = ssobj_attr
                    self.size *= (ssobj_elem.size*ssobj_attr.size)
            self.case = ( ( tuple(items), attrs ), self.size )

    def walk(self, casenumseq, selectfunc, prefunc, postfunc, items=None, attrs=None, objs=None, **kwargs):
        if prefunc:
            prefunc(self)

        if not objs is None: objs.append(self)

        #node_items, node_attrs = selectfunc(self, casenumseq, **kwargs)
        #for item in node_items:
        for item in self.case[0][0]:
            elems = []
            if isinstance(item, SearchSpace):
                item.walk(casenumseq, selectfunc, prefunc, postfunc, elems=elems, objs=objs, **kwargs)
            elif isinstance(item, str):
                elems.append(item)
            else: raise ProgramException('Unknown type: %s'%item.__class__)
            if items is not None:
                items.extend(elems)
        #for key, value in node_attrs.iteritems():
        for key, value in self.case[0][1].iteritems():
            elems = []
            if isinstance(value, SearchSpace):
                value.walk(casenumseq, selectfunc, prefunc, postfunc, elems=elems, objs=objs, **kwargs)
            elif isinstance(value, str):
                elems.append(value)
            else: raise ProgramException('Unknown type: %s'%item.__class__)
            if attrs is not None and len(elems)>0:
                if not attrs.has_key(key):
                    attrs[key] = []
                attrs[key].extend(elems)
 
#        for node in selectfunc(self, casenumseq, **kwargs):
#            if node:
#                if isinstance(node, tuple):
#                    for item in node:
#                        if isinstance(item, SearchSpace):
#                            item.walk(casenumseq, selectfunc, prefunc, postfunc, **kwargs)
#                elif isinstance(node, dict):
#                    for key, value in node.iteritems():
#                        if isinstance(value, SearchSpace):
#                            value.walk(casenumseq, selectfunc, prefunc, postfunc, **kwargs)
#                else: raise ProgramException('Unknown type: %s'%node.__class__)


        if postfunc:
            postfunc(self)

class SearchSubSpace(SearchSpace):

    def _add_cases(self, case):
        caselen = 1
        for e in case:
            caselen *= e.size
        self.cases += [ ( case, caselen ) ]
        return caselen

    def _comb_cases(self, k):
        caselen = 0
        if self.controls[1]=='+':
            for case in it.combinations_with_replacement(self.elemgroup, k):
                caselen += self._add_cases(case)
        else:
            for case in it.combinations(self.elemgroup, k):
                caselen += self._add_cases(case)
        return caselen

    def _perm_cases(self, k):
        caselen = 0
        if self.controls[1]=='+':
            for case in it.product(self.elemgroup, repeat=k):
                caselen += self._add_cases(case)
        else:
            for case in it.permutations(self.elemgroup, k):
                caselen += self._add_cases(case)
        return caselen

    def __init__(self, name, gentype, elemgroup, controls):
        self.attr = {} # attribute dictionary for external objects
        self.parent = None
        self.name = name
        self.gentype = gentype
        self.attrsize = 1
        self.elemgroup = [] # SearchSubSubSpace, SearchSubSubSpace, ...

        for elem in elemgroup:
            self.elemgroup.append(SearchSubSubSpace(elem))

        # *, number
        self.controls = controls

        # set default values for controls
        if self.controls[2] is None:
            self.controls[2] = len(self.elemgroup)
        else:
            self.controls[2] = min(int(self.controls[2]), len(self.elemgroup))

        # generate cases
        self.cases = [] # [(case, case_length)]

        # null case
        if self.controls[0]=='*':
            self.cases += [ ( [], 1 ) ]

        if gentype==COMB:
            self._comb_cases(self.controls[2])
        elif gentype==ACCUM_COMB:
            for i in range(1,self.controls[2]+1):
                self._comb_cases(i)
        elif gentype==PERM:
            self._perm_cases(self.controls[2])
        elif gentype==ACCUM_PERM:
            for i in range(1,self.controls[2]+1):
                self._perm_cases(i)
        else: raise Exception()

        self.size = 0
        for case in self.cases:
            self.size += case[1]

    def set_parent(self, parent):
        self.parent = parent

    def walk(self, casenumseq, selectfunc, prefunc, postfunc, elems=None, objs=None, **kwargs):

        if prefunc:
            prefunc(self)

        if not objs is None: objs.append(self)

        for node in selectfunc(self, casenumseq, **kwargs):
            if node:
                if isinstance(node, SearchSpace):
                    if elems is not None:
                        items = []
                        attrs = {}
                        node.walk(casenumseq, selectfunc, prefunc, postfunc, items=items, attrs=attrs, objs=objs, **kwargs)
                        if len(items)>0:
                            elems.append( (items, attrs) )
                    else:
                        node.walk(casenumseq, selectfunc, prefunc, postfunc, objs=objs, **kwargs)
                else: raise ProgramException('Unknown type: %s'%node.__class__)

        if postfunc:
            postfunc(self)

def debug(msg, _v=False, _e=False):
    if _DEBUG:
        if _v:
            print str(msg)
            print str(msg.__class__)
            print dir(msg.__class__)
        else: print str(msg)
    if _e: sys.exit(-1)


class ParserBase(object):
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()
    literals = ()

    def __init__(self, line, **kw):
        self.debug = kw.get('debug', 0)
        self.line = line
        self.searchtree = []
        self.numcases = 1

        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[1] + "_" + self.__class__.__name__
        except:
            modname = "parser"+"_"+self.__class__.__name__
        self.debugfile = modname + ".dbg"
        self.tabmodule = modname + "_" + "parsetab"
        #print self.debugfile, self.tabmodule
        #self.debug = True

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debugfile,
                  tabmodule=self.tabmodule)

        yacc.parse(self.line)

        for s in self.searchtree:
            if isinstance(s, SearchSubSpace):
                self.numcases *= s.size

class Parser(ParserBase):
    sssname = {}
 
    literals = ( '+', '-', '*', '(', ')', '[', ']', '{', '}', '<', '>')

    # List of token names.   This is always required
    tokens = (
        'WHITESPACE',
        'DECIMALINTEGER',
        'DECIMALFLOAT',
        'IDENTIFIER',
        'COMMA_DELIMITER',
        'EQUAL_DELIMITER',
        'COLON_DELIMITER',
        'SEMICOLON_DELIMITER'
    )

    # Regular expression rules for simple tokens
    t_WHITESPACE = r'\s+'
    t_DECIMALINTEGER = r'[0-9]+'
    t_DECIMALFLOAT = r'[0-9]*\.[0-9]*'
    #t_IDENTIFIER = r'[a-zA-Z]+[_a-zA-Z0-9]*'
    t_IDENTIFIER = r'[-a-zA-Z]+[-._a-zA-Z0-9]*'
    t_COMMA_DELIMITER = r'\s*,\s*'
    t_EQUAL_DELIMITER = r'\s*=\s*'
    t_COLON_DELIMITER = r'\s*:\s*'
    t_SEMICOLON_DELIMITER = r'\s*;\s*'

#    def t_NUMBER(self, t):
#        r'\d+'
#        try:
#            t.value = int(t.value)
#        except ValueError:
#            print("Integer value too large %s" % t.value)
#            t.value = 0
#        #print "parsed number %s" % repr(t.value)
#        return t
#
#    t_ignore = " \t"
#
#    def t_newline(self, t):
#        r'\n+'
#        t.lexer.lineno += t.value.count("\n")
   
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Parsing rules

    precedence = (
        ('right','-'),
        )

# searchspace ::= (searchsubspace)+
    def p_searchspace(self, p):
        """searchspace : searchsubspace
                        | searchspace whitespaceopt searchsubspace
        """

        if len(p)==2: self.searchtree += [ p[1] ]
        else: self.searchtree += [ p[3] ]

        if _DEBUG:
            for i in p: debug('searchspace: '+str(i))

    def p_searchsubspace(self, p):
        """searchsubspace : IDENTIFIERopt whitespaceopt leftbracket whitespaceopt elementgrouplist whitespaceopt rightbracket generationcontrolopt
        """
        gentype = None
        if p[3]=='(' and p[7]==')': gentype = COMB 
        elif p[3]=='{' and p[7]=='}': gentype = ACCUM_COMB
        elif p[3]=='[' and p[7]==']': gentype = PERM
        elif p[3]=='<' and p[7]=='>': gentype = ACCUM_PERM
        else:
            raise Exception('Error at p_searchsubspace')

        # create object
        #if p[0] is None: p[0] = []

        # generate cases
        sssid = 0
        if self.sssname.has_key(str(p[1])): sssid = self.sssname[str(p[1])]
        else: self.sssname[str(p[1])] = sssid

        p[0] = SearchSubSpace(str(p[1])+'-'+str(sssid), gentype, p[5], p[8])
        
        self.sssname[str(p[1])] += 1

        if _DEBUG:
            for i in p: debug('searchsubspace: '+str(i))

# attributelistpartopt ::= (attribute elementdelimiter)* attribute
    def p_attributelistpartopt(self, p):
        """attributelistpartopt : 
                        | COLON_DELIMITER attributelist
        """            
        if len(p)>1: p[0] = p[2]

        if _DEBUG:
            for i in p: debug('attributelistpartopt: '+str(i))

# attributelist ::= (attribute elementdelimiter)* attribute
    def p_attributelist(self, p):
        """attributelist : attribute
                        | attributelist COMMA_DELIMITER attribute
        """            
        if len(p)==2: p[0] = p[1]
        else: p[0] = dict(p[1], **p[3])

        if _DEBUG:
            for i in p: debug('attributelist: '+str(i))

# attribute ::= identifier (whitelspace)* equalmark (whitespace)* identifier 
    def p_attribute(self, p):
        """attribute : IDENTIFIER EQUAL_DELIMITER
                        | IDENTIFIER EQUAL_DELIMITER element
                        | DECIMALINTEGER EQUAL_DELIMITER element
        """            
        if len(p)>3:
            p[0] = { p[1]: p[3] }
        else:
            p[0] = { p[1]: None }
        if _DEBUG:
            for i in p: debug('attribute: '+str(i))

# elementgrouplist ::= (elementgroup ;)* elementgroup
    def p_elementgrouplist(self, p):
        """elementgrouplist : elementgroup attributelistpartopt
                        | elementgrouplist SEMICOLON_DELIMITER elementgroup attributelistpartopt
        """            
        if len(p)==3: p[0] = [[ p[1], p[2] ]]
        else: p[0] = p[1] + [[ p[3], p[4] ]]
        if _DEBUG:
            for i in p: debug('elementgrouplist: '+str(i))

# elementgroup ::= (element elementdelimiter)* element
    def p_elementgroup(self, p):
        """elementgroup : element
                        | elementgroup whitespaceopt COMMA_DELIMITER whitespaceopt element
        """
        if len(p)==2:
            p[0] = [ p[1] ]
        else:
            p[0] = p[1] + [ p[3] ]
        if _DEBUG:
            for i in p: debug('elementgroup: '+str(i))

# element ::= identifier | searchsubspace
    def p_element(self, p):
        """element : IDENTIFIER
                        | minusopt DECIMALINTEGER 
                        | minusopt DECIMALFLOAT 
                        | searchsubspace
        """            
        if len(p)==2:
            p[0] = p[1]
        elif len(p)==3:
            if p[1]: p[0] = p[1]+p[2]
            else: p[0] = p[2]
        if _DEBUG:
            for i in p: debug('element: '+str(i))

    def p_minusopt(self, p):
        """ minusopt :
                        | '-'
        """
        if len(p)>1: p[0] = p[1]
        if _DEBUG:
            for i in p: debug('minusopt: '+str(i))

    def p_whitespaceopt(self, p):
        """ whitespaceopt :
                        | WHITESPACE
        """
        if _DEBUG:
            for i in p: debug('whitespaceopt: '+str(i))

    def p_leftbracket(self, p):
        """ leftbracket : '('
                        | '{'
                        | '['
                        | '<'
        """
        p[0] = p[1]
        if _DEBUG:
            for i in p: debug('leftbracket: '+str(i))

    def p_rightbracket(self, p):
        """ rightbracket : ')'
                        | '}'
                        | ']'
                        | '>'
        """
        p[0] = p[1]
        if _DEBUG:
            for i in p: debug('rightbracket: '+str(i))

# generationcontrolopt ::= (\*)? ("+")? (decimalinteger)?
    def p_generationcontrolopt(self, p):
        """ generationcontrolopt : nullspaceopt repeatopt decimalintegeropt
        """
        p[0] = p[1:]
        if _DEBUG:
            for i in p: debug('generationcontrolopt: '+str(i))


# nullspaceopt ::= (\*)?
    def p_nullspaceopt(self, p):
        """ nullspaceopt : 
                        | '*'
        """
        if len(p)>1: p[0] = p[1]
        if _DEBUG:
            for i in p: debug('nullspaceopt: '+str(i))

# repeatopt ::= (\+)?
    def p_repeatopt(self, p):
        """ repeatopt : 
                        | '+'
        """
        if len(p)>1: p[0] = p[1]
        if _DEBUG:
            for i in p: debug('repeatopt: '+str(i))

# decimalintegeropt ::= (\+)?
    def p_decimalintegeropt(self, p):
        """ decimalintegeropt : 
                        | minusopt DECIMALINTEGER
        """
        
        if len(p)==3:
            if p[1]: p[0] = p[1]+p[2]
            else: p[0] = p[2]
        if _DEBUG:
            for i in p: debug('decimalintegeropt: '+str(i))

# IDENTIFIERopt
    def p_IDENTIFIERopt(self, p):
        """ IDENTIFIERopt :
                        | IDENTIFIER
        """
        if len(p)>1: p[0] = p[1]
#
#    def p_statement_expr(self, p):
#        'statement : expression'
#        print(p[1])
#
#    def p_expression_binop(self, p):
#        """
#        expression : expression '+' expression
#                  | expression MINUS expression
#                  | expression TIMES expression
#                  | expression DIVIDE expression
#                  | expression EXP expression
#        """
#        #print [repr(p[i]) for i in range(0,4)]
#        if p[2] == '+'  : p[0] = p[1] + p[3]
#        elif p[2] == '-': p[0] = p[1] - p[3]
#        elif p[2] == '*': p[0] = p[1] * p[3]
#        elif p[2] == '/': p[0] = p[1] / p[3]
#        elif p[2] == '**': p[0] = p[1] ** p[3]
#
#    def p_expression_uminus(self, p):
#        'expression : MINUS expression %prec UMINUS'
#        p[0] = -p[2]
#
#    def p_expression_group(self, p):
#        'expression : LPAREN expression RPAREN'
#        p[0] = p[2]
#
#    def p_expression_number(self, p):
#        'expression : NUMBER'
#        p[0] = p[1]
#
#    def p_expression_name(self, p):
#        'expression : NAME'
#        try:
#            p[0] = self.names[p[1]]
#        except LookupError:
#            print("Undefined name '%s'" % p[1])
#            p[0] = 0
#
    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        #else:
        #    print("Syntax error at EOF")

def generate_searchtree(line):
    parser = Parser(line)
    return parser.searchtree
