"""rage::fiAsciiTokenizer::CloseAndFlush (0x822E6D00), slot 37: tail-calls slot 36 with padCount 0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::CloseAndFlush"
ADDRESS = 0x822E6D00

CALLS = {
    "tok.vfn_36": stub(args=('r3','r4','r5')),
}


def inputs(t):
    obj = tokenizer(t)
    nm = name(t)
    t.args(r3=obj, r4=nm)
