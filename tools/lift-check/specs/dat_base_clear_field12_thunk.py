"""The real forwarding entry delegates to the common count clear helper."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from dat_base_clear_field12 import inputs
from liftcheck.spec import *
FUNCTION = 'datBase_ClearField12_Thunk'
ADDRESS = 0x82494128
SOURCE = 'src/rage/core/rage_core_utils.cpp'
TRIALS = 500
CALLS = {'datBase_ClearField12': run(args=('r3',))}
