# oc_output.py

import datetime
from oc_utils import Logger, Config, TAB
from oc_state import State
from oc_case import Case

def generate_output():
    Logger.info('\n******** SUMMARY **********', stdout=True)

    Logger.info('\nINPUT FILES:', stdout=True)
    # list source files
    for srcfile in State.inputfile:
        Logger.info(TAB+srcfile.tree.reader.id, stdout=True)
        if Config.debug['enabled']:
            #for directline in srcfile.directlines:
            #    Logger.info(TAB*2+directline, stdout=True)
            pass
    Logger.info('TOTAL %d cases'%State.cases['size'], stdout=True)

    # ranking
    topN = min(10, State.cases['size'])
    Logger.info('\nRANKING - top %d:'%topN, stdout=True)
    mgr = State.cases['mgr']
    if mgr:
        if mgr.refcase.result==Case.VERIFIED:
            refperfvals = [ float(val) for val in mgr.refcase.measured[mgr.rank_var] ]
            refperfval = sum(refperfvals)/len(refperfvals)
            Logger.info('\nReference performance: %e'%refperfval, stdout=True)
        else:
            Logger.info('\nReference performance: not available', stdout=True)

        Logger.info('\nranking\tcase-number\tcase-order\tperformance', stdout=True)
        for i, rank in enumerate(mgr.ranking[:topN]):
            Logger.info('%d\t\t%d\t\t%d\t\t%e'%((i+1,)+rank), stdout=True)

    # summarize operation
    begin = datetime.datetime.fromtimestamp(State.operation['begin']).strftime('%Y-%m-%d %H:%M:%S')
    diffsecs = State.operation['end']-State.operation['begin']
    Logger.info('\nELAPSED TIME:', stdout=True)
    Logger.info(TAB+'%s from %s'%(str(datetime.timedelta(seconds=diffsecs)), begin), stdout=True)

    # how much quality has improved(compared to reference???)

    # what algorithm is used(with parameters)

    # what are the common features of the quality cases

    # write ranking into a file
    with open(Config.path['outdir']+'/perf.log', 'wb') as f:
        mgr = State.cases['mgr']
        if mgr:
            if mgr.refcase.result==Case.VERIFIED:
                refperfvals = [ float(val) for val in mgr.refcase.measured[mgr.rank_var] ]
                refperfval = sum(refperfvals)/len(refperfvals)
                f.write('Reference performance: %e\n'%refperfval)
            else:
                f.write('Reference performance: not available\n')

            f.write('\nranking\tcase-number\tcase-order\tperformance\n')
            for i, rank in enumerate(mgr.ranking):
                f.write('%d\t\t%d\t\t%d\t\t%e\n'%((i+1,)+rank))

            for i, failed in enumerate(mgr.failed):
                f.write('%d\t\t%d\t\t%d\t\t%e\n'%((-1,)+failed))

    Logger.info('', stdout=True)
