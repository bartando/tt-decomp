"""From repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_cr_anim_dof_copy_mutations.py

Mutate build-cache copies only. Only behavioral FAIL counts as caught;
BUILD/SPEC/UNSUPPORTED or a passing mutant make this runner fail.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


VECTOR_COPY = """    uint32_t words[4];
    __builtin_memcpy(words, sourceVec, sizeof(words));
    __builtin_memcpy(destVec, words, sizeof(words));"""
QUAT_COPY = """    dst[0] = src[0];
    dst[1] = src[1];"""


def arithmetic_copy(source, dest, expression):
    return f"""    for (int i = 0; i < 4; ++i) {{
        float value = reinterpret_cast<float*>({source})[i];
        reinterpret_cast<float*>({dest})[i] = {expression};
    }}"""


def mutations(kind):
    vector = kind == "vector3"
    old = VECTOR_COPY if vector else QUAT_COPY
    src, dst = ("sourceVec", "destVec") if vector else ("src", "dst")
    yield "omit fourth lane" if vector else "omit second pair", old, (
        VECTOR_COPY.replace("memcpy(destVec, words, sizeof(words))", "memcpy(destVec, words, 12)")
        if vector else "    dst[0] = src[0];")
    yield "skip copy", old, "    (void)0;"
    yield "swap lane pairs", old, (
        "    __builtin_memcpy(destVec, sourceVec + 2, 8);\n"
        "    __builtin_memcpy(destVec + 2, sourceVec, 8);"
        if vector else "    dst[0] = src[1];\n    dst[1] = src[0];")
    # Volatile operands prevent LLVM simplifying the FMA to an addition.
    yield "FP identity FMA (NaN/zero bits)", old, (
        "    volatile float one = 1.0f, zero = 0.0f;\n" + arithmetic_copy(
            src, dst, "__builtin_fmaf(value, one, zero)"))
    yield "canonicalize NaNs", old, arithmetic_copy(
        src, dst, "value != value ? __builtin_nanf(\"\") : value")
    yield "clear zero signs", old, arithmetic_copy(
        src, dst, "value == 0.0f ? 0.0f : value")
    yield "flush subnormals", old, f"""    for (int i = 0; i < 4; ++i) {{
        uint32_t word;
        __builtin_memcpy(&word, reinterpret_cast<char*>({src}) + 4 * i, 4);
        if ((word & 0x7f800000u) == 0) word &= 0x80000000u;
        __builtin_memcpy(reinterpret_cast<char*>({dst}) + 4 * i, &word, 4);
    }}"""
    # Catch accidental use of the neighboring arithmetic blend/normalize path.
    yield "normalize copied value", old, old + f"""
    float* value = reinterpret_cast<float*>({dst});
    float length = sqrtf(value[0] * value[0] + value[1] * value[1]
                        + value[2] * value[2] + value[3] * value[3]);
    for (int i = 0; i < 4; ++i) value[i] /= length;"""
    if not vector:
        yield "snapshot both pairs before storing", old, "    __builtin_memmove(dst, src, 16);"


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/animation/rage_anim.cpp").read_text()
    total = 0
    for kind in ("vector3", "quaternion"):
        spec = Path(__file__).with_name(f"cr_anim_dof_{kind}_copy_from.py")
        # Scope shared snippets to this function; other methods also copy pairs.
        start = source.index(f"void crAnimDof{'Vector3' if kind == 'vector3' else 'Quaternion'}::CopyFrom(")
        end = source.index("\n}\n", start) + 2
        function = source[start:end]
        caught = 0
        cases = list(mutations(kind))
        for name, old, new in cases:
            assert function.count(old) == 1, f"mutation anchor changed: {kind}: {name}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(spec, Options(trials=2000, seed=1,
                    patches=((function, function.replace(old, new, 1)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{kind}: {'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            caught += 1
        total += caught
        print(f"{kind}: caught {caught}/{len(cases)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
