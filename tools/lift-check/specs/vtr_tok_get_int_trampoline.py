"""rage::fiAsciiTokenizer::GetIntTrampoline (0x822E5E78), slot 2: tail-calls slot 4."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::GetIntTrampoline"
ADDRESS = 0x822E5E78

CALLS = {
    "tok.vfn_4": stub(),
}


def inputs(t):
    obj = tokenizer(t)
    t.args(r3=obj)
