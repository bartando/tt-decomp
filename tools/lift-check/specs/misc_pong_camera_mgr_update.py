"""pongCameraMgr::Update (slot 27): per-frame camera tick. Everything it calls
is stubbed; the spec checks the calls, their arguments and the globals it sets."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCameraMgr::Update"
ADDRESS = 0x82166118
SOURCE = "src/game/camera/pong_camera.cpp"


def find_flag(ctx):
    """0x82274870: name lookup; null or an entry whose +0x20 byte is the flag."""
    if ctx.rng.random() < 0.3:
        return 0
    e = ctx.alloc(0x24)
    ctx.write(e + 0x20, bytes([ctx.rng.choice([0, 1, 0xA5])]))
    return e


CALLS = {
    0x821722F8: stub(ret="void", args=("r3", "r4")),   # CMtoCSAdapter::PublishCameraMatrix
    0x82167180: stub(ret="void"),                      # game_7180
    0x82167558: stub(ret="void"),                      # pongCineCamMgr::StepActiveGovernor
    0x82274870: stub(ret=find_flag),
    0x8225E6E0: stub(ret="void", args=("r3", "r4", "r5", "r6")),
    0x821539F0: stub(ret="void", args=("r3", "r4")),   # grcViewport::SetCameraMtx
    0x82166280: stub(ret="void"),                      # pongCameraMgr_6280_g
}


def inputs(t):
    rng = t.rng
    mgr = t.alloc(0x370, "mgr")
    srcs = []
    for k in range(2):
        s = t.alloc(0x140, f"source{k}")
        t.w32(s, t.vtable(f"source{k}"))
        t.w32(s + 0x98, t.alloc(0x390, f"source{k}.viewport"))
        t.w32(mgr + 0x20 + 4 * k, s)
        srcs.append(s)
    t.w32(mgr + 0x1C, rng.choice([0, 1]))
    view = t.alloc(0x48, "camViewCS")
    t.w32(view, t.vtable("camViewCS"))
    t.w32(view + 0x2C, rng.choice(srcs))
    t.w32(mgr + 0x28, view)
    t.w32(mgr + 0x2C, t.alloc(0x40, "cine"))
    machine = t.alloc(0x40, "machine")
    t.w32(machine + 0x3C, t.alloc(0x10, "flagTable"))
    cm = t.alloc(0x20, "cmCamera")
    t.w32(cm + 4, machine)
    t.w32(mgr + 0x34, cm)

    shot = t.alloc(0x20, "shotMgr")
    t.w32(shot + 4, t.vtable("shotFsm"))
    cur = rng.randrange(8)
    t.w32(shot + 0x10, cur)
    t.w32(shot + 0x18, cur if rng.random() < 0.5 else rng.randrange(8))
    t.w32(0x8271A318, shot)
    t.w32(0x8271A32C, t.alloc(0x10, "sharedState"))
    t.args(r3=mgr)
