import os
import sys
import stat
from shutil import copyfile
from oc_utils import Config, collect_items, case_filename
from oc_state import State
from oc_parse import SrcFile

def generate_script(casenum, directs, srcfileids):

    # collect directs
    for direct in [ 'prerun', 'clean', 'build', 'execute', 'postrun' ]:
        exec('%s = []'%direct)
        for key, value in directs.iteritems():
            if key.lower().startswith(direct):
                exec('%s.extend(value[0])'%direct)

    script_file = Config.path['outdir']+'/case_'+str(casenum)+'.sh'
    fscr = open(script_file, 'w+')

    # start of script
    fscr.write('#!/bin/bash\n')

    fscr.write('\n')
    fscr.write('echo start of case ' + str(casenum)+ '\n')

    # cd to workdir
    fscr.write('\n')
    fscr.write('cd %s\n'%Config.path['workdir'])

    # prerun
    fscr.write('\n')
    fscr.write('# prerun\n')
    for cmds, attr in prerun:
        for cmd in cmds:
            fscr.write(SrcFile.applymap(cmd)+'\n')

    # create symlink
    fscr.write('\n')
    fscr.write('# symlink\n')
    for i, inputfile in enumerate(State.inputfile):
        #fscr.write('rm -f %s\n'%inputfile.filename)
        fscr.write('rm -f %s\n'%inputfile.abspath)
        if i in srcfileids:
            outpath = os.path.join(Config.path['outdir'], case_filename(inputfile.filename, casenum))
            fscr.write('ln -s %s %s\n'%(outpath, inputfile.filename))
        else:
            fscr.write('ln -s %s.oc_org %s\n'%(inputfile.filename, inputfile.filename))

    # clean
    fscr.write('\n')
    fscr.write('# clean\n')
    if len(clean)!=1: raise Exception('Only one clean directive is allowed')
    clean_cmds, clean_attrs = clean[0]
    if len(clean_cmds)!=1: raise Exception('Only one clean command is allowed')
    clean_cmd = clean_cmds[0]

    cline = clean_cmd
    clean_makefile = 'Makefile'
    clean_target = 'clean'
    if clean_attrs.has_key('makefile'):
        clean_makefile = SrcFile.applymap(clean_attrs['makefile'][0])
    cline += ' -f %s'%clean_makefile
    if clean_attrs.has_key('target'):
        clean_target = SrcFile.applymap(clean_attrs['target'][0])
    cline += ' %s'%clean_target
    #dstpath = Config.path['outdir']+'/'+os.path.basename(clean_makefile)
    #if os.path.exists(dstpath): os.remove(dstpath)
    #if os.path.isabs(clean_makefile):
    #    copyfile(clean_makefile, dstpath)
    #else:
    #    copyfile(Config.path['workdir']+'/'+clean_makefile, dstpath)

    for macro, value in clean_attrs.iteritems():
        if macro not in [ 'makefile', 'target']:
            items = collect_items(value)
            cline += ' %s="%s"'%(macro, ' '.join([ SrcFile.applymap(item) for item in items ]))
    fscr.write(cline)
    fscr.write('\n')

    # build
    fscr.write('\n')
    fscr.write('# build\n')
    if len(build)!=1: raise Exception('Only one build directive is allowed')
    build_cmds, build_attrs = build[0]
    if len(build_cmds)!=1: raise Exception('Only one build command is allowed')
    build_cmd = build_cmds[0]

    cline = build_cmd
    build_makefile = 'Makefile'
    build_target = 'build'
    if build_attrs.has_key('makefile'):
        build_makefile = SrcFile.applymap(build_attrs['makefile'][0])
    cline += ' -f %s'%build_makefile
    if build_attrs.has_key('target'):
        build_target = SrcFile.applymap(build_attrs['target'][0])
    cline += ' %s'%build_target
    #if os.path.abspath(build_makefile)!=os.path.abspath(clean_makefile):
    #    dstpath = Config.path['outdir']+'/'+os.path.basename(build_makefile)
    #    if os.path.exists(dstpath): os.remove(dstpath)
    #    if os.path.isabs(build_makefile):
    #        copyfile(build_makefile, dstpath)
    #    else:
    #        copyfile(Config.path['workdir']+'/'+build_makefile, dstpath)

    for macro, value in build_attrs.iteritems():
        if macro not in [ 'makefile', 'target']:
            items = collect_items(value)
            cline += ' %s="%s"'%(macro, ' '.join([ SrcFile.applymap(item) for item in items ]))
    fscr.write(cline)
    fscr.write('\n')

    # execute
    fscr.write('\n')
    fscr.write('# execute\n')
    if len(execute)!=1: raise Exception('Only one execute directive is allowed')
    execute_cmds, execute_attrs = execute[0]
    if len(execute_cmds)!=1: raise Exception('Only one execute command is allowed')
    execute_cmd = execute_cmds[0]

    repeat = 1
    sleep = 0.3
    if execute_attrs.has_key('repeat'):
        repeat = int(execute_attrs['repeat'][0])
    if execute_attrs.has_key('sleep'):
        sleep = float(execute_attrs['sleep'][0])

    if repeat>1: fscr.write("for i in `seq 1 %s`; do\n"%repeat)    

    if repeat>1: cline = '    %s '%execute_cmd
    else: cline = '%s '%execute_cmd

    
    execute_makefile = 'Makefile'
    execute_target = 'run'
    if execute_attrs.has_key('makefile'):
        execute_makefile = SrcFile.applymap(execute_attrs['makefile'][0])
    cline += ' -f %s'%execute_makefile
    if execute_attrs.has_key('target'):
        execute_target = SrcFile.applymap(execute_attrs['target'][0])
    cline += ' %s'%execute_target
    #if os.path.abspath(execute_makefile)!=os.path.abspath(clean_makefile) and \
    #    os.path.abspath(execute_makefile)!=os.path.abspath(build_makefile):
    #    dstpath = Config.path['outdir']+'/'+os.path.basename(execute_makefile)
    #    if os.path.exists(dstpath): os.remove(dstpath)
    #    if os.path.isabs(build_makefile):
    #        copyfile(execute_makefile, dstpath)
    #    else:
    #        copyfile(Config.path['workdir']+'/'+execute_makefile, dstpath)

    for macro, value in execute_attrs.iteritems():
        if macro not in [ 'makefile', 'target', 'repeat', 'sleep']:
            items = collect_items(value)
            cline += ' %s="%s"'%(macro, ','.join([ SrcFile.applymap(item) for item in items ]))

    fscr.write(cline+'\n')

    if repeat>1:
        fscr.write("    python -c 'import time; time.sleep(%s)'\n"%sleep)    
        fscr.write("done\n")    

    fscr.flush()

    st = os.stat(script_file)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC)

    return script_file
