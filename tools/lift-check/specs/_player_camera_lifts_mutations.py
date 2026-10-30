"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_player_camera_lifts_mutations.py

Patch build-cache copies only. Every mutation must produce behavioral FAIL (1);
BUILD, SPEC and UNSUPPORTED do not count. Anchors are scoped to each lift.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


CASES = [
    ("player_is_swing_apex_reached", "src/game/player/pong_player.cpp",
     "bool pongPlayerState::IsSwingApexReached() const {", [
         ("empty lift", "    if (m_bActive", "    return false;\n    if (m_bActive"),
         ("skip primary readiness gate", "if (m_bActive &&", "if (false &&"),
         ("invert secondary gate", "if (IsCreatureState2Active())", "if (!IsCreatureState2Active())"),
         ("reject nonpositive swing progress", "if (!(m_pSwingSubState->m_swingProgress > g_kZero))\n            return true;",
          "if (!(m_pSwingSubState->m_swingProgress > g_kZero))\n            return false;"),
         ("unsigned swing frame count", "float(m_pSwingSubState->m_swingSubFrame)",
          "float(static_cast<uint16_t>(m_pSwingSubState->m_swingSubFrame))"),
         ("wrong frame scale", "float(m_pSwingSubState->m_swingSubFrame) * g_kFrameScale",
          "float(m_pSwingSubState->m_swingSubFrame) * 1.0f"),
         ("inclusive swing timer", "m_pTimingState->m_currentTime > fraction", "m_pTimingState->m_currentTime >= fraction"),
         ("invert anim phase gate", "m_pAnimState->m_swingPhase <= g_kZero", "m_pAnimState->m_swingPhase > g_kZero"),
         ("strict anim boundary", "m_pAnimState->m_animProgress >= fraction", "m_pAnimState->m_animProgress > fraction"),
         ("accept unordered anim comparison", "m_pAnimState->m_animProgress >= fraction", "!(m_pAnimState->m_animProgress < fraction)"),
         ("wrong frame array index", "frames[m_pAnimState->m_frameIndex]", "frames[0]"),
         ("omit recovery time helper", "pongPlayer_D238_g(m_pRecoveryState)", "g_kZero"),
         ("strict recovery boundary", "m_pRecoveryState->m_recoveryTimer >= fraction", "m_pRecoveryState->m_recoveryTimer > fraction"),
         ("reject idle fallback", "    return true;\n}", "    return false;\n}"),
     ]),
    ("player_compute_box_correction", "src/game/player/pong_player.cpp",
     'extern "C" bool pongPlayer_ComputeBoxCorrection(', [
         ("empty lift", "    const float zero", "    return false;\n    const float zero"),
         ("any axis instead of all", "< 0x1p-126f &&", "< 0x1p-126f ||"),
         ("reverse correction sign", "boundMin->x - pos->x", "pos->x - boundMin->x"),
         ("wrong upper bound", "boundMax->y - pos->y", "boundMin->y - pos->y"),
         ("skip z output", "    outDelta->z = pos->z < boundMin->z ? boundMin->z - pos->z\n"
          "        : pos->z > boundMax->z ? boundMax->z - pos->z : zero;", "    (void)outDelta;"),
         ("overwrite w lane", "    // VMX compares", "    outDelta->_pad = zero;\n    // VMX compares"),
         ("scalar zero test loses VMX flush", "__builtin_fabsf(outDelta->z) < 0x1p-126f", "outDelta->z == zero"),
     ]),
    ("transform_point_3x4", "src/game/camera/cm_cam_actions.cpp",
     'extern "C" void TransformPoint3x4(', [
         ("empty lift", "    // Preserve", "    return;\n    // Preserve"),
         ("wrong basis element", "mat[8], pt[2]", "mat[9], pt[2]"),
         ("omit translation", "+ mat[12]", "+ 0.0f"),
         ("wrong destination lane", "out[2] =", "out[1] ="),
         ("overwrite w lane", "    out[2] =", "    out[3] = 0.0f;\n    out[2] ="),
         ("unfuse first multiply-add", "__builtin_fmaf(mat[8], pt[2], mat[4] * pt[1])", "(mat[8] * pt[2] + mat[4] * pt[1])"),
         ("reorder first accumulation", "__builtin_fmaf(pt[0], mat[0],\n                 __builtin_fmaf(mat[8], pt[2], mat[4] * pt[1]))",
          "__builtin_fmaf(mat[8], pt[2],\n                 __builtin_fmaf(pt[0], mat[0], mat[4] * pt[1]))"),
         ("snapshot point breaks overlap", "const float* pt, const float* mat) {",
          "const float* input, const float* mat) {\n    float pt[3] = {input[0], input[1], input[2]};"),
         ("snapshot matrix breaks overlap", "const float* pt, const float* mat) {",
          "const float* pt, const float* input) {\n    float mat[16];\n    std::memcpy(mat, input, sizeof(mat));"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    caught = 0
    for spec_name, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            # "any axis" deliberately changes both conjunctions.
            expected = 2 if label == "any axis instead of all" else 1
            assert body.count(old) == expected, f"mutation anchor changed: {label}"
            changed = body.replace(old, new)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=((body, changed),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            caught += 1
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {caught}/{sum(len(c[3]) for c in CASES)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
