"""Mutation proof for the channel lookup/evaluator and cmLerp scalar getter.

Run from the repository root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_channel_lerp_mutations.py

Only temporary build copies change. Every mutation must produce behavioral
FAIL (exit 1); BUILD, SPEC and UNSUPPORTED never count as caught. Use the full
1000-trial spec defaults, with anchors scoped to each target function.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("locomotion_find_channel", "src/game/creature/pong_creature.cpp",
     "void* LocomotionStateAnim_FindChannelByKey(", [
         ("empty lift", "    LocomotionStateAnim* lsa", "    return nullptr;\n    LocomotionStateAnim* lsa"),
         ("signed count", "int high = (int)count - 1;", "int high = (int)(int16_t)count - 1;"),
         ("wrong high-key shift", "((uint32_t)animID_high << 16)", "((uint32_t)animID_high << 8)"),
         ("padding byte in entry key", "((char*)entry + 0)", "((char*)entry + 1)"),
         ("upper midpoint", "(low + high) / 2", "(low + high + 1) / 2"),
         ("wrong insertion index", "    *outIndex = low;\n    return nullptr;",
          "    *outIndex = high;\n    return nullptr;"),
         ("omit hit index", "        *outIndex = mid;", "        (void)outIndex;"),
     ]),
    ("locomotion_evaluate_channel", "src/game/creature/pong_creature.cpp",
     "bool LocomotionStateAnim_EvaluateChannel(", [
         ("empty lift", "    LocomotionStateAnim* lsa", "    return false;\n    LocomotionStateAnim* lsa"),
         ("key from animation header", "static_cast<const uint8_t*>(destination)", "static_cast<const uint8_t*>(self)"),
         ("omit sample count decrement", "lsa->field_0x000a) - 1", "lsa->field_0x000a)"),
         ("omit time scale", "sampleRate * time", "time"),
         ("wrong evaluate receiver", "(destination, nullptr, channels[index], sampleTime)",
          "(found, nullptr, channels[index], sampleTime)"),
         ("wrong source channel", "channels[index], sampleTime", "channels[0], sampleTime"),
         ("wrong evaluate slot", "VCALL(destination, 4, Evaluate)", "VCALL(destination, 5, Evaluate)"),
         ("omit miss reset", "VCALL(destination, 13, Reset)(destination);", "(void)destination;"),
         ("invert success return", "        return true;", "        return false;"),
     ]),
    ("cm_lerp_get_float", "src/rage/misc/rage_cm.cpp",
     "void cmLerp::GetFloat(", [
         ("empty lift", "    const float t", "    return;\n    const float t"),
         ("factor from wrong port", "cmNode_GetFloat(&factor)", "cmNode_GetFloat(&portB)"),
         ("inclusive zero window", "t < 0.0001f && t > -0.0001f", "t <= 0.0001f && t >= -0.0001f"),
         ("inclusive one window", "t > 0.9999f && t < 1.0001f", "t >= 0.9999f && t <= 1.0001f"),
         ("evaluate both endpoints near zero", "if (t < 0.0001f && t > -0.0001f)", "if (false)"),
         ("forward endpoint evaluation order",
          "        const float b = cmNode_GetFloat(&portB);\n        const float a = cmNode_GetFloat(&portA);",
          "        const float a = cmNode_GetFloat(&portA);\n        const float b = cmNode_GetFloat(&portB);"),
         ("reversed difference", "const float difference = b - a;", "const float difference = a - b;"),
         ("nonfused lerp", "        *out = difference * t + a;",
          "        const float product = difference * t;\n        *out = product + a;"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec_name, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
