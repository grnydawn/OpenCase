# oc_utils.py
# OpenCase utillities

import os
import re
import sys
import signal
from shutil import copyfile, rmtree
from Fortran2003 import Name, Data_Ref

# Put src folder first in path
sys.path = sys.path + [ os.path.dirname(__file__) ]

#############################################################################
## COMMON
#############################################################################

TAB = ' '*4

#_DEBUG = True
_DEBUG = False

unit_conv = { 's':1, 'm':60, 'h':3600, 'd':86400 }

EXTERNAL_NAMELEVEL_SEPERATOR = '.'
INTERNAL_NAMELEVEL_SEPERATOR = '__oc__' # lower-case only

def encode_NS(namepath):
    return namepath.replace(EXTERNAL_NAMELEVEL_SEPERATOR, INTERNAL_NAMELEVEL_SEPERATOR)

def decode_NS(namepath):
    return namepath.replace(INTERNAL_NAMELEVEL_SEPERATOR, EXTERNAL_NAMELEVEL_SEPERATOR)

class OCName(object):
    def __init__(self, name, node=None, stmt=None):
        if not name: raise ProgramException('Name can not be none or blank')
        if name[0].isdigit(): raise ProgramException('Name can not have digit as its first character')

        self.namepath = encode_NS(name).strip().lower() # lower case
        self.namelist = self.namepath.split(INTERNAL_NAMELEVEL_SEPERATOR)
        self.dataref = Data_Ref(self.namelist[-1])
        self.node = node
        self.stmt = stmt
        #self.rename = []

    def path(self):
        return decode_NS(self.namepath)

    def list(self):
        return self.namelist

    def dataref(self):
        return self.dataref

    def last(self):
        return self.namelist[-1]

    def first(self):
        return self.namelist[0]

    def firstpartname(self):
        if isinstance(self.dataref, Name):
            return self.dataref.string
        else:
            return self.dataref.items[0].string

    def __eq__(self, other):
        return self.namepath==other.namepath

    def __str__(self):
        raise Exception('KGName')

def pathname(stmt, lastname):
    ancnames = '.'.join([ a.name.lower() for a in stmt.ancestors() ])
    return '%s.%s'%(ancnames, lastname)

def singleton(cls):
    """ singleton generator """

    instances = {}
    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return get_instance()

def exec_cmd(cmd, show_error_msg=True, shell=True):
    import subprocess

    proc = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.read()
    ret_code = proc.wait()
    if ret_code != 0 and show_error_msg:
        cmd_out, cmd_err = proc.communicate()
        print '>> %s' % out
        print '>> %s' % cmd
        print '>> %s' % out
        print 'returned non-zero code from shell('+str(ret_code)+')\n OUTPUT: '+str(cmd_out)+'\n ERROR: '+str(cmd_err)+'\n'
    return out

def findall(pattern, string):
    start = 0
    while True:
        start = string.find(pattern, start)
        if start == -1: return
        yield start
        start += len(pattern)

def collect_items(obj):
    result = []
    if obj is None: return result

    if isinstance(obj, str):
        result.append(obj)
    elif isinstance(obj, (tuple, list)):
        for item in obj:
            result.extend(collect_items(item))

    return result

def case_filename(filename, casenum):
    return '%s.%d'%(filename, casenum)

def traverse(node, func, extra, attr='items', prerun=True, depth=0):
    if prerun and func is not None:
        func(node, depth, extra)

    if node and hasattr(node, attr) and getattr(node, attr):
            exec('for child in node.%s: traverse(child, func, extra, attr=attr, prerun=prerun, depth=depth+1)' % attr)

    if not prerun and func is not None:
        func(node, depth, extra)

def get_subtree(obj, tree, prefix='top', depth=0):
    tab = '    '
    postfix = ''
    if isinstance(obj, str): postfix = ' => ' + obj
    elif isinstance(obj, type): postfix = ' => ' + str(obj)
    elif obj.__class__.__name__=='Name': postfix = ' => ' + obj.string

    #tree += [ ( tab*depth + prefix + ': ' + str(obj.__class__) + postfix, depth ) ]
    if hasattr(obj, 'parent'):
        pcls = str(obj.parent.__class__)
    else:
        pcls = 'None'
    tree += [ ( tab*depth + prefix + ': ' + str(obj.__class__) + postfix + ': parent => ' + pcls , depth ) ]
    if hasattr(obj, 'items'):
        for item in obj.items:
            get_subtree(item, tree, prefix='item', depth=depth+1)

    if hasattr(obj, 'content'):
        for elem in obj.content:
            get_subtree(elem, tree, prefix='content', depth=depth+1)

