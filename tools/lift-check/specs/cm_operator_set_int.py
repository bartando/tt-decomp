"""Append one initialized child, set its name/value, then clear owner flag 2.
Exercise allocation failure, arbitrary flags and slot redirection during name
assignment. Run retail operator-new transparently, observing heap init and the
real allocator ABI. Downstream setters remain checked call boundaries.
"""
from specs._parameter_node_inputs import WRAPPER_CALLS, wrapper, text, copy_flag, real
FUNCTION = "cmOperator_SetInt"
ADDRESS = 0x822395f0
SOURCE = "src/rage/data/parameter_node.cpp"
TRIALS = 600
EXTERNS = {'g_sda_base': 0x82600000}
CALLS = WRAPPER_CALLS

def inputs(t):
    t.args(r3=wrapper(t), r4=text(t), r5=t.u32(), r6=copy_flag(t))
