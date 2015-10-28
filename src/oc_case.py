# oc_case.py

import re
import time
from oc_algorithm import select_nextcasenum
from oc_utils import exec_cmd, findall, Logger, ProgramException, Config
from oc_state import State
from oc_parse import get_directs, SrcFile
from oc_script import generate_script
from oc_source import generate_source
    
##################################################################
#                        WALK FUNCTIONS                          #
##################################################################


import random

def weighted_choice(items):
    """items is a list of tuples in the form (item, weight)"""
    weight_total = sum((item[1] for item in items))
    n = random.uniform(0, weight_total)
    for item, weight in items:
        if n < weight:
            return item
        n = n - weight
    return item

def selectfunc_random(node, casenumseq, **kwargs):
    import random

    count = len(node.cases)
    idx = random.choice(range(count))

    casenumseq.append((idx, node))

    return node.cases[idx][0]

def selectfunc_dtree(node, casenumseq, **kwargs):
#    import numpy

    # total number of edges to children nodes
    count = len(node.cases)

    # create weight list if not exists
    if not hasattr(node, 'dtree_weights'):
        node.dtree_weights = [State.algorithm['dtree']['initial_weight']]*count
        node.dtree_top = None

    # generate probability distribution
    wsum = sum(node.dtree_weights)
    if wsum==0:
        p = [ 1./len(node.dtree_weights) ]*count
    else:
        p = [ w/wsum for w in node.dtree_weights ]

    # select a case based on probability distribution
    idx = weighted_choice(zip(range(count), p))
#    idx = numpy.random.choice(count, p=p)

    # save the selection into a list
    casenumseq.append((idx, node))

    return node.cases[idx][0]

def prefunc_printelem(node, **kwargs):
    if hasattr(node, 'default_items'):
        print SrcFile.applymap(str(node.default_items)), SrcFile.applymap(str(node.default_attrs))

def prefunc_printweight(node, **kwargs):
    if hasattr(node, 'dtree_weights'):
        print node.dtree_weights

def prefunc_printweightelem(node, **kwargs):
    prefunc_printweight(node, **kwargs)
    prefunc_printelem(node, **kwargs)

def prefunc_pass(node, **kwargs):
    pass

def postfunc_pass(node, **kwargs):
    pass

def updatefunc_pass(case, ranking, num_success, num_failed):
    pass

def updatefunc_dtree(case, ranking, num_success, num_failed):
    
    if ranking<0: # if an execution of a case is failed
        if ranking==Case.VERIFICATION_FAIL: penalty = 0.05 # 5% penalty
        else: penalty = 0.1 # 10% penalty

        # apply penalty
        for idx, node in case.caseidxseq:
            if len(node.cases)>1:
                if node.dtree_top and node.dtree_top==idx:
                    pass
                else:
                    node.dtree_weights[idx] *= (1.0 - penalty)
    else: # if an execution of a case is success
        median = int(num_success/2.0)
        if ranking<median: # if ranking is top 50%, gain between 0 ~ 0.1 according to the ranking
            gain = 0.1 - 0.1*ranking/median # 
        else: gain = 0 # if ranking is lower 50%, no gain

        # apply gain
        for idx, node in case.caseidxseq:
            if len(node.cases)>1:
                if ranking==0:
                    node.dtree_top = idx
                node.dtree_weights[idx] *= (1.0 + gain)

casegen_functions_random = (selectfunc_random, prefunc_pass, postfunc_pass, updatefunc_pass)
casegen_functions_dtree = (selectfunc_dtree, prefunc_pass, postfunc_pass, updatefunc_dtree)

