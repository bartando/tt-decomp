"""X-offset stroke position, centerline UVs and the real 36-byte vertex writer."""
from liftcheck.spec import *
from specs._swf_line_inputs import vertex_inputs as inputs

FUNCTION = "rage::swfEmitLineVertexOffsetX"
ADDRESS = 0x82406620
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
RET = None
CALLS = {0x82406010: run(args=("f1", "f2"))}
