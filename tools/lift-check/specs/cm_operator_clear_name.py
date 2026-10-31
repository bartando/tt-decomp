"""Full type/ownership matrix, null pointers, unrelated flags and node guards.
String duplication/free are observed boundaries; their algorithms are outside
this node proof. Compare all writes and calls without tolerance or ignored bytes.
"""
from specs._parameter_node_inputs import LEAF_CALLS, node, text, copy_flag, real
FUNCTION = "cmOperator_ClearName"
ADDRESS = 0x8223a258
SOURCE = "src/rage/data/parameter_node.cpp"
TRIALS = 600
CALLS = LEAF_CALLS

def inputs(t):
    t.args(r3=node(t))
