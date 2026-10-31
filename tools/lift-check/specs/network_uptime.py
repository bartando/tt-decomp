"""0x82566F98: the imported bundle's +0x10 word, with full uint32 wrap range."""
from liftcheck.spec import *
FUNCTION = "atSingleton_6F98_g"
ADDRESS = 0x82566F98
SOURCE = "src/xam/time_stamp.cpp"
TRIALS = 400

def _bundle(ctx):
    ctx.ret(r3=0x45000000)
HOST = {"hostGetKeTimeStampBundle": model(_bundle, args=(), transparent=True)}

def inputs(t):
    bundle = t.map(0x45000000, 0x1000, 'kernel timestamp bundle')
    t.w32(0x8200084C, bundle)
    t.w32(bundle + 0x10, t.rng.choice([0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, t.u32()]))
    t.args()
