"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
tools/lift-check/specs/_cloth_solve_distance_constraints_mutations.py

Only build-cache copies are changed. Each broken lift must report FAIL;
BUILD/SPEC/UNSUPPORTED are not caught mutations. The checked-in lift stays intact.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("discard partial batches", (
        ("batch < static_cast<uint32_t>(count); batch += 8",
         "batch + 8 <= static_cast<uint32_t>(count); batch += 8"),)),
    ("skip every other batch", (
        ("batch += 8) {", "batch += 16) {"),)),
    ("read endpoints after earlier stores", (
        ("const ClothDistanceConstraint& record = records[i];",
         "const ClothDistanceConstraint& record = records[i];\n"
         "            first[i] = points[record.firstParticle];\n"
         "            second[i] = points[record.secondParticle];"),)),
    ("drop the second endpoint store", (
        ("points[record.secondParticle] = newSecond;", "/* lost second endpoint */"),)),
    ("reverse record store order", (
        ("        for (uint32_t i = 0; i < 8; ++i) {\n            const ClothDistanceConstraint& record = records[i];",
         "        for (uint32_t reversed = 8; reversed-- > 0;) {\n"
         "            const uint32_t i = reversed;\n"
         "            const ClothDistanceConstraint& record = records[i];"),)),
    ("use the same weight for both endpoints", (
        ("flushVmx(flushVmx(1.0f - weight) * strength)", "flushVmx(weight * strength)"),)),
    ("ignore compression scaling", (
        ("restSq > distanceSq ? compression : 1.0f", "1.0f"),)),
    ("reverse the correction sign", (
        ("const float error = flushVmx(1.0f - ratio);",
         "const float error = flushVmx(ratio - 1.0f);"),)),
    ("include padding w in squared distance", (
        ("            const float distanceSq = flushVmx(dot(delta, delta, 3));\n"
         "            const float restSq = flushVmx(record.restLengthSq);",
         "            delta.lane[3] = first[i].lane[3] - second[i].lane[3];\n"
         "            const float distanceSq = flushVmx(dot(delta, delta, 4));\n"
         "            const float restSq = flushVmx(record.restLengthSq);"),)),
    ("lose uint16 index bit 15", (
        ("first[i] = points[records[i].firstParticle];",
         "first[i] = points[records[i].firstParticle & 0x7FFFu];"),)),
    ("forget position-base rounding", (
        ("auto* points = reinterpret_cast<LvlTableVector*>(reinterpret_cast<uintptr_t>(positions) & ~uintptr_t(15));",
         "auto* points = positions;"),)),
    ("keep VMX subnormals", (
        ("        bits &= 0x80000000u;", "        /* lost VMX flush */"),)),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/match/lvl_table.cpp").read_text()
    spec = Path(__file__).with_name("cloth_solve_distance_constraints.py")
    caught = 0
    for name, patches in MUTATIONS:
        for old, _ in patches:
            assert source.count(old) == 1, f"mutation anchor changed: {name}"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=200, seed=1, patches=patches)).run()
        first = output.getvalue().splitlines()[0]
        detected = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if detected else 'MISSED'} {name}: {first}", flush=True)
        if not detected:
            print(output.getvalue())
            return 1
        caught += 1
    print(f"Caught {caught}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
