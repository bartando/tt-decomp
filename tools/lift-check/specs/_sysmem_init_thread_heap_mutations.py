"""Deliberate defects; patches apply to build-cache copies, never the source tree."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("old 2.75 MiB heap", "0x02C00000u", "0x002C0000u"),
    ("overwrite active allocator", "if (allocCtx[1] == NULL)", "if (1)"),
    ("test wrong initialization bit", "g_allocatorInitFlag & 1u", "g_allocatorInitFlag & 2u"),
    ("discard unrelated flag bits", "g_allocatorInitFlag |= 1u;", "g_allocatorInitFlag = 1u;"),
    ("omit active allocator", "allocCtx[1] = &g_mainThreadXtf;", "(void)allocCtx;"),
    ("omit saved allocator", "allocCtx[2] = &g_mainThreadXtf;", "(void)allocCtx;"),
    ("wrong exit callback", "atexit(xe_get_thread_ctx_36E8);", "atexit(sysMemAllocator_InitThreadHeap);"),
    ("publish guard after construction",
     "g_allocatorInitFlag |= 1u;\n            xe_alloc_thread_ctx_6CA8(&g_mainThreadXtf, 0x02C00000u, 0u);",
     "xe_alloc_thread_ctx_6CA8(&g_mainThreadXtf, 0x02C00000u, 0u);\n            g_allocatorInitFlag |= 1u;"),
)


def main():
    source = (Path(__file__).resolve().parents[3] / "src/crt/entry.c").read_text()
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, name
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("sysmem_init_thread_heap.py"),
                         Options(trials=128, seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
