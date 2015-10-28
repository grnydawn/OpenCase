# ocplot.py

import os
import sys
import csv
import glob
import json
import argparse
import matplotlib.pyplot as plt

# states
args = None
data = {}
data_summary = {}

def parse_command_line():
    global args

    # parsing arguments
    parser = argparse.ArgumentParser(description='Plot OpenCase results')
    parser.add_argument('csvpaths', metavar='csvpaths', type=str, nargs='+', help='Path to OpenCase result data')
    parser.add_argument('--filename', metavar='filename', type=str, nargs=1, default='perf.log*', help='OpenCase result filename')
    parser.add_argument('-t', '--title', metavar='title', type=str, nargs=1, required=False, help='title  plotting.')
    parser.add_argument('-p', '--plot', metavar='plot type', type=str, nargs=1, action='append', required=False, help='plot type for plotting.')
    parser.add_argument('--figure', metavar='figure', type=str, nargs=1, required=False, help='figure for plotting.')
    parser.add_argument('--xlabel', metavar='xlabel', type=str, nargs=1, required=False, help='xlabel for plotting.')
    parser.add_argument('--xticks', metavar='xticks', type=str, nargs=1, required=False, help='xticks for plotting.')
    parser.add_argument('--xlim', metavar='xlim', type=str, nargs=1, required=False, help='xlim for plotting.')
    parser.add_argument('--ylabel', metavar='ylabel', type=str, nargs=1, required=False, help='ylabel for plotting.')
    parser.add_argument('--yticks', metavar='yticks', type=str, nargs=1, required=False, help='yticks for plotting.')
    parser.add_argument('--ylim', metavar='ylim', type=str, nargs=1, required=False, help='ylim for plotting.')
    parser.add_argument('--grid', metavar='grid', type=str, nargs=1, required=False, action='append', help='grid for plotting.')
    parser.add_argument('--legend', metavar='legend', type=str, nargs=1, required=False, help='legend for plotting.')
    parser.add_argument('--save', metavar='save', type=str, nargs=1, required=False, help='file path to save png image.')
    parser.add_argument('--limitcases', metavar='limitcases', type=int, nargs=1, default=0, required=False, help='Maximum number of cases to plot.')
    parser.add_argument('--noshow', action='store_true', default=False, help='prevent showing plot on screen.')
    parser.add_argument('--reciprocal', action='store_true', default=False, help='Performance value is a reciprocal number of measurment.')
    args = parser.parse_args()

    if len(args.csvpaths)<1:
        print 'ERROR: Not enough arguments'
        sys.exit(-1)

    for path in args.csvpaths:
        if os.path.isdir(path):
            dpaths = glob.glob('%s/%s'%(path, args.filename))
            for dpath in dpaths:
                data[dpath] = None
        elif os.path.isfile(path):
            data[path] = None
        else: raise Exception('Can not find path')

