"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_shadow_map_apply_shader_parameters_mutations.py

Build broken copies in the cache, leaving the real source intact. Only a
behavioral FAIL counts as a caught mutation; build/spec errors never do.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("invert pass filtering", "if (slot.pass != pass)", "if (slot.pass == pass)"),
    ("omit weight scale", "slot.weight.lane[lane] * slot.weight.lane[3]",
     "slot.weight.lane[lane]"),
    ("keep weight w", "weights[selected].lane[3] = lbl_8202D108;",
     "weights[selected].lane[3] = slot.weight.lane[3];"),
    ("invert slot-5 active-player gate", "i == 5 && m_draw_448 != 0", "i == 5 && m_draw_448 == 0"),
    ("ignore enabled byte", "slot.enabled == 0 ||", "false ||"),
    ("truncate matrix copy", "sizeof(slot.matrix));", "sizeof(slot.matrix) - 16);"),
    ("wrong matrix upload count", "matrices, pass > 0 ? 2 : 1", "matrices, pass > 0 ? 1 : 2"),
    ("lose softness scratch update", "lbl_82617DF0.lane[2] = m_config->slots[pass].softness;",
     "/* omitted softness */"),
    ("lose inline write counter", "if (m_draw_41c != 0) {\n        ++g_grmShaderFx_boundContext;", "if (m_draw_41c != 0) { /* omitted counter */"),
    ("omit second texture binding", "pongShadowMap_A5C8_g(m_draw_414, second);",
     "/* omitted second binding */"),
    ("omit fallback substitution", "texture = second;", "texture = texture;"),
    ("reverse secondary mode selection", "static_cast<int32_t>(m_draw_444) < 2 ?",
     "static_cast<int32_t>(m_draw_444) >= 2 ?"),
    ("use height for x scale", "scaleX /= static_cast<float>(width);",
     "scaleX /= static_cast<float>(height);"),
    ("unfuse tap arithmetic", "__builtin_fmaf(lbl_825CA4A8[i].lane[2], scaleX, offsetX)",
     "(lbl_825CA4A8[i].lane[2] * scaleX + offsetX)"),
    ("drop tap vector four", "i < 4; ++i) {\n            taps[i]", "i < 3; ++i) {\n            taps[i]"),
    ("reject zero tap handle", "static_cast<int32_t>(m_draw_42c) >= 0",
     "static_cast<int32_t>(m_draw_42c) > 0"),
    ("clobber a blend neighbor lane", "table->values[index].lane[0] = lbl_825C4890;",
     "table->values[index].lane[0] = lbl_825C4890;\n        table->values[index].lane[1] = 0.0f;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/pong_render.cpp").read_text()
    spec = Path(__file__).with_name("shadow_map_apply_shader_parameters.py")
    for name, old, new in MUTATIONS:
        expected = 1
        assert source.count(old) == expected, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=((old, new),),
                                        workdir=root / "tools/lift-check/build/shadow-mutations")).run()
        first = output.getvalue().splitlines()[0]
        caught = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if caught else 'MISSED'} {name}: {first}", flush=True)
        if not caught:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
