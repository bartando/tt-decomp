"""Render-state cache hit/miss, override gate, and all forwarded arguments."""
from liftcheck.spec import *

FUNCTION = "rage_ApplyDeviceRenderState"
ADDRESS = 0x820EE910
SOURCE = "src/rage/rage_system.cpp"
TRIALS = 1200
RET = None
EXTERNS = {"g_lastRenderStateId": 0x825EB98C, "g_renderStateDevice": 0x825EB988,
           "g_iccProfilePtr": 0x8260634C}
CALLS = {"rage_UpdateDeviceState": stub(ret="void", args=("r3",)),
         "rage_ApplyRenderState": stub(ret="void", args=("r3", "r4", "r5", "r6"))}


def inputs(t):
    r = t.rng
    obj = t.alloc(40, "state")
    state_id = t.u32()
    t.w32(obj, t.u32())
    t.w32(obj + 4, state_id)
    t.w32(obj + 32, t.u32())
    t.w8(obj + 37, r.choice((0, 1, 2, 128, 255)))
    t.w8(obj + 39, r.randrange(256))
    t.w32(EXTERNS["g_lastRenderStateId"], r.choice((state_id, state_id ^ 1, t.u32())))
    t.w32(EXTERNS["g_renderStateDevice"], t.u32())
    t.w32(EXTERNS["g_iccProfilePtr"], t.u32())
    t.args(r3=obj)
