from liftcheck.spec import *

FUNCTION = "crtIsLeadByte"
ADDRESS = 0x8243A348
SOURCE = "src/crt/printf.cpp"
TRIALS = 1000
EXTERNS = {"crtLocaleData": 0x825B14D8}

def inputs(t):
    locale = t.alloc(204, "locale")
    table = t.alloc(512, "ctype table")
    for i in range(256): t.w16(table + 2*i, t.u32())
    t.w32(locale + 200, table)
    t.w32(EXTERNS["crtLocaleData"], locale)
    t.args(r3=t.rng.choice([0, 255, 256, -1, t.u32()]), r4=t.u32())
