"""GPU command-ring ownership wait and persistent watchdog state.

Exercise all modulo-four lags, end before/at/after the fence, full unsigned
cursor values and sequence wrap. Script immediate/later watchdog aborts,
one/multiple retries, changing queue pointers and fence progress. The watchdog
checks and mutates its persistent three-word state each time. All memory and
call arguments compare exactly; no ignored regions. The GPU/watchdog boundary
is modelled rather than relying on asynchronous hardware or a real hang.
Ground truth: disasm/sections/.text.s, 0x82359DC0..0x82359E78.
"""
from liftcheck.spec import model

FUNCTION = "grcDevice_CommitCommandSpace"
ADDRESS = 0x82359DC0
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1000
RET = None
EXTERNS = {"g_sda_base": 0x82600000,
           "D3DDeviceXenon_ReportGPUHang": 0x823643E0}

_device = _sequence = _end = 0
_queues = []
_initial = b""
_calls = {}
_mode = 0


def watchdog(ctx):
    n = _calls.get(ctx.side, 0)
    _calls[ctx.side] = n + 1
    state = ctx.r(3)
    expected = _initial if n == 0 else (_device.to_bytes(4, "big") +
                                       (0x12340000 + n).to_bytes(4, "big") +
                                       (0x56780000 + n).to_bytes(4, "big"))
    assert ctx.read(state, 12) == expected, "watchdog state was reset or misinitialized"
    assert n < 4, "wait failed to observe progress"
    ctx.write(state + 4, (0x12340001 + n).to_bytes(4, "big"))
    ctx.write(state + 8, (0x56780001 + n).to_bytes(4, "big"))
    queue = _queues[(n + 1) % len(_queues)]
    ctx.write(_device + 0x2890, queue.to_bytes(4, "big"))
    # Leave the new queue stalled for up to three calls, then release ownership.
    fence = ((_sequence - 2) & 3) | (_end & ~3)
    if n >= _mode:
        fence = _sequence & 3
    ctx.write(queue + 4, fence.to_bytes(4, "big"))
    # Some trials stop via watchdog before their fence is released.
    ctx.ret(r3=0 if (_mode == 3 and n == 1) or (_mode == 2 and n == 0) else 1)


CALLS = {0x823643E0: model(watchdog, args=("r3",), deref={"r3": 12})}


def inputs(t):
    global _device, _sequence, _end, _queues, _initial, _calls, _mode
    r = t.rng
    _calls = {}
    _mode = (t.index // 12) % 4
    _device = t.alloc(0x3800, "device")
    _queues = [t.alloc(16, f"gpuQueue{i}") for i in range(3)]
    sda = t.alloc(0x110, "threadRoot")
    thread = t.alloc(0x60, "kernelThread")
    t.w32(0x82600000, sda)
    t.w32(sda + 0x100, thread)
    tick, head = t.u32(), t.u32()
    t.w32(thread + 0x58, tick)
    t.w32(_device + 0x2890, _queues[0])
    _sequence = r.choice((0, 1, 2, 3, 0xfffffffe, 0xffffffff, t.u32()))
    lag = t.index % 4
    cursor = r.choice((0, 4, 0x7ffffffc, 0x80000000, 0xfffffffc, t.u32() & ~3))
    fence = cursor | ((_sequence - lag) & 3)
    _end = (cursor + (-4, 0, 4)[(t.index // 4) % 3]) & 0xffffffff
    t.w32(_queues[0], head)
    t.w32(_queues[0] + 4, fence)
    _initial = b"".join(v.to_bytes(4, "big") for v in (_device, tick, head))
    t.args(r3=_device, r4=_end, r5=_sequence, r13=sda)
