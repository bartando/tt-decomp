"""Run with PYTHONPATH=tools/lift-check and the lift-check venv's Python."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CASES = (
    ("xe_get_current_thread_id", "src/crt/xe_thread.c",
     "thread + 0x14C", "thread + 0x148"),
    ("rage_free", "src/crt/heap.c",
     "if (!ptr || (uint8_t)rage_FindSingleton(ptr))",
     "if (!ptr || !(uint8_t)rage_FindSingleton(ptr))"),
    ("movie_store_thread_id", "src/game/misc/pong_misc.cpp",
     "m_threadId = xe_GetCurrentThreadId();", "m_threadId = 0;"),
    ("sysmem_allocator_free_aligned", "src/rage/memory/rage_heap.c",
     "((uint32_t*)ptr)[-1]", "((uint32_t*)ptr)[0]"),
    ("link_check_button_pressed", "src/game/input/button_edges.cpp",
     "return ((b[1] ^ b[3]) & 0xFF) <= 0x7F;",
     "return ((b[0] ^ b[3]) & 0xFF) <= 0x7F;"),
    ("msg_msg_sink_84c0_gen", "src/game/network/pong_network_io.cpp",
     "if (current == owner) {", "if (current != owner) {"),
)

for spec, filename, old, new in CASES:
    source = (ROOT / filename).read_text()
    assert source.count(old) == 1
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((source, source.replace(old, new)),))).run()
    print(f"{'CAUGHT' if result == 1 else 'MISSED'} {spec}: {output.getvalue().splitlines()[0]}")
    if result != 1:
        raise SystemExit(1)
