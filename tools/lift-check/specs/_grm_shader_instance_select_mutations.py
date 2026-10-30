"""Run from the repo root with PYTHONPATH=tools/lift-check and .venv/bin/python."""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = [
    ("ignore cached entry", "entryId == activeEntry", "true"),
    ("ignore context changes", "changed || g_grmShaderFx_boundParam != previous", "g_grmShaderFx_boundParam != previous"),
    ("skip unbind", "        grmShaderInstance_Unbind(previous);\n    }\n    if (entryId == 0)", "    }\n    if (entryId == 0)"),
    ("lose saved state", "old + 540) = *reinterpret_cast<uint32_t*>(old + 532)", "old + 540) = 0"),
    ("wrong entry index", "entries[(entryId >> 18) & 0x3FFF]", "entries[(entryId >> 19) & 0x3FFF]"),
    ("skip descriptor setup", "    rage_8C48(selected, *reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(descriptor + 12)));", "    (void)descriptor;"),
    ("skip upload", "    grmShaderInstance_FilterAndUploadParameters(active);", "    (void)active;"),
    ("retain instance on zero", "        g_grmShaderInstance_previous = 0;\n        return;\n    }\n    const uint32_t selected", "        return;\n    }\n    const uint32_t selected"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/rage_grm.cpp").read_text()
    spec = Path(__file__).with_name("grm_shader_instance_select.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=100, seed=1, patches=((old, new),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
