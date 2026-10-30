"""Behavioral mutation proof for the four renamed hot lifts.

Run from the repo root with PYTHONPATH=tools/lift-check and the lift-check
venv's python. Patch only build-cache copies, scoped to the named function;
use the default 1200 trials and seed 1. Only behavioral FAIL counts: BUILD,
SPEC, UNSUPPORTED, original/lift faults and surviving mutants fail the proof.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options


CASES = [
    ("ph_build_rotation_matrix_y", "src/physics/ph_physics.cpp",
     "void ph_BuildRotationMatrixY(", [
         ("empty lift", "    const float cosine", "    return;\n    const float cosine"),
         ("truncate angle", "crt_cos(angle)", "crt_cos(static_cast<float>(angle))"),
         ("wrong sine sign", "matrix[2] = -sine;", "matrix[2] = sine;"),
         ("wrong identity axis", "matrix[5] = 1.0f;", "matrix[5] = 0.0f;"),
         ("clobber padding", "matrix[10] = cosine;", "matrix[10] = cosine; matrix[11] = 0.0f;"),
     ]),
    ("ph_matrix_rotate_z", "src/physics/ph_physics.cpp",
     "void phMatrix_RotateZ(", [
         ("empty lift", "    float cosine, sine;", "    return;\n    float cosine, sine;"),
         ("truncate angle", "&sine, angle)", "&sine, static_cast<float>(angle))"),
         ("wrong rotation sign", "phFlushVmx(-(xs - yc))", "phFlushVmx(xs + yc)"),
         ("lose w lane", "lane < 4", "lane < 3"),
         ("use already rotated Y", "matrix[lane] = phFlushVmx(xc + ys);",
          "matrix[lane] = phFlushVmx(xc + matrix[4 + lane] * sine);"),
         ("fuse VMX multiply/add", "matrix[lane] = phFlushVmx(xc + ys);",
          "matrix[lane] = phFlushVmx(__builtin_fmaf(x[lane], cosine, ys));"),
     ]),
    ("ph_bound_tapered_capsule_transform_endpoints", "src/physics/ph_physics.cpp",
     "void phBoundTaperedCapsule::TransformEndpoints(", [
         ("empty lift", "    if (reinterpret_cast", "    return;\n    if (reinterpret_cast"),
         ("only accept flag one", "this)[7] == 0", "this)[7] != 1"),
         ("omit base transform", "phBound_TransformWorldCentroid(this, matrix);", "(void)matrix;"),
         ("wrong cap length", "bound[49] = bound[36] * -0.5f;", "bound[49] = bound[36] * -1.3333333f;"),
         ("drop centre", "phFlushVmx(bound[48 + lane]) + phFlushVmx(bound[12 + lane])",
          "phFlushVmx(bound[48 + lane]) + 0.0f"),
         ("drop translation", "point[3] = 1.0f;", "point[3] = 0.0f;"),
         ("transpose basis", "matrix[axis], matrix[4 + axis],\n                                     matrix[8 + axis]",
          "matrix[axis * 4], matrix[axis * 4 + 1],\n                                     matrix[axis * 4 + 2]"),
         ("clobber shuffle w", "memcpy(result + 3, point, sizeof(float));", "result[3] = 0.0f;"),
         ("reverse direction", "phFlushVmx(bound[52 + lane]) - phFlushVmx(bound[48 + lane])",
          "phFlushVmx(bound[48 + lane]) - phFlushVmx(bound[52 + lane])"),
         ("omit normalization", "* inverseLength);", "* 1.0f);"),
     ]),
    ("pong_mover_update_velocity", "src/game/creature/pong_creature.cpp",
     "void pongMover::UpdateVelocity(", [
         ("empty lift", "    const auto* creature", "    return;\n    const auto* creature"),
         ("wrong cached transform", "instance + 0x40", "instance + 0x30"),
         ("keep expired timer flag", "m_posZ <= 0.0f", "m_posZ < 0.0f"),
         ("reverse input blend", "1.0f - pongMover_GetBlendWeight(this)", "pongMover_GetBlendWeight(this)"),
         ("omit clamp", "const float clamped = static_cast<float>(lower - limit >= 0.0 ? limit : lower);",
          "const float clamped = static_cast<float>(speed);"),
         ("reverse remote selection", "(m_flags & 0x10) != 0", "(m_flags & 0x10) == 0"),
         ("ignore returned vector", "x = blend(velocity[0]", "x = blend(scratch[0]"),
         ("skip velocity adjustment", "pongMover_AdjustVelocity(this, &m_unk30, &m_unk34);", "(void)this;"),
         ("exclude threshold equality", "length2 <= threshold", "length2 < threshold"),
         ("reverse court mirror", "forward ? m_unk30 : -m_unk30", "forward ? -m_unk30 : m_unk30"),
         ("expire at equality", "if (timer > threshold)", "if (timer >= threshold)"),
         ("expire unordered timer", "if (timer > threshold)", "if (!(timer <= threshold))"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec}: {label}: BUILD {exc}", flush=True)
                return 1
            report = output.getvalue()
            caught = rc == 1 and "faulted" not in report
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
        total += len(mutations)
        print(f"{spec}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} behavioral mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
