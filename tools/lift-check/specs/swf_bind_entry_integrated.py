"""Real context selection, hash lookup and pooled insertion; compare every write."""
from specs._swf_group_integrated_inputs import CALLS, setup
FUNCTION = 'SinglesNetworkClient_BindEntry'
ADDRESS = 0x823F9318
SOURCE = 'src/rage/swf_page_group.cpp'
TRIALS = 1000


def inputs(t):
    group = setup(t)
    key = t.rng.choice([b'possible', b'completed', b'time_low', b'arrow_direction'])
    t.args(r3=group, r4=t.alloc(len(key) + 1, 'key', fill=key + b'\0'))
