"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_draw_bucket_layer_render_mutations.py

Only patch build-cache copies. Every mutant must compile and produce behavioral
FAIL (exit 1); BUILD, SPEC and UNSUPPORTED are not successful detections.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("skip disabled-layer callbacks", "if (void* callback = callbacks[beforeCallback * 2])",
     "if (void* callback = enabled ? callbacks[beforeCallback * 2] : nullptr)"),
    ("wrong after callback", "callbacks[afterCallback * 2]", "callbacks[beforeCallback * 2]"),
    ("accept only canonical enabled byte", "if (enabled != 0)", "if (enabled == 1)"),
    ("read frame after reset",
     "const uint32_t frame = *reinterpret_cast<const uint32_t*>(0x825C4898u);\n"
     "        pongRender_ResetState(pass);",
     "pongRender_ResetState(pass);\n"
     "        const uint32_t frame = *reinterpret_cast<const uint32_t*>(0x825C4898u);"),
    ("wrong scratch count", "defaults.count = 3;", "defaults.count = 2;"),
    ("drop the second reset", "        pongLightState_Reset(&defaults, -1);\n", ""),
    ("omit ambient w", "lane < 4", "lane < 3"),
    ("split every sort mode", "&& sortMode == 4", "&& sortMode != 4"),
    ("swap registry key sources", "loop[576] != 0", "loop[576] == 0"),
    ("reject registry key zero", "key >= 0", "key > 0"),
    ("traverse insertion order", "order[frame][i]", "i"),
    ("treat light zero as unlit", "phase == 0 && light >= 0", "phase == 0 && light > 0"),
    ("swap light states", "weight > threshold ? 3552 : 208", "weight > threshold ? 208 : 3552"),
    ("wrong equality threshold", "weight > threshold", "weight >= threshold"),
    ("wrong unordered threshold", "weight > threshold", "!(weight <= threshold)"),
    ("wrong light-state stride", "lighting + light * 544 + offset", "lighting + light * 540 + offset"),
    ("wrong draw pass", "(entry, pass);", "(entry, pass + 1);"),
    ("omit single-pass default restore", "                        if (!twoPasses)\n",
     "                        if (false)\n"),
    ("omit shader override publication", "shaderOverride = *reinterpret_cast<void**>(manager + 84);",
     "/* omitted override */"),
    ("omit override restore", "shaderOverride = savedOverride;", "/* omitted restore */"),
    ("flush override too late", "                cmOperatorCtor_0B50_w(*reinterpret_cast<void**>(manager + 84));",
     "                shaderOverride = savedOverride;\n"
     "                cmOperatorCtor_0B50_w(*reinterpret_cast<void**>(manager + 84));"),
    ("skip manager reload", "                manager = *reinterpret_cast<uint8_t**>(0x826064F4u);",
     "/* omitted manager reload */"),
    ("skip device command", "if (pass == -1)", "if (pass == -2)"),
    ("grow at exact capacity", "+ 4 > reinterpret_cast<uintptr_t>(end)",
     "+ 4 >= reinterpret_cast<uintptr_t>(end)"),
    ("wrong command word", "*cursor = 0x84000000u;", "*cursor = 0x80000000u;"),
    ("omit cursor advancement", "= cursor + 1;", "= cursor;"),
    ("retain cleared device flag", "& 0xDDu", "& 0xFDu"),
    ("set high half of dirty mask", "|= 0x20000000ull;", "|= 0x2000000000000000ull;"),
    ("invert device flush", "(device[10432] & 1) != 0", "(device[10432] & 1) == 0"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/pong_render.cpp").read_text()
    begin = source.index("void pongDrawBucketLayer::Render(int32_t pass) {")
    end = source.index("\n// ──", begin)
    function = source[begin:end]
    spec = Path(__file__).with_name("draw_bucket_layer_render.py")
    for name, old, new in MUTATIONS:
        assert old in function, f"mutation anchor changed: {name}"
        mutant = function.replace(old, new, 1)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((function, mutant),))).run()
        lines = output.getvalue().splitlines()
        first = lines[0] if lines else "no checker output"
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