def read_data_files(reciprocal=False, limitcases=0):
    global data, data_summary

    data_summary['casenum'] = {}
    data_summary['casenum']['min'] = None
    data_summary['casenum']['max'] = None
    data_summary['caseord'] = {}
    data_summary['caseord']['min'] = None
    data_summary['caseord']['max'] = None
    data_summary['caseperf'] = {}
    data_summary['caseperf']['best'] = None

    for path, content in data.iteritems():
        if content is None:

            head = []
            table = []
            ref = 0

            # min, max, avg, count pos, avg top10
            summary = {}
            summary['casenum'] = {}
            summary['casenum']['min'] = None
            summary['casenum']['max'] = None
            summary['caseord'] = {}
            summary['caseord']['min'] = None
            summary['caseord']['max'] = None
            summary['caseperf'] = {}
            summary['caseperf']['success'] = {}
            summary['caseperf']['success']['count'] = 0
            summary['caseperf']['success']['mean'] = 0.0
            summary['caseperf']['success']['count_top10'] = 0
            summary['caseperf']['success']['top10mean'] = 0.0
            summary['caseperf']['success']['count_betterthan_ref'] = 0
            summary['caseperf']['failure'] = {}
            summary['caseperf']['failure']['count_3'] = 0
            summary['caseperf']['failure']['count_4'] = 0

            with open(path, 'rb') as f:
                reader = csv.reader(f, delimiter='\t')
                ref = 0.0
                try:
                    for i, row in enumerate(reader):
                        if len(row)<1: continue
                        if i==0:
                            if reciprocal:
                                ref = 1.0/float(row[0].split(' ')[2])
                            else:
                                ref = float(row[0].split(' ')[2])
                        elif row[0].isdigit():
                            floatrow = [ float(val) for val in row if val]

                            if reciprocal:
                                floatrow[3] = 1.0/floatrow[3]
                            if limitcases>0:
                                if floatrow[2]>limitcases: continue

                            table += [ floatrow ]

                            # ranking, casenum, caseorder, perfval
                            if summary['casenum']['min'] is None or floatrow[1]<summary['casenum']['min']:
                                summary['casenum']['min'] = floatrow[1]
                            if summary['casenum']['max'] is None or floatrow[1]>summary['casenum']['max']:
                                summary['casenum']['max'] = floatrow[1]
                            if summary['caseord']['min'] is None or floatrow[2]<summary['caseord']['min']:
                                summary['caseord']['min'] = floatrow[2]
                            if summary['caseord']['max'] is None or floatrow[2]>summary['caseord']['max']:
                                summary['caseord']['max'] = floatrow[2]
                            if floatrow[3]>0:
                                summary['caseperf']['success']['count'] += 1
                                summary['caseperf']['success']['mean'] += floatrow[3]
                                if summary['caseperf']['success']['count_top10']<10:
                                    summary['caseperf']['success']['count_top10'] += 1
                                    summary['caseperf']['success']['top10mean'] += floatrow[3]
                                if floatrow[3]>ref:
                                    summary['caseperf']['success']['count_betterthan_ref'] += 1
                            if floatrow[3]==-3.0:
                                summary['caseperf']['failure']['count_3'] += 1
                            if floatrow[3]==-4.0:
                                summary['caseperf']['failure']['count_4'] += 1
                        else:
                            head = row

                except csv.Error as e:
                    sys.exit('file %s, line %d: %s' % (path, reader.line_num, e))
                except ValueError as e:
                    import pdb; pdb.set_trace()

            summary['caseperf']['success']['mean'] /= summary['caseperf']['success']['count']
            summary['caseperf']['success']['top10mean'] /= summary['caseperf']['success']['count_top10']

            if data_summary['casenum']['min'] is None or data_summary['casenum']['min']>summary['casenum']['min']:
                data_summary['casenum']['min'] = summary['casenum']['min']
            if data_summary['casenum']['max'] is None or data_summary['casenum']['max']<summary['casenum']['max']:
                data_summary['casenum']['max'] = summary['casenum']['max']
            if data_summary['caseord']['min'] is None or data_summary['caseord']['min']>summary['caseord']['min']:
                data_summary['caseord']['min'] = summary['caseord']['min']
            if data_summary['caseord']['max'] is None or data_summary['caseord']['max']<summary['caseord']['max']:
                data_summary['caseord']['max'] = summary['caseord']['max']
            if data_summary['caseperf']['best'] is None or data_summary['caseperf']['best']<table[0][3]:
                data_summary['caseperf']['best'] = table[0][3]

            data[path] = (ref, head, table, summary)

def plot_best(ax, plotargs, dpath, summary, caseranks, casenums, caseorders, caseperfs):

    caseorder = sorted(zip(caseorders, caseperfs), key=lambda case: case[0])

    xval = [ caseord for caseord, caseperf in caseorder ]
    perfvals = [ caseperf for caseord, caseperf in caseorder ]

    bestperf = -100
    yval = []
    for perfval in perfvals:
        if len(yval)==0 or perfval>bestperf:
            yval.append(perfval)
            bestperf = perfval
        else: yval.append(bestperf)

    if dpath.find('ctree')>=0:
        clr = 'k'
        lns = '-'
        algotype = 'CTREE\nalgorithm'
    elif dpath.find('rand')>=0:
        clr = 'm'
        lns = '--'
        algotype = 'random\nalgorithm'
    else: raise Exception('unknown: %s'%dpath)

    plotobj = None
    exec('plotobj = ax.plot(xval, yval, color=clr, linestyle=lns%s)'%plotargs)

    return plotobj, algotype

def plot_scatter(ax, plotargs, dpath, summary, caseranks, casenums, caseorders, caseperfs):

    caseorder = sorted(zip(caseorders, caseperfs), key=lambda case: case[0])

    xval = [ caseord for caseord, caseperf in caseorder ]
    perfvals = [ caseperf for caseord, caseperf in caseorder ]

    yval = []
    for perfval in perfvals:
        if perfval<0:
            yval.append(None)
        else: yval.append(perfval)

    if dpath.find('ctree')>=0:
        clr = 'k'
        mkr = '^'
        algotype = 'CTREE\nalgorithm'
    elif dpath.find('rand')>=0:
        clr = 'm'
        mkr = 'o'
        algotype = 'random\nalgorithm'
    else: raise Exception('unknown: %s'%dpath)

    plotobj = None
    exec('plotobj = ax.scatter(xval, yval, s=80, color=clr, marker=mkr%s)'%plotargs)

    return plotobj, algotype

