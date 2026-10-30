"""GPU watchdog: reported flag, queue/fiber progress, timeout and hang bookkeeping.

Cover elapsed ticks 0/1/1999/2000/2001 and unsigned wraparound, independent
queue snapshots and rollback values, every flag bit, matching/mismatched fiber
IDs, zero/nonzero progress gates, and unset/already-set global hang sentinels.
The TLS/fiber accessor runs as original code; diagnostic callees are stubs whose
arguments (including the banner text) are compared. All writes compare exactly.

Limits: valid device, state, queue and TLS pointers; diagnostics do not mutate
the device. Timeout cases have a nonnull diagnostic context: the null-context
timeout path deliberately traps, which lift-check reports as a SPEC fault rather
than comparing trap outcomes. Null contexts are covered on returning paths.
"""
from liftcheck.spec import *

FUNCTION = "D3DDeviceXenon_ReportGPUHang"
ADDRESS = 0x823643E0
SOURCE = "src/graphics/grc_gpu_hang.cpp"

EXTERNS = {
    "xe_GetCurrentThreadId": 0x82566B78,
    "rage_DebugPrintf": 0x82363FE0,
    "g_gpuHangSentinel": 0x82606654,
    "g_sda_base": 0x82600000,
    "rage::k_str_d3d_hang_try_instrumented": 0x82066510,
    "rage::k_str_d3d_hang_breaking_into_debugger": 0x820665E8,
}
CALLS = {
    0x82566B78: run(),
    0x82363FE0: stub(ret="void", args=("r3",)),
    0x82364258: stub(ret="void", args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    rng = t.rng
    state = t.alloc(12, "hangState")
    device = t.alloc(0x5014, "device")
    queue = t.alloc(4, "queueHead")
    sda = t.alloc(0x104, "r13")
    tls = t.alloc(0x150, "tls")
    diagnostic = t.alloc(12, "diagnosticContext")

    now = rng.choice([0, 1, 1999, 2000, 0x7FFFFFFF, 0xFFFFFFFF, t.u32()])
    elapsed = rng.choice([0, 1, 1999, 2000, 2001, 0x7FFFFFFF, 0x80000000,
                          0xFFFFFFFF, t.u32()])
    head = rng.choice([0, 1, 2, 0xFFFFFFFF, t.u32()])
    previous_head = rng.choice([head, head, (head + 1) & 0xFFFFFFFF])
    fiber = t.u32()
    device_fiber = rng.choice([fiber, fiber ^ 1])
    gate = rng.choice([0, 0, 1, 0x80000000, t.u32()])
    flags = rng.randrange(256)
    timed_out = (previous_head == head and not (device_fiber == fiber and gate)
                 and elapsed >= 2000 and not flags & 4)

    t.w32(state, device)
    t.w32(state + 4, now - elapsed)
    t.w32(state + 8, previous_head)
    t.w32(device + 0x2888, device_fiber)
    # Poison the old lift's misplaced queue pointer while keeping it readable.
    t.w32(device + 0x288C, t.alloc(4, "wrongQueueOffset"))
    t.w32(device + 0x2890, queue)
    t.w32(device + 0x289C, rng.choice([0, 1, 2, 0xFFFFFFFF, t.u32()]))
    t.w8(device + 0x28C1, flags)
    t.w32(device + 0x28F8, gate)
    t.w32(device + 0x354C, diagnostic if timed_out else rng.choice([0, diagnostic]))
    t.w32(queue, head)
    t.w32(sda + 0x100, tls)
    t.w32(tls + 0x58, now)
    t.w32(tls + 0x14C, fiber)
    t.w32(0x82600000, sda)
    t.w32(0x82606654, rng.choice([0, 0, 15, 1, 0xFFFFFFFF, t.u32()]))
    t.args(r3=state, r13=sda)
