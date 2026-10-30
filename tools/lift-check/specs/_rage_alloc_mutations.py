"""Deliberately break allocator dispatch; patches affect build-cache copies only.

Run with PYTHONPATH=tools/lift-check and the lift-check venv's Python.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("skip thread initialization", "    sysMemAllocator_InitThreadHeap();", "    // initialization omitted"),
    ("use secondary allocator", "void* allocator = tls[1];", "void* allocator = tls[2];"),
    ("wrong virtual slot", "reinterpret_cast<Allocate>(vtable[1])", "reinterpret_cast<Allocate>(vtable[2])"),
    ("truncate request", "(allocator, size, 16)", "(allocator, size & 0xffffu, 16)"),
    ("wrong alignment", "(allocator, size, 16)", "(allocator, size, 8)"),
    ("reject zero-sized request", "    sysMemAllocator_InitThreadHeap();", "    if (size == 0) return nullptr;\n    sysMemAllocator_InitThreadHeap();"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/core/rage_core_utils.cpp").read_text()
    before, target = source.split('void* rage_Alloc(unsigned int size) {', 1)
    target, after = target.split('// Same entry, declared with a signed size', 1)
    for name, old, new in MUTATIONS:
        assert target.count(old) == 1, name
        mutated = (before + 'void* rage_Alloc(unsigned int size) {' + target.replace(old, new)
                   + '// Same entry, declared with a signed size' + after)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name('rage_alloc.py'),
                         Options(trials=128, seed=1, patches=((source, mutated),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
