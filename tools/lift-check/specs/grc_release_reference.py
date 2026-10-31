"""Exact reference/ownership state and release order, including null pointers,
byte-count underflow and reentrant callback writes. Allocation release and debug
traps are observed boundaries; all memory and calls compare with no ignored bytes.
"""
from specs._grc_release_inputs import RESOURCE_CALLS, resource_input
FUNCTION = "grcResource_ReleaseRef"
ADDRESS = 0x82352ee0
SOURCE = "src/graphics/grc_resource_release.cpp"
TRIALS = 1000
CALLS = RESOURCE_CALLS
inputs = resource_input
