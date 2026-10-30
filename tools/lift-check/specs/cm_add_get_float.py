"""cmAdd slot 4: ordered evaluation of both real ports, then float32 addition."""
from specs._cm_binary_float_inputs import CALLS, inputs

FUNCTION = "rage::cmAdd::GetFloat"
ADDRESS = 0x8227B100
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1200
RET = None