def plot_barbest(ax, plotargs, barbests, legends):
    width = 0.35
    xticks = []
    xticklabels = []
    idx_rand = 0
    idx_ctree = 0
    for dpath, ref, best in barbests:
        if dpath.find('ctree')>=0:
            stride = 7
            idx_ctree += 1
            idx = idx_ctree
            ename = 'CTREE\n%d'%idx
        elif dpath.find('rand')>=0:
            stride = 0
            idx_rand += 1
            idx = idx_rand
            ename = 'RAND\n%d'%idx

        objs = ax.bar([stride+idx, stride+idx+width], [ref, best], width, color=['y', 'k'])
        xticks.append(stride+idx+width)
        xticklabels.append(ename)

    ax.set_xticks(xticks)
    ax.set_xticklabels(xticklabels)

    legends['objs'] = objs
    legends['labels'] = ['reference performance', 'best performance found by OpenCase']

    ax.text(1.5, 47, 'Random Search Algorithm', fontsize=30)
    ax.text(9, 53, 'Casetree Search Algorithm', fontsize=30)
    #ax.text(1.5, 380000, 'Random Search Algorithm', fontsize=30)
    #ax.text(9, 380000, 'Casetree Search Algorithm', fontsize=30)
    #import pdb; pdb.set_trace()
#
#    caseorder = sorted(zip(caseorders, caseperfs), key=lambda case: case[0])
#
#    xval = [ caseord for caseord, caseperf in caseorder ]
#    perfvals = [ caseperf for caseord, caseperf in caseorder ]
#
#    bestperf = -100
#    yval = []
#    for perfval in perfvals:
#        if len(yval)==0 or perfval>bestperf:
#            yval.append(perfval)
#            bestperf = perfval
#        else: yval.append(bestperf)
#
#    if dpath.find('ctree')>=0:
#        clr = 'k'
#        lns = '-'
#        algotype = 'CTREE\nalgorithm'
#    elif dpath.find('rand')>=0:
#        clr = 'm'
#        lns = '--'
#        algotype = 'random\nalgorithm'
#    else: raise Exception('unknown: %s'%dpath)
#
#    plotobj = None
#    exec('plotobj = ax.plot(xval, yval, color=clr, linestyle=lns%s)'%plotargs)
#
#    rects2 = ax.bar(ind+width, womenMeans, width, color='y', yerr=womenStd)
#    return plotobj, algotype

