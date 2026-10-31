"""Mutation proof for body-state clearing and saved-pose chain reset."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/physics/ph_physics.cpp"
CASES = {
    "ph_articulated_body_clear_state": ("void phArticulatedBody_ClearState(void* object) {", [
        ("skip velocity W/cache", "memset(body + 0x110, 0, 64);", "memset(body + 0x110, 0, 48);"),
        ("clear wrong force range", "memset(body + 0x3D0, 0, 32);", "memset(body + 0x3F0, 0, 32);"),
        ("leave saved force state", "memset(body + 0x410, 0, 64);", "memset(body + 0x410, 0, 32);"),
    ]),
    "ph_articulated_reset_joint_chain": ("void phArticulatedCollider_ResetJointChain(void* jointData) {", [
        ("skip body reset", "phArticulatedBody_ClearState(reinterpret_cast<void*>(uintptr_t(data[10 + i])));",
         "(void)data;"),
        ("wrong saved position", "memcpy(body + 0xC0 / 4, body + 0x100 / 4, 16);",
         "memcpy(body + 0xC0 / 4, body + 0xD0 / 4, 16);"),
        ("omit final saved basis row", "memcpy(body + 0x90 / 4, body + 0xD0 / 4, 48);",
         "memcpy(body + 0x90 / 4, body + 0xD0 / 4, 32);"),
        ("wrong per-body flag offset", "data[105 + i] = 0;", "data[104 + i] = 0;"),
        ("clear extra child flag", "static_cast<unsigned>(count - 1)", "static_cast<unsigned>(count)"),
    ]),
}


def main():
    source = (ROOT / SOURCE).read_text()
    total = 0
    for spec, (signature, mutations) in CASES.items():
        start = source.index(signature)
        body = source[start:source.index('\n}\n', start) + 2]
        for name, old, new in mutations:
            assert body.count(old) == 1, (spec, name, body.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=600, seed=1, patches=((body, body.replace(old, new)),))).run()
            report = output.getvalue()
            caught = rc == 1 and "the lift faulted" not in report
            print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
