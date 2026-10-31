from specs._network_wave_acquire_cases import *
FUNCTION='xactCue_AcquireWave'
ADDRESS=0x82456D70
def inputs(t): t.args(r3=cue(t))
