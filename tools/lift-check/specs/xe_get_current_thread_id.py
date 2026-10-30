from liftcheck.spec import *

FUNCTION = "xe_GetCurrentThreadId"
ADDRESS = 0x82566B78
SOURCE = "src/crt/xe_thread.c"
TRIALS = 1000
EXTERNS = {"g_sda_base": 0x82600000}


def inputs(t):
    sda = t.alloc(0x104, "sda")
    thread = t.alloc(0x150, "thread")
    other = t.alloc(0x150, "other_thread")
    t.w32(other + 0x14c, 0xdeadbeef)
    t.w32(sda + 0xfc, other)
    t.w32(sda + 0x100, thread)
    t.w32(thread + 0x14c, t.rng.choice((0, 1, 0xffffffff, t.u32())))
    t.w32(t.sym("g_sda_base"), sda)
    t.args(r13=sda)
