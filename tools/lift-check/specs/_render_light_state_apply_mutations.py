"""From the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_render_light_state_apply_mutations.py

Compile broken copies in the build cache. Every mutation must produce a
behavioral FAIL; BUILD/SPEC/UNSUPPORTED never count as detection.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("omit applied-state snapshot", "    game_E0A8(&lbl_825CA610, state);",
     "    /* omitted snapshot */"),
    ("unsigned light count", "const int count = state->count;",
     "const int count = static_cast<uint16_t>(state->count);"),
    ("wrong directional render mode", "mode == 2 && light.flags[0] == 0",
     "mode != 2 && light.flags[0] == 0"),
    ("use position for directional lights", "light.vectors[directional ? 1 : 0].bits",
     "light.vectors[0].bits"),
    ("keep source position w", "position[i].lane[3] = light.scalars[1];",
     "/* omitted position w replacement */"),
    ("keep source diffuse w", "diffuse[i].lane[3] = light.scalars[0];",
     "/* omitted diffuse w replacement */"),
    ("negate diffuse w too", "lane == 3 ? lbl_8202D108 : lbl_825C5938",
     "lbl_825C5938"),
    ("keep VMX subnormals", "        bits &= 0x80000000u;",
     "        /* omitted VMX flush */"),
    ("accept only canonical diffuse flag", "if (light.flags[2] != 0)",
     "if (light.flags[2] == 1)"),
    ("omit falloff sign", "diffuse[i].lane[3] *= lbl_825C5938;",
     "/* omitted falloff sign */"),
    ("invert uploaded light type", "type[i] = directional ? 0.0f : 1.0f;",
     "type[i] = directional ? 1.0f : 0.0f;"),
    ("stop before remaining failed lookups", 'lbl_825EBB18 = diffuseHandle = game_A2F8("Diffuse", 1);',
     'lbl_825EBB18 = diffuseHandle = game_A2F8("Diffuse", 1);\n        if (diffuseHandle == 0) return;'),
    ("omit position handle cache", 'lbl_825EBAAC = positionHandle = game_A2F8("Position", 1);',
     'positionHandle = game_A2F8("Position", 1);'),
    ("truncate diffuse upload", "game_A670(diffuseHandle, diffuse, count);",
     "game_A670(diffuseHandle, diffuse, count > 0 ? count - 1 : count);"),
    ("reverse dirty-bit order", "table->dirtyBits[bit >> 3] |= lbl_825D4C80[bit & 7];",
     "table->dirtyBits[bit >> 3] |= 1u << (bit & 7);"),
    ("clobber another count lane", "table->values[slot].lane[0] = static_cast<float>(count);",
     "table->values[slot].lane[0] = static_cast<float>(count);\n    table->values[slot].lane[1] = 0.0f;"),
    ("wrong inline write count", "g_grmShaderFx_boundContext += 3;",
     "g_grmShaderFx_boundContext += 2;"),
    ("upload diffuse as ambient", "memcpy(table->values[slot].lane, state->ambient.bits, 16);",
     "memcpy(table->values[slot].lane, state->lights[0].vectors[2].bits, 16);"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/pong_render.cpp").read_text()
    spec = Path(__file__).with_name("render_light_state_apply.py")
    caught = 0
    for name, old, new in MUTATIONS:
        # The dirty-bit expression intentionally occurs once for each inline
        # write; patch the first, matching build_lift's single replacement.
        expected = 2 if name == "reverse dirty-bit order" else 1
        assert source.count(old) == expected, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
