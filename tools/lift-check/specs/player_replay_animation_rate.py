"""821CCBD0: replay speed curve, pause/selection gates, override and time scale.

All arithmetic runs in the lift and original, with exact float comparison;
no calls, ignored output, or fabricated lookup results. Directed ramp/hold/
tail boundaries are mixed with zero divisors, infinities and unordered values.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _animation_clock_common import *

FUNCTION = "util_CBD0"
ADDRESS = 0x821CCBD0


def inputs(t):
    t.args(r3=replay_inputs(t))