def gen_plots():
    # figure setting
    if args.figure:
        exec('fig = plt.figure(%s)'%args.figure[0])
    else:
        fig = plt.figure()

    ax = fig.add_subplot(111)

    if args.title:
        exec('ax.set_title(%s)'%args.title[0])

    # x axis setting
    if args.xlabel:
        exec('ax.set_xlabel(%s)'%args.xlabel[0])

    if args.xticks:
        tickpos = None
        ticklabel = None
        for xtick in args.xticks:
            if len(xtick.strip())==0: continue
            if xtick.find('=')>0:
                key,value = xtick.split('=')
                if key.strip().lower()=='fontsize':
                    for label in ax.xaxis.get_ticklabels(): label.set_fontsize(int(value))
                else: raise Exception('Unknown xtick attribute: %s'%xtick)
            elif tickpos is None:
                pass
            elif ticklabel is None:
                pass
            else: raise Exception('Wrong xticks: %s'%xtick)

    if args.xlim:
        exec('ax.set_xlim(%s)'%args.xlim[0])
    #else:
    #    ax.set_xlim([_xdata[0], _xdata[-1]])

    # y axis setting
    if args.ylabel:
        exec('ax.set_ylabel(%s)'%args.ylabel[0])

    if args.yticks:
        tickpos = None
        ticklabel = None
        for ytick in args.yticks:
            if len(ytick.strip())==0: continue
            if ytick.find('=')>0:
                key,value = ytick.split('=')
                if key.strip().lower()=='fontsize':
                    for label in ax.yaxis.get_ticklabels(): label.set_fontsize(int(value))
                else: raise Exception('Unknown xtick attribute: %s'%ytick)
            elif tickpos is None:
                pass
            elif ticklabel is None:
                pass
            else: raise Exception('Wrong xticks: %s'%ytick)

    if args.ylim:
        exec('ax.set_ylim(%s)'%args.ylim[0])

    if args.grid:
        for g in args.grid:
            exec('ax.grid(%s)'%g)

    print json.dumps(data_summary)

    # plotting
    legends = {}
    legends['objs'] = []
    legends['labels'] = []
    refperfs = []
    barbests = []

    for dpath, (ref, head, table, summary) in data.iteritems():
        print dpath+ ' ******************************'
        print json.dumps(summary)

        casenums = [ caseresult[1] for caseresult in table ]
        caseorders = [ caseresult[2] for caseresult in table ]
        caseperfs = [ caseresult[3] for caseresult in table ]
        caseranks = range(len(caseperfs))

        _xdata = caseranks
        _ydata = caseperfs

        if args.plot:
            for plot in args.plot:
                plotarg = plot[0].strip()
                poscomma = plotarg.find(',')
                if poscomma<0:
                    raise Exception('Wrong plot option: %s'%plotarg)
                elif plotarg[:poscomma]=='best':
                    ax.set_xlim([0, data_summary['caseord']['max']])
                    bestplot,algotype = plot_best(ax, plotarg[poscomma:], dpath, summary, caseranks, casenums, caseorders, caseperfs)
                    if algotype not in legends['labels']:
                        legends['objs'].append(bestplot[0])
                        legends['labels'].append(algotype)
                    refperfs.append(ref)
                    if len(refperfs)==len(data):
                        refperfmean = sum(refperfs)/len(refperfs)
                        refplot = ax.plot( [0, data_summary['caseord']['max']], [refperfmean, refperfmean], \
                            linestyle='-.', color='g', linewidth=8.0 )
                        legends['objs'].append(refplot[0])
                        legends['labels'].append('reference\nperformance')

                elif plotarg[:poscomma]=='barbest':
                    barbests.append((dpath, ref, caseperfs[0]))
                    if len(barbests)==len(data):
                        plot_barbest(ax, plotarg[poscomma:], barbests, legends)
                    #ax.set_xlim([0, data_summary['caseord']['max']])
                    #bestbarplot,algotype = plot_barbest(ax, plotarg[poscomma:], dpath, summary, caseranks, casenums, caseorders, caseperfs)
                    #if algotype not in legends['labels']:
                    #    legends['objs'].append(bestbarplot[0])
                    #    legends['labels'].append(algotype)
#                    refperfs.append(ref)
#                    if len(refperfs)==len(data):
#                        refperfmean = sum(refperfs)/len(refperfs)
#                        refplot = ax.plot( [0, data_summary['caseord']['max']], [refperfmean, refperfmean], \
#                            linestyle='-.', color='g', linewidth=8.0 )
#                        legends['objs'].append(refplot[0])
#                        legends['labels'].append('reference\nperformance')

                elif plotarg[:poscomma]=='scatter':
                    ax.set_xlim([0, data_summary['caseord']['max']])
                    scatterplot,algotype = plot_scatter(ax, plotarg[poscomma:], dpath, summary, caseranks, casenums, caseorders, caseperfs)
                    if algotype not in legends['labels']:
                        legends['objs'].append(scatterplot)
                        legends['labels'].append(algotype)
                    refperfs.append(ref)
                    if len(refperfs)==len(data):
                        refperfmean = sum(refperfs)/len(refperfs)
                        refplot = ax.plot( [0, data_summary['caseord']['max']], [refperfmean, refperfmean], \
                            linestyle='-', color='g', linewidth=8.0 )
                        legends['objs'].append(refplot[0])
                        legends['labels'].append('reference\nperformance')

                elif plotarg[:poscomma]=='plot':
                    exec('ax.plot(_xdata, _ydata%s)'%plotarg[poscomma:])
                elif plotarg[:poscomma]=='text':
                    exec('ax.text(%s)'%plotarg[poscomma+1:])
                else:
                    exec('ax.%s(_xdata, _ydata%s)'%(plotarg[:poscomma], plotarg[poscomma:]))
        else:
            ax.plot(_xdata, _ydata)

    # legend
    if args.legend:
        exec('plt.legend(legends["objs"], legends["labels"]%s)'%args.legend[0])

    # saving an image file
    if args.save:
        exec('_savename=%s'%args.save[0])
        plt.savefig("%s.pdf"%_savename, format='pdf')

    # displyaing an image on screen
    if not args.noshow:
        plt.show()

def main():

    parse_command_line()

    read_data_files(reciprocal=args.reciprocal, limitcases=args.limitcases[0])

    gen_plots()

# starts HERE
if __name__ == "__main__":
    main()
   
