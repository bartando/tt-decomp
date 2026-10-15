"""rage::fiAsciiTokenizer::SetIndentDepth (0x820C2E08), slot 30."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::SetIndentDepth"
ADDRESS = 0x820C2E08


def inputs(t):
    obj = tokenizer(t)
    t.args(r3=obj, r4=t.rng.getrandbits(32))
