"""Exact reference/ownership state and release order, including null pointers,
byte-count underflow and reentrant callback writes. Allocation release and debug
traps are observed boundaries; all memory and calls compare with no ignored bytes.
"""
from specs._grc_release_inputs import HOLDER_CALLS, holder_input
FUNCTION = "grcDevice_cleanupInternal"
ADDRESS = 0x82151068
SOURCE = "src/graphics/grc_resource_release.cpp"
TRIALS = 1000
CALLS = HOLDER_CALLS
inputs = holder_input