##################################################################
#                        CASE CLASSES                            #
##################################################################
class Case(object):
    NOT_INTIALIZED, REFCASE = range(-1, -3, -1)
    VERIFIED, GENERIC_FAIL, EXECUTION_FAIL, MEASURMENT_FAIL, VERIFICATION_FAIL = range(0, -5, -1)
    ref_outer_iter = 2
    ref_inner_iter = 3

    def __init__(self, parent, casenum, caseorder=None , directs=None, objs=None, caseidxseq=None):
        self.parent = parent
        self.casenum = casenum
        self.caseorder = caseorder
        self.directs = directs
        self.objs = objs
        self.caseidxseq = caseidxseq

        self.result = Case.GENERIC_FAIL

    def execute(self):

        if self.casenum==Case.NOT_INTIALIZED:
            raise ProgramException('Case is not initialized')

        output = None

        if self.casenum==Case.REFCASE:
            # execute refcase
            stdout = []
            cmd = State.direct['refcase'][0][0].cases[0][0][0].case[0][0][0]
            refcmd = SrcFile.applymap(cmd) 
            for j in range(self.ref_outer_iter):
                for i in range(self.ref_inner_iter):
                    stdout.append(exec_cmd(refcmd))
                    time.sleep(0.1)
                time.sleep(0.3)
            output = '\n'.join(stdout)
        else:
            print 'Executing case %d of %d'%(self.casenum, State.cases['size'])

            # transform source
            srcgen = [ value for key, value in self.directs.iteritems() if key.lower().startswith('srcgen') ]
            srcfiles = generate_source(self.casenum, srcgen)

            # generate shell script
            script = generate_script(self.casenum, self.directs, srcfiles)

            # execute shell script
            output = exec_cmd(script)

        #print 'OUTPUT: ', output

        if not output:
            self.result = Case.EXECUTION_FAIL
            return


        # measure
        self.measured = {}
        for var, attrs in self.parent.measure.iteritems():
            self.measured[var] = []
            prefix = attrs['prefix']
            len_prefix = len(prefix)
            match_prefix = findall(prefix, output)
            if match_prefix:
                for start in match_prefix:
                    valuestr = output[start+len_prefix:].lstrip()
                    match_value = re.search(r'[\s\r\n\z]', valuestr)
                    if match_value:
                        self.measured[var].append(valuestr[:match_value.start()])
                    else:
                        self.result = Case.MEASURMENT_FAIL
                        return
            else:
                self.result = Case.MEASURMENT_FAIL
                return
        if any([ len(v)==0 for k,v in self.measured.iteritems()]):
            self.result = Case.MEASURMENT_FAIL
            return

        # verify
        for var, attrs in self.parent.verify.iteritems():
            if not self.measured.has_key(var):
                self.result = Case.NO_MEASUREMENT_FAIL
                return

            method = attrs['method']
            if method=='match':
                pattern = attrs['pattern']
                if any( [ value!=pattern for value in self.measured[var] ] ):
                    self.result = Case.VERIFICATION_FAIL
                    return
            elif method=='diff':
                refval = float(attrs['refval'])
                maxdiff = float(attrs['maxdiff'])
                if any( [ abs(float(value)-refval)>maxdiff for value in self.measured[var] ] ):
                    self.result = Case.VERIFICATION_FAIL
                    return
            else: raise ProgramException('Unsupported method: %s'%method)

        self.result = Case.VERIFIED
        return