def show_obj(obj):
    print 'CLS: ', obj.__class__
    print 'STR: ', str(obj)
    print 'DIR: ', dir(obj)

def show_tree(node):
    tree = []
    get_subtree(node, tree)
    for elem, depth in tree:
        print '    '*depth + elem

def insert_content(olditem, newitems, remove_olditem=True):
    parent = olditem.parent
    if olditem in parent.content:
        idx = parent.content.index(olditem)

        for item in newitems:
            item.parent = parent

        if remove_olditem:
                parent.content.remove(olditem)

        parent.content[idx:idx] = newitems

def remove_content(olditems):
    if isinstance(olditems, tuple) or isinstance(olditems, list):
        for olditem in olditems:
            if olditem in olditem.parent.content:
                olditem.parent.content.remove(olditem)
    else:
        if olditems in olditems.parent.content:
            olditems.parent.content.remove(olditems)

#############################################################################
## EXCEPTION
#############################################################################

class OCException(Exception):
    pass

class TimeoutException(OCException):
    pass

class UserException(OCException):
    pass

class ProgramException(OCException):
    pass

class Timeout(object):
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutException(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

#############################################################################
## CONFIG
#############################################################################

@singleton
class Config(object):
    """ OpenCase configuration parameter holder """

    def __init__(self):
        import optparse

        # setup config parameters
        self._attrs = {}

        # openase parameters
        self._attrs['opencase'] = {}
        self._attrs['opencase']['version'] = [ 0, 0, '1' ]

        # logging parameters
        self._attrs['logging'] = {}
        self._attrs['logging']['select'] = {}
        self._attrs['logging']['enabled'] = True

        # input source files
        self._attrs['inputfile'] = []

        # external tool parameters
        self._attrs['bin'] = {}
        self._attrs['bin']['pp'] = 'fpp'
        self._attrs['bin']['cpp_flags'] = '-w -traditional'
        self._attrs['bin']['fpp_flags'] = '-w'

        # path parameters
        self._attrs['path'] = {}
        self._attrs['path']['workdir'] = './work'
        self._attrs['path']['outdir'] = './output'
        self._attrs['path']['refdir'] = './ref'

        # include parameters
        self._attrs['include'] = {}
        self._attrs['include']['macro'] = {}
        self._attrs['include']['path'] = []
        self._attrs['include']['file'] = {}

        # miscellaneous parameters
        self._attrs['misc'] = {}
        self._attrs['misc']['timeout'] = None

        # debugging parameters
        self._attrs['debug'] = {}
        self._attrs['debug']['enabled'] = False

        # parsing arguments
        usage = "usage: %prog [options] file, file, ..."
        parser = optparse.OptionParser(usage=usage)
        parser.add_option("-i", "--include-ini", dest="include_ini", action='store', type='string', default=None, help="information used for analysis")
        parser.add_option("-I", dest="include", action='append', type='string', default=None, help="include path information used for analysis")
        parser.add_option("-D", dest="macro", action='append', type='string', default=None, help="macro information used for analysis")
        parser.add_option("--srcdir", dest="srcdir", action='store', type='string', help="specifiying path to source directory")
        parser.add_option("--outdir", dest="outdir", action='store', type='string', default=None, help="path to create outputs")
        parser.add_option("--workdir", dest="workdir", action='store', type='string', default=None, help="path to working dir")
        parser.add_option("--refdir", dest="refdir", action='store', type='string', default=None, help="path to reference dir")
        parser.add_option("--skip-intrinsic", dest="skip_intrinsic", action='append', type='string', default=None, help="Skip intrinsic procedures during searching")
        parser.add_option("--noskip-intrinsic", dest="noskip_intrinsic", action='append', type='string', default=None, help="Do not skip intrinsic procedures during searching")
        parser.add_option("--timeout", dest="timeout", action='store', type='string', default=None, help="Timeout to exit")
        parser.add_option("--nologging", dest="nologging", action='store_true', default=False, help="Turn-off logging")
        parser.add_option("--debug", dest="debug", action='append', type='string', help=optparse.SUPPRESS_HELP)

        opts, args = parser.parse_args()
        if len(args)<1:
            print 'ERROR: No input file is provided in command line.'
            sys.exit(-1)

        for inputfile in args:
            if not os.path.isfile(inputfile):
                print 'ERROR: %s can not be found.' % inputfile
                sys.exit(-1)
            self._attrs['inputfile'].append(os.path.abspath(inputfile))
            #if os.path.exists(inputfile + '.oc_org'):
            #    os.remove(inputfile)
            #    copyfile(inputfile + '.oc_org', inputfile)
            #else:
            #    copyfile(inputfile, inputfile + '.oc_org')

        # check if exists fpp or cpp
        output = ''
        try: output = exec_cmd('which fpp', show_error_msg=False).strip()
        except Exception as e: pass
        if output.endswith('fpp'):
            self.bin['pp'] = output
        else:
            output = ''
            try: output = exec_cmd('which cpp', show_error_msg=False).strip()
            except Exception as e: pass
            if output.endswith('cpp'):
                self.bin['pp'] = output
            else:
                print 'ERROR: neither cpp or fpp is found'
                sys.exit(-1)

        # parsing intrinsic skip option
        if opts.noskip_intrinsic:
            self._attrs['search']['skip_intrinsic'] = False
            for line in opts.noskip_intrinsic:
                for noskip in line.lower().split(','):
                    key, value = noskip.split('=')
                    if key=='except':
                        self._attrs['search']['except'].extend(value.split(':'))
                    else:
                        raise UserException('Unknown noskip_intrinsic option: %s' % comp)

        if opts.skip_intrinsic:
            self._attrs['search']['skip_intrinsic'] = True
            for line in opts.skip_intrinsic:
                for skip in line.lower().split(','):
                    key, value = skip.split('=')
                    if key=='except':
                        self._attrs['search']['except'].extend(value.split(':'))
                    else:
                        raise UserException('Unknown skip_intrinsic option: %s' % comp)

        # parsing include parameters
        if opts.include:
            for inc in opts.include:
                inc_eq = inc.split('=')
                if len(inc_eq)==1:
                    for inc_colon in inc_eq[0].split(':'):
                        self._attrs['include']['path'].append(inc_colon)
                elif len(inc_eq)==2:
                    # TODO: support path for each file
                    pass
                else: raise UserException('Wrong format include: %s'%inc)

        if opts.include_ini:
            process_include_option(opts.include_ini, self._attrs['include'])

        # parsing macro parameters
        if opts.macro:
            for line in opts.macro:
                for macro in line.split(','):
                    macro_eq = macro.split('=')
                    if len(macro_eq)==1:
                        self._attrs['include']['macro'][macro_eq[0]] = '1'
                    elif len(macro_eq)==2:
                        self._attrs['include']['macro'][macro_eq[0]] = macro_eq[1]
                    else: raise UserException('Wrong format include: %s'%inc)


        if opts.outdir:
            self._attrs['path']['outdir'] = opts.outdir
        # create state directories and change working directory
        if os.path.exists(self._attrs['path']['outdir']):
            map( os.unlink, [os.path.join(opts.outdir ,f) for f in os.listdir(opts.outdir)] ) 
        else:
            os.makedirs(self._attrs['path']['outdir'])

        if opts.workdir:
            self._attrs['path']['workdir'] = opts.workdir
        # create state directories and change working directory
        if os.path.exists(self._attrs['path']['workdir']):
            rmtree(self._attrs['path']['workdir'])

        if opts.refdir:
            self._attrs['path']['refdir'] = opts.refdir

        # support only a single directory 
        if opts.srcdir and os.path.exists(opts.srcdir):
            srcdir = opts.srcdir
            self._attrs['path']['srcdir'] = srcdir
            abssrcdir = os.path.abspath(srcdir)
            srcfiles = [ f for f in os.listdir(abssrcdir) if os.path.isfile(os.path.join(abssrcdir,f)) ]
            for srcfile in srcfiles:
                if srcfile[0]=='.': continue
                srcpath = os.path.join(abssrcdir,srcfile)
                dstpath = srcpath + '.oc_org'
                #dstpath = os.path.join(self._attrs['path']['outdir'], srcfile)
                self._attrs['inputfile'].append(os.path.abspath(srcpath))
                if not os.path.exists(dstpath):
                    copyfile(srcpath, dstpath)
                #if os.path.exists(dstpath):
                #    os.remove(dstpath)
                #os.symlink(srcpath, dstpath)

        # timeout
        if opts.timeout:
            value = int(opts.timeout[:-1])
            unitchar = opts.timeout[-1].lower()
            unit_seconds = unit_conv[unitchar]
            self._attrs['misc']['timeout'] = value * unit_seconds


        # no logging
        if opts.nologging:
            self._attrs['logging']['enabled'] = False

        # parsing debugging options
        if opts.debug:
            for dbg in opts.debug:
                param_path, value = dbg.split('=')
                param_split = param_path.lower().split('.')
                value_split = value.lower().split(',')
                curdict = self._attrs
                for param in param_split[:-1]:
                    curdict = curdict[param]
                exec('curdict[param_split[-1]] = value_split')

    def __getattr__(self, name):
        return self._attrs[name]

#############################################################################
## LOGGING
#############################################################################

def check_logging(func):
    """ logging decorator to check if to continue to log """

    def func_wrapper(obj, msg, **kwargs):
        exe_func = True
        if Config.logging['select'].has_key('name'):
            if kwargs.has_key('name'):
                exe_func = False
                np1 = kwargs['name'].namepath.lower()
                for np2 in Config.logging['select']['name']:
                    np1_split = decode_NS(np1).split('.')
                    np2_split = np2.split('.')
                    minlen = min(len(np1_split), len(np2_split))
                    if np1_split[-1*minlen:]==np2_split[-1*minlen:]:
                        exe_func = True
                        break

        if kwargs.has_key('stmt'):
            stmt = kwargs['stmt']
            msg += ' at %s in %s' % ( str(stmt.item.span), stmt.item.reader.id )

        # prerun
        if kwargs.has_key('stdout') and kwargs['stdout']:
            print msg

        # execute func
        if exe_func or func.__name__ in [ 'error', 'critical']:
            func(obj, msg)

        # postrun

    return func_wrapper

@singleton
class Logger(object):
    """ OpenCase logger """

    def __init__(self):
        import logging
        import logging.config
        logconfig_path = os.path.join(os.path.dirname(__file__),'log.config')
        logging.config.fileConfig(logconfig_path)
        self.logger = logging.getLogger('opencase')
        if not Config.logging['enabled']:
            logging.disable(logging.CRITICAL)

    def _pack_msg(self, msg):
        import traceback
        import inspect

        #import pdb; pdb.set_trace()
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = traceback.format_tb(exc_traceback)
        if len(tb)>0:
            return str(msg) + '\n' + '\n'.join(tb)
        else:
            frame=inspect.currentframe()
            frame=frame.f_back.f_back.f_back
            code=frame.f_code
            return '%s:%d - %s'%(os.path.basename(code.co_filename), frame.f_lineno, str(msg))

    @check_logging
    def debug(self, msg, **kwargs):
        self.logger.debug(self._pack_msg(msg))

    @check_logging
    def info(self, msg, **kwargs):
        self.logger.info(self._pack_msg(msg))

    @check_logging
    def warn(self, msg, **kwargs):
        self.logger.warn(self._pack_msg(msg))

    @check_logging
    def error(self, msg, **kwargs):
        self.logger.error(self._pack_msg(msg))

    @check_logging
    def critical(self, msg, **kwargs):
        self.logger.critical(self._pack_msg(msg))


import unittest
class Test_oc_utils(unittest.TestCase):

    def setUp(self):
        pass

    def test_exec_cmd(self):
        output = exec_cmd('echo "TestOK"')
        self.assertEqual( output, "TestOK\n")


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])
