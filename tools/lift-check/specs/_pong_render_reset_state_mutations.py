"""From the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_pong_render_reset_state_mutations.py

Mutate build-cache copies only. Require behavioral FAIL (exit 1) for every
mutation; BUILD, SPEC and UNSUPPORTED do not count as detection.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("include pass zero in depth enable", "static_cast<uint32_t>(pass) - 1u <= 15u",
     "static_cast<uint32_t>(pass) <= 16u"),
    ("only accumulate render dirty bits",
     "dirty = applied[index] == value ? dirty & ~bit : dirty | bit;",
     "dirty |= applied[index] == value ? 0 : bit;"),
    ("omit baseline render write", "        defaults[index] = value;", ""),
    ("exclude pass 4 from full colour", "pass >= 4 && pass < 17", "pass > 4 && pass < 17"),
    ("cull pass 14", "static_cast<uint32_t>(pass) - 13u <= 1u ? 0 : 2",
     "static_cast<uint32_t>(pass) == 13u ? 0 : 2"),
    ("skip the eighth texture", "slot < 8", "slot < 7"),
    ("pack texture dirty bits contiguously", "1u << (slot * 4)", "1u << slot"),
    ("omit device sampler reset", "    game_5450();", ""),
    ("swap shadow textures", "pass == 18 ? 980 : 976", "pass == 18 ? 976 : 980"),
    ("upload a zero shadow handle", "if (handle != 0)", "if (true)"),
    ("invert format selection", "g_grcFormatId == 0x1A220197u", "g_grcFormatId != 0x1A220197u"),
    ("skip final render table entry", "i < 87", "i < 86"),
    ("update duplicate render keys too", "                break;", "                continue;"),
    ("skip final sampler table entry", "i < 20", "i < 19"),
    ("scan past sampler table end", "i < 20", "i < 21"),
    ("accept only canonical LOD flag", "*reinterpret_cast<const uint8_t*>(0x826064E2u) != 0",
     "*reinterpret_cast<const uint8_t*>(0x826064E2u) == 1"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/pong_render.cpp").read_text()
    begin = source.index("void pongRender_ResetState(int32_t pass) {")
    end = source.index("\n// ──", begin)
    function = source[begin:end]
    spec = Path(__file__).with_name("pong_render_reset_state.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert old in function, f"mutation anchor changed: {name}"
        # Replace once, so the cull predicate and duplicate-key mutations each
        # break one path independently rather than modifying both tables.
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
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
