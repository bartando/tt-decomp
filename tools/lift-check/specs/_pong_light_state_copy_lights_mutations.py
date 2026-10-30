"""From repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_pong_light_state_copy_lights_mutations.py

Mutates build-cache copies only. Each must yield behavioral FAIL (exit 1);
BUILD, SPEC and UNSUPPORTED do not count as caught mutations.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("skip eighth light", "i < 8;", "i < 7;"),
    ("copy only active lights", "i < 8;", "i < src->count;"),
    ("omit third vector", "v < 3;", "v < 2;"),
    ("swap vector sources", "= src->lights[i].vectors[v];",
     "= src->lights[i].vectors[2 - v];"),
    ("omit second scalar", "dst->lights[i].scalars[1] = src->lights[i].scalars[1];", ""),
    ("duplicate first scalar", "scalars[1] = src->lights[i].scalars[1];",
     "scalars[1] = src->lights[i].scalars[0];"),
    ("omit fourth flag", "f < 4;", "f < 3;"),
    ("normalize flag bytes", "= src->lights[i].flags[f];",
     "= !!src->lights[i].flags[f];"),
    ("copy record padding", "        for (int v = 0; v < 3; ++v) {",
     "        dst->lights[i] = src->lights[i];\n        for (int v = 0; v < 3; ++v) {"),
    ("overwrite ambient and count", "    return dst;",
     "    dst->ambient = src->ambient;\n    dst->count = src->count;\n    return dst;"),
    ("return source", "    return dst;", "    return const_cast<pongLightState*>(src);"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/pong_render.cpp").read_text()
    spec = Path(__file__).with_name("pong_light_state_copy_lights.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
