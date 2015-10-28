# oc_state.py

from oc_utils import Logger, Config, singleton

@singleton
class State(object):
    mod_num = 1
    def __init__(self):
        # module number

        # attributes holder
        self._attrs = {}

        # source files
        self._attrs['inputfile'] = []

        # common directives
        self._attrs['direct'] = {}

        # cases object
        self._attrs['cases'] = {}
        self._attrs['cases']['size'] = 1
        self._attrs['cases']['mgr'] = None

        # opencase operation details
        self._attrs['operation'] = {}
        self._attrs['operation']['begin'] = None
        self._attrs['operation']['end'] = None
        
        # qualities achived
        self._attrs['quality'] = {}
        self._attrs['quality']['ref'] = None
        self._attrs['quality']['best'] = None

        # algirithm details
        self._attrs['algorithm'] = {}
        self._attrs['algorithm']['rand'] = {}
        self._attrs['algorithm']['dtree'] = {}
        self._attrs['algorithm']['dtree']['initial_weight'] = 1.0

        # characteristics of search result
        self._attrs['feature'] = {}

    def __getattr__(self, name):
        return self._attrs[name]

class ResState(object):
    ( NOT_STARTED, RESOLVED ) = range(2)

    def __init__(self, uname, org, resolvers):
        self.state = self.NOT_STARTED
        self.uname = uname
        self.originator = org
        self.resolvers = resolvers
        self.temp_uname = None
        self.res_stmt = None

    def set_uname(self, uname):
        self.temp_uname = self.uname
        self.uname = uname

    def reset_uname(self):
        self.uname = self.temp_uname
        self.temp_uname = None

import unittest
class Test_oc_state(unittest.TestCase):

    def setUp(self):
        pass

    def test_true(self):
        pass

if __name__ == "__main__":
    import sys
    unittest.main(argv=[sys.argv[0]])

