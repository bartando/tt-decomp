"""Verify the void-pointer shim used by cm_operators against the same PPC entry.

Reuse the canonical port cases. The forwarding call executes the real evaluator
and is transparent because the original entry already is that evaluator.
"""
from pathlib import Path
import runpy
from liftcheck.spec import run

_base = runpy.run_path(str(Path(__file__).with_name("cm_node_get_dim.py")))
FUNCTION = "cmNode_GetDim_stub"
ADDRESS = _base["ADDRESS"]
SOURCE = "src/rage/animation/cm_shims.cpp"
TRIALS = _base["TRIALS"]
inputs = _base["inputs"]
CALLS = {**_base["CALLS"], "rage::cmNode_GetDim": run(transparent=True)}
