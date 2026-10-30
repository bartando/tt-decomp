"""Mutation checks; patches apply only to build-cache copies."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    "rage_apply_device_render_state": (
        "src/rage/rage_system.cpp", [
            ("inverted cache gate", "stateId != g_lastRenderStateId", "stateId == g_lastRenderStateId"),
            ("missing cache write", "g_lastRenderStateId = stateId;", "(void)stateId;"),
            ("override gate", "if (hasIccOverride != 0)", "if (hasIccOverride == 0)"),
            ("force offset", "stateObj + 39)", "stateObj + 38)"),
        ]),
    "cm_node_get_float": (
        "src/rage/misc/rage_cm.cpp", [
            ("direct port", "return *reinterpret_cast<const float*>(port->m_pData);", "return g_cm_zeroFloat;"),
            ("virtual slot", "reinterpret_cast<GetFltFn>(node->vtable[4])(node, &tmp);", "reinterpret_cast<GetFltFn>(node->vtable[3])(node, &tmp);"),
            ("default value", "return g_cm_zeroFloat;  // 0.0f", "return 1.0f;  // 0.0f"),
        ]),
    "normalize_quaternion": (
        "src/rage/animation/rage_anim.cpp", [
            ("wrong fused lane", "__builtin_fmaf(quat[2], quat[2], magSquared)", "__builtin_fmaf(quat[1], quat[1], magSquared)"),
            ("missing lane write", "quat[3] *= invMag;", "(void)invMag;"),
            ("zero magnitude skips writes", "quat[0] *= invMag;", "if (magSquared != 0.0f) quat[0] *= invMag;"),
            ("wrong scale", "1.0f / std::sqrt(magSquared) : 0.0f", "2.0f / std::sqrt(magSquared) : 0.0f"),
        ]),
}


def main():
    for spec, (path, mutations) in CASES.items():
        source = (ROOT / path).read_text()
        for name, old, new in mutations:
            assert source.count(old) == 1, name
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=128, seed=1, patches=((old, new),))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {name}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
