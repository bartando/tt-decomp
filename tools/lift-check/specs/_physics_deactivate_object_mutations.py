"""Mutation checks for the 0x822C4B60 lift; only behavioral FAIL counts.

PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_physics_deactivate_object_mutations.py
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = [
    ("empty lift", "    using namespace physicsDeactivate;",
     "    return;\n    using namespace physicsDeactivate;"),
    ("wrong pool stride", "sizeof(ColliderSlot));", "sizeof(ColliderSlot) - 4);"),
    ("unsigned pool offset", "intptr_t index = offset /",
     "intptr_t index = static_cast<uintptr_t>(offset) /"),
    ("accept capacity boundary", "index < sim->capacity", "index <= sim->capacity"),
    ("increment pool count", "--sim->used;", "++sim->used;"),
    ("store wrong index", "static_cast<uint16_t>(index);", "static_cast<uint16_t>(index + 1);"),
    ("reload replaced body", "body->Deactivate();", "collider->body->Deactivate();"),
    ("lose object handle", "sim->level->DeactivateObject(handle);",
     "sim->level->DeactivateObject(0);"),
    ("omit level removal", "sim->level->DeactivateObject(handle);", "(void)handle;"),
]


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/physics/ph_update_object.cpp").read_text()
    start = source.index("void game_4B60(void* scene, uint16_t handle) {")
    end = source.index("\n}\n", start) + 2
    body = source[start:end]
    stale_level = body.replace("    ColliderSlot* collider =",
                              "    Level* level = sim->level;\n    ColliderSlot* collider =")
    stale_level = stale_level.replace("sim->level->DeactivateObject(handle);",
                                      "level->DeactivateObject(handle);")
    mutations = MUTATIONS + [("retain replaced level", body, stale_level)]
    for label, old, new in mutations:
        assert body.count(old) == 1, f"mutation anchor changed: {label}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("physics_deactivate_object.py"),
                         Options(trials=256, seed=1,
                                 patches=((body, body.replace(old, new)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: "
              f"{output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
