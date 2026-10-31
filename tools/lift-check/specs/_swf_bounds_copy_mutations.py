"""Require behavioral failures for bounds traversal and action assignment."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

COMMON = [
    ("ignore own minimum", "if (lower < minimum) minimum = lower;", "/* lost rectangle minimum */"),
    ("subtract rectangle span", "const float upper = lower + span;", "const float upper = lower - span;"),
    ("ignore children", "child = instance->firstChild.get()", "child = static_cast<BoundsInstance*>(nullptr)"),
    ("wrong child extent", "const float childMax = childMin + childWidth;", "const float childMax = childMin - childWidth;"),
    ("omit minimum output", "if (outMin) *outMin = minimum;", "/* lost outMin */"),
]
CASES = {
    "swf_instance_width": COMMON + [
        ("wrong own axis", "outMin, 0);", "outMin, 1);"),
    ],
    "swf_instance_height": COMMON + [
        ("wrong own axis", "outMin, 1);", "outMin, 0);"),
        ("fix retail child-axis quirk", "const float childWidth = util_EF98(child, &childMin);",
         "const float childWidth = swfINSTANCE_F0D8_w(child, &childMin);"),
    ],
    "swf_copy_action_function": [
        ("copy dispatch", "bytes(4, 0x84);", "bytes(0, 0x84);"),
        ("omit string tail", "bytes(0x88, 0x488);", "bytes(0x88, 0x487);"),
        ("copy alignment padding", "words(0x89C, 0x1CA8);", "words(0x898, 0x1CA8);"),
        ("omit final word", "words(0x89C, 0x1CA8);", "words(0x89C, 0x1CA4);"),
        ("reverse word-copy direction", "for (size_t i = begin; i < end; i += 4)",
         "for (size_t i = end - 4; i >= begin && i < end; i -= 4)"),
    ],
}


def main():
    for spec, cases in CASES.items():
        for label, old, new in cases:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(seed=1, patches=((old, new),))).run()
            first = output.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith("FAIL ")
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if not caught:
                print(output.getvalue())
                return 1
    print(f"Caught {sum(map(len, CASES.values()))} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
