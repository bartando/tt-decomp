"""Seven register groups: every boundary bit, full/zero/random masks, and
callee changes to current/later groups. Reuse the existing full logical call
observer to compare all 64 mask bits, register offsets, source bytes and state.
Register packet generation itself is an observed boundary, not executed.
"""
from specs import grc_device_flush_dirty_state as shared
FUNCTION = "grc_3E20"
ADDRESS = 0x82363E20
SOURCE = "src/graphics/grc_state_helpers.cpp"
TRIALS = 1200
CALLS = {0x82362658: shared.boundary("registers", 256)}

def inputs(t):
    shared.inputs(t)
