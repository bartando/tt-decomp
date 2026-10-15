"""camViewCS::Update (slot 10): current viewport gets the source's matrix, then
m_viewport gets FOV, display aspect and clip planes (global or the source's)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "camViewCS::Update"
ADDRESS = 0x8216CD88
SOURCE = "src/game/camera/pong_camera.cpp"
EXTERNS = {"gameLoop_GetDisplayAspect": 0x82228EA0, "g_loop_obj_ptr": 0x825EAB30}

CALLS = {
    0x821539F0: stub(ret="void", args=("r3", "r4")),   # grcViewport::SetCameraMtx
    # A leaf that leaves f6/f7 alone; the original keeps the clip planes there
    # across the call, so it has to run rather than be stubbed (a stub
    # clobbers the volatile FPRs).
    0x82228EA0: run(),
    0x82153598: stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    view = t.alloc(0x48, "camViewCS", ctype="camViewCS")
    src = t.alloc(0xB0, "source", ctype="camBaseCS")
    t.floats(src + 0x10, 16, -20, 20)
    t.floats(src + 0xA4, 3, 0.1, 500)
    vp = t.alloc(0x390, "viewport", ctype="grcViewport")
    t.w32(view + 0x28, vp)
    t.w32(view + 0x2C, src)
    t.w8(view + 0x38, rng.choice([0, 1, 0x80]))
    t.floats(view + 0x3C, 2, 0.1, 500)
    t.w32(0x825EBAA0, t.alloc(0x390, "currentViewport"))
    loop = t.alloc(0x210, "gameLoop")
    t.w32(loop + 0x200, rng.randrange(6))
    t.wf32(loop + 0x204, rng.uniform(0.5, 2.0))
    t.w32(0x825EAB30, loop)
    t.args(r3=view)
