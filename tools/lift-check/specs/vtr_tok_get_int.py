"""rage::fiAsciiTokenizer::GetInt (0x822E5E88), slot 4: token, then strtol on '-' or a digit."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::GetInt"
ADDRESS = 0x822E5E88

CALLS = {
    "tok.vfn_1": GET_TOKEN,
    "_xe_strcpyn_10": stub(),
}


def inputs(t):
    obj = tokenizer(t)
    t.args(r3=obj)
