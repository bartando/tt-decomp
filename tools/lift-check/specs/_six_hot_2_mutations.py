"""Mutation checks: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python tools/lift-check/specs/_six_hot_2_mutations.py"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = {
    "cr_anim_dof_quaternion_normalize": [
        ("wrong x", "quat[0] = 0.0f;\n    quat[1] = 0.0f;", "quat[0] = 1.0f;\n    quat[1] = 0.0f;"),
        ("wrong w", "quat[3] = 1.0f;", "quat[3] = 0.0f;"),
        ("omit z", "quat[2] = 0.0f;\n    quat[3] = 1.0f;", "quat[3] = 1.0f;"),
    ],
    "cr_anim_dof_vector3_set_value": [
        ("omit fourth lane", "currentVec[3] = sourceVec[3];", ""),
        ("wrong source lane", "currentVec[0] = sourceVec[0];\n    currentVec[1] = sourceVec[1];", "currentVec[0] = sourceVec[0];\n    currentVec[1] = sourceVec[0];"),
        ("wrong destination", "currentVec[2] = sourceVec[2];\n    currentVec[3] = sourceVec[3];", "currentVec[4] = sourceVec[2];\n    currentVec[3] = sourceVec[3];"),
    ],
    "grm_shader_fx_reset_constant_state": [
        ("wrong live offset", "instanceBytes + 532", "instanceBytes + 528"),
        ("wrong standby offset", "instanceBytes + 540", "instanceBytes + 536"),
        ("omit clear", "*liveCounter = 0;", ""),
    ],
    "msg_msg_sink_get_state_flags": [
        ("wrong null result", "return 32;  // Default state when no nested object", "return 0;"),
        ("wrong state mapping", "{ 1, 2, 4, 8, 16, 32 }", "{ 1, 2, 4, 8, 16, 16 }"),
        ("wrong extra bit", "if (extraFlags & 0x20) {\n            flags |= 64;", "if (extraFlags & 0x10) {\n            flags |= 64;"),
    ],
    "util_b188": [
        ("ignore sentinel", "entry == 0xFFFFFFFF ||", "false ||"),
        ("ignore table state", "g_network_array1[table * 36 + 28] == 0", "false"),
        ("wrong entry stride", "return entries + entry * 4;", "return entries + entry * 8;"),
    ],
    "grc_texture_factory_xenon_efe8": [
        ("wrong target slot", "grcDevice_SetRenderTarget(g_grcTextureDevice, slot, surface);", "grcDevice_SetRenderTarget(g_grcTextureDevice, 0, surface);"),
        ("invert format condition", "g_grcFormatId == 0x1A220197", "g_grcFormatId != 0x1A220197"),
        ("omit max depth reversal", "transformData[5] = 1.0f - transformData[5];", ""),
    ],
}


def main():
    total = 0
    for spec, mutations in CASES.items():
        spec_path = Path(__file__).with_name(spec + ".py")
        namespace = {}
        exec(spec_path.read_text(), namespace)
        source = Path(namespace["SOURCE"]).read_text()
        for label, old, new in mutations:
            assert source.count(old) == 1, f"ambiguous mutation: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(spec_path,
                             Options(seed=1, patches=((old, new),))).run()
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
