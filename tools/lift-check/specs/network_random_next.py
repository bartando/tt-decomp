"""0x82568858: both wrapping transitions and the shared 128-word shuffle."""
from specs._network_random_cases import *
FUNCTION='rage::randomNext'
ADDRESS=0x82568858
def inputs(t): t.args(r3=setup_random(t)+0xAC)
