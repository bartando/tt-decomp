"""Exact reference/ownership state and release order, including null pointers,
byte-count underflow and reentrant callback writes. Allocation release and debug
traps are observed boundaries; all memory and calls compare with no ignored bytes.
"""
from specs._grc_release_inputs import SHARED_CALLS, shared_input
FUNCTION = "grcDevice_releaseSharedResources"
ADDRESS = 0x8214f338
SOURCE = "src/graphics/grc_resource_release.cpp"
TRIALS = 1000
CALLS = SHARED_CALLS
inputs = shared_input
