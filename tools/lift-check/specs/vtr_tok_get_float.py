"""rage::fiAsciiTokenizer::GetFloat (0x822E5F08), slot 5: token, then strtod on '-', '.' or a digit."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::GetFloat"
ADDRESS = 0x822E5F08

CALLS = {
    "tok.vfn_1": GET_TOKEN,
    "jumptable_2B80": stub(),
}


def inputs(t):
    obj = tokenizer(t)
    t.args(r3=obj)
