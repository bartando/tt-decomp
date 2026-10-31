"""All 16 entries, singular/dependent rows, cancellation, scale and permutations.
Reuse inverse inputs, compare exact float return and unchanged matrix/guards.
"""
from specs.rage_mat44_inverse import inputs as inverse_inputs
FUNCTION = "rage::mat44Determinant"
ADDRESS = 0x8223F008
SOURCE = "src/rage/math/mat44.cpp"
TRIALS = 1500
FP_CONTRACT = "off"

def inputs(t):
    inverse_inputs(t)
    t.args(r3=t.reg_args["r4"])
