"""cmMultiply slot 4: ordered real port reads followed by float32 multiplication."""
from specs._cm_binary_float_inputs import CALLS, inputs

FUNCTION = "rage::cmMultiply::GetFloat"
ADDRESS = 0x8227B2F0
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1200
RET = None
