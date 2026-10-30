"""Run with PYTHONPATH=tools/lift-check and its venv Python from repo root.

Each patch affects only the checker's build copy and must produce FAIL.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("ignore null TLS", "if (!rsc || !*field)", "if (!*field)"),
    ("ignore null pointer", "if (!rsc || !*field)", "if (!rsc)"),
    ("exclude lower boundary", "if (at < rsc->m_base || at > rsc->m_base + rsc->m_size) {\n        *field = 0;\n        return;\n    }\n    rsc = CurrentResource();\n    const uint32_t value = *field;\n    if (value) {", "if (at <= rsc->m_base || at > rsc->m_base + rsc->m_size) {\n        *field = 0;\n        return;\n    }\n    rsc = CurrentResource();\n    const uint32_t value = *field;\n    if (value) {"),
    ("exclude upper boundary", "at > rsc->m_base + rsc->m_size) {\n        *field = 0;\n        return;\n    }\n    rsc = CurrentResource();\n    const uint32_t value = *field;\n    if (value) {", "at >= rsc->m_base + rsc->m_size) {\n        *field = 0;\n        return;\n    }\n    rsc = CurrentResource();\n    const uint32_t value = *field;\n    if (value) {"),
    ("wrong page", "const uint32_t page = (value - rsc->m_imageBase) / rsc->m_pageSize;\n        *field", "const uint32_t page = ((value - rsc->m_imageBase) / rsc->m_pageSize + 1) % 8;\n        *field"),
    ("skip relocation", "*field = reinterpret_cast<const uint32_t*>(rsc)[page + 2] + value;\n    }", "*field = value;\n    }"),
    ("wrong virtual slot", "(vtable[1])(object, rsc)", "(vtable[0])(object, rsc)"),
    ("wrong placer context", "(vtable[1])(object, rsc)", "(vtable[1])(object, object)"),
    ("omit placer", "reinterpret_cast<void (*)(void*, void*)>(vtable[1])(object, rsc);", "(void)vtable;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/data/dat_resource_fixup.cpp").read_text()
    spec = Path(__file__).with_name("dat_resource_place_pointer.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
        print(f'{"CAUGHT" if rc == 1 else "MISSED"} {name}: {output.getvalue().splitlines()[0]}', flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
