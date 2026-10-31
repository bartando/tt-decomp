from specs._network_key_cases import *
FUNCTION='msgSink_MatchesKey'
ADDRESS=0x82458D28
def inputs(t): t.args(r3=inner(t),r4=key(t))
