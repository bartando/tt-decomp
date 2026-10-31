"""Behavioral mutation proof for the candidate-flight simulation and helpers.
Run with PYTHONPATH=tools/lift-check and the real lift-check virtual environment.
Only exit1 (behavioral FAIL) counts; BUILD/SPEC failures do not.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("ball_shot_is_local_play", "bool BallShot_IsLocalPlay()", [
        ("constant false", "    return static_cast", "    return false;\n    return static_cast"),
        ("test all poll bits", "static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr))", "io_Input_poll_9D68(g_input_obj_ptr)"),
        ("ignore play mode", "&& lbl_825C9A2C == 0", "&& true"),
        ("cache mode before poll", "    return static_cast", "    const int mode = lbl_825C9A2C;\n    return static_cast"),
    ]),
    ("ball_shot_record_net_crossing", "void BallShot_RecordNetCrossing(", [
        ("empty crossing report", "    if (contacts == nullptr", "    return;\n    if (contacts == nullptr"),
        ("lose signed-zero crossings", "SimSign(current->z) == SimSign(previous->z)", "(current->z < 0) == (previous->z < 0)"),
        ("require both heights low", "current->y < netHeight || previous->y < netHeight", "current->y < netHeight && previous->y < netHeight"),
        ("wrong report flag", "contacts->flags[2] = 1;", "contacts->flags[1] = 1;"),
        ("wrong crossing height", "contacts->secondMeasure = current->y;", "contacts->secondMeasure = previous->y;"),
        ("overwrite unused report field", "contacts->flags[2] = 1;", "contacts->flags[2] = 1;\n        contacts->firstPosition.x = current->x;"),
    ]),
    ("ball_shot_simulate_trajectory", "void BallShot_SimulateTrajectory(", [
        ("empty simulation", "    using namespace shotSimulation;", "    return;\n    using namespace shotSimulation;"),
        ("omit frame-rate rounding", "->frameRate + 0.5f", "->frameRate"),
        ("wrong time limit", "elapsed < 24.0f", "elapsed < 12.0f"),
        ("test all target-flag bits", "static_cast<uint8_t>(stackFlag) != 0", "stackFlag != 0"),
        ("test all bounce-flag bits", "static_cast<uint8_t>(firstFlag) == 0", "firstFlag == 0"),
        ("wrong scaled net height", "netOffset = table->net->scaledHeight;", "netOffset = table->net->height;"),
        ("omit net surface offset", "(table->height + netOffset) + g_ballTableSurfaceOffset", "table->height + netOffset"),
        ("omit radius in bounce", "const float radius = initialBall ? initialBall->archetype->bound->radius : 0.0f;", "const float radius = 0.0f;"),
        ("omit radius in plane height", "const float tableHeight = heightRadius + table->height;", "const float tableHeight = table->height;"),
        ("skip outside-entry tracking", "bool trackEntry = contacts != nullptr", "bool trackEntry = false && contacts != nullptr"),
        ("report new edge position", "contacts->secondPosition = previous;", "contacts->secondPosition = position;"),
        ("invert net sign crossing", "SimSign(previous.z) != SimSign(position.z)", "SimSign(previous.z) == SimSign(position.z)"),
        ("omit height maximum", "SimMaxHeight(contacts, position.y);", "(void)contacts;"),
        ("omit plane rewind", "position = SimNmsub(velocity, correction, position);", "position = position;"),
        ("wrong material index", "GetMaterial(0)", "GetMaterial(1)"),
        ("omit table friction", "material->friction * currentTable->friction", "material->friction"),
        ("cache old table friction", "material->friction * currentTable->friction", "material->friction * table->friction"),
        ("wrong elasticity", "radius, friction, elasticity);", "radius, friction, 0.0f);"),
        ("mutate caller spin", "&spin, radius, friction, elasticity);", "const_cast<Vec4*>(inputSpin), radius, friction, elasticity);"),
        ("wrong post-bounce remainder", "SimStep(position, velocity, acceleration, correction);", "SimStep(position, velocity, acceleration, step);"),
        ("omit immediate net report", "BallShot_RecordNetCrossing(contacts, &position, &previous, netHeight);", "(void)netHeight;"),
        ("omit second flight", "while ((position.y > tableHeight || velocity.y > 0.0f) && elapsed < 24.0f) {", "while (false) {"),
        ("omit final plane rewind", "*result = SimNmsub(velocity, finalCorrection, position);", "*result = position;"),
        ("lose output w", "*result = SimNmsub(velocity, finalCorrection, position);", "*result = SimNmsub(velocity, finalCorrection, position);\n    result->w = 0;"),
    ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/ball/ball_shot_simulation.cpp").read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"missing mutation anchor: {spec}: {label}"
            replacement = body.replace(old, new)
            if label == "cache mode before poll": replacement = replacement.replace("&& lbl_825C9A2C == 0", "&& mode == 0")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"), Options(
                    trials=128, seed=1, patches=((body, replacement),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
