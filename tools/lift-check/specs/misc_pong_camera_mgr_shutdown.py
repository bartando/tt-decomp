"""pongCameraMgr::Shutdown (slot 24): deletes the shot manager singleton, both
sources and the camera-machine wrapper through vtable slot 0, then frees the
viewport array (delete[] with ~grcViewport inlined) and the single viewport,
clearing the current-viewport global if it pointed into either."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCameraMgr::Shutdown"
ADDRESS = 0x82165F30
SOURCE = "src/game/camera/pong_camera.cpp"
EXTERNS = {"sysMemAllocator_Free": 0x820C00C0}

CALLS = {
    0x820C00C0: stub(ret="void"),
    **{f"{n}.vfn_0": stub(ret="void", args=("r3", "r4"))      # scalar deleting dtor, flag 1
       for n in ("shotMgr", "source0", "source1", "cmCamera")},
}


def obj(t, name):
    if t.rng.random() < 0.25:
        return 0
    o = t.alloc(0x10, name)
    t.w32(o, t.vtable(name, 2))
    return o


def inputs(t):
    rng = t.rng
    mgr = t.alloc(0x370, "mgr")
    t.w32(0x8271A318, obj(t, "shotMgr"))
    t.w32(mgr + 0x20, obj(t, "source0"))
    t.w32(mgr + 0x24, obj(t, "source1"))
    t.w32(mgr + 0x34, obj(t, "cmCamera"))

    cands = [0, rng.getrandbits(32)]
    if rng.random() < 0.8:
        n = rng.choice([0, 1, 2, 3])
        block = t.alloc(16 + 0x390 * n, "slots", fill="zero")
        t.w32(block, n)
        slots = block + 16
        cands += [slots + 0x390 * k for k in range(n)]
    else:
        slots = 0
    t.w32(mgr + 0x18, slots)
    vp = t.alloc(0x390, "viewport", fill="zero") if rng.random() < 0.8 else 0
    t.w32(mgr + 0x14, vp)
    cands += [vp]
    t.w32(0x825EBAA0, rng.choice(cands))
    t.args(r3=mgr)