class Cases(object):

    def __init__(self):
        self.refcase = None
        self.ranking = [] # (casenum, caseorder, performance )
        self.failed = [] # (casenum, caseorder, performance )
        self.casenums = []

        # configure for case generation
        if State.direct.has_key('casegen'):
            if len(State.direct['casegen'])!=1:
                raise UserException('Only one CASEGEN directive is allowed')
            sub = State.direct['casegen'][0][0] # (sub, stmt, span)
            subsub = sub.cases[0][0][0]
            item = SrcFile.applymap(subsub.case[0][0][0])
            attrs = SrcFile.applymap(subsub.case[0][1])

            if item=='rand':
                self.selectfunc, self.prefunc, self.postfunc, self.updatefunc = casegen_functions_random
            elif item=='dtree':
                self.selectfunc, self.prefunc, self.postfunc, self.updatefunc = casegen_functions_dtree
            else: raise UserException('%s is not valid cage generation algorithm'%item)
        else:
            self.selectfunc, self.prefunc, self.postfunc, self.updatefunc = casegen_functions_random

        # configure for measurment
        self.measure = {}
        for sub, stmt, span in State.direct['measure']:
            for subsub in sub.cases[0][0]:
                item = SrcFile.applymap(subsub.case[0][0][0])
                attrs = SrcFile.applymap(subsub.case[0][1])
                self.measure[item] = attrs

        # configure for verification
        self.verify = {}
        for sub, stmt, span in State.direct['verify']:
            for subsub in sub.cases[0][0]:
                item = SrcFile.applymap(subsub.case[0][0][0])
                attrs = SrcFile.applymap(subsub.case[0][1])
                self.verify[item] = attrs

        self.rank_var = State.direct['rank'][0][0].cases[0][0][0].case[0][0][0]
        self.rank_attrs = State.direct['rank'][0][0].cases[0][0][0].case[0][1]

    def get_refcase(self):
        # construct refcase
        self.refcase = Case( self, casenum=Case.REFCASE )

        return self.refcase

    def get_nextcase(self):
        # construct directives
        casenum = -1
        while casenum==-1 or len(self.casenums)>=State.cases['size']:
            casenum, casenumseq, directs, objs = get_directs( self.selectfunc, self.prefunc, self.postfunc)
            if casenum in self.casenums:
                casenum = -1

        self.casenums.append(casenum)
        return Case( self, casenum=casenum, caseorder=len(self.casenums), directs=directs, caseidxseq=casenumseq, objs=objs )

    def rank(self, case):
        if case.result==Case.VERIFIED:
            perfvals = [ float(val) for val in case.measured[self.rank_var] ]
            perfval = sum(perfvals)/len(perfvals)
            result_triple = (case.casenum, case.caseorder, perfval)

            print 'SUCCESS: ', result_triple

            self.ranking.append(result_triple)
            if self.rank_attrs.has_key('sort'):
                if self.rank_attrs['sort'].lower()=='descend':
                    self.ranking.sort(key=lambda c: c[2], reverse=True)
                elif self.rank_attrs['sort'].lower()=='ascend':
                    self.ranking.sort(key=lambda c: c[2], reverse=False)
            else:
                self.ranking.sort(key=lambda c: c[2], reverse=False)

            self.updatefunc(case, self.ranking.index(result_triple), len(self.ranking), len(self.failed))
        else:
            print 'FAILED: ', (case.casenum, case.caseorder, case.result)

            self.failed.append((case.casenum, case.caseorder, case.result))
            self.updatefunc(case, case.result, len(self.ranking), len(self.failed))

##################################################################
#                     INTERFACE FUNCTIONS                        #
##################################################################
def configure_searching():
    cases = Cases()

    State.cases['mgr'] = cases

def execute_refcase():
    mgr = State.cases['mgr']
    refcase = mgr.get_refcase()
    refcase.execute()
    if refcase.result!=Case.VERIFIED:
        print 'WARNING: Reference case is not correctly executed'
    else:
        refperfvals = [ float(val) for val in refcase.measured[mgr.rank_var] ]
        refperfval = sum(refperfvals)/len(refperfvals)
        Logger.info('\nReference performance: %e'%refperfval, stdout=True)

def execute_nextcase():
    case_mgr = State.cases['mgr']
    if len(case_mgr.casenums)>=State.cases['size']:
        return False

    # reset parsed tree
    for inputfile in State.inputfile:
        inputfile.reset_parsing()

    nextcase = case_mgr.get_nextcase()
    nextcase.execute()
    case_mgr.rank(nextcase)

    # return False to finish
    with open(Config.path['perf'], 'wb') as f:
        if case_mgr:
            if case_mgr.refcase.result==Case.VERIFIED:
                refperfvals = [ float(val) for val in case_mgr.refcase.measured[case_mgr.rank_var] ]
                refperfval = sum(refperfvals)/len(refperfvals)
                f.write('Reference performance: %e\n'%refperfval)
            else:
                f.write('Reference performance: not available\n')

            f.write('\nranking\tcase-number\tcase-order\tperformance\n')
            for i, rank in enumerate(case_mgr.ranking):
                f.write('%d\t\t%d\t\t%d\t\t%e\n'%((i+1,)+rank))

            for i, failed in enumerate(case_mgr.failed):
                f.write('%d\t\t%d\t\t%d\t\t%e\n'%((i+1,)+failed))
 
    return True
