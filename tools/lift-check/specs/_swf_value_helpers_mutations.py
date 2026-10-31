"""Only behavioral FAIL counts; patches apply to cached build copies."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "swf_value_is_integer": [
        ("reject null text", "if (!text) return 1;", "if (!text) return 0;"),
        ("reject strings without a point", "if (!point) return 1;", "if (!point) return 0;"),
        ("skip nonzero fraction", "*point == '0'", "*point != '\\0'"),
        ("accept float tag", "case 2: case 3: return 1;", "case 2: case 3: case 4: return 1;"),
        ("truncate chunk chain", "chunk = chunk->next.get();", "chunk = nullptr;"),
    ],
    "swf_values_equal": [
        ("normalize boolean", "*reinterpret_cast<const uint8_t*>(a) == static_cast<uint8_t>(swfValueToBoolean(b))",
         "(*reinterpret_cast<const uint8_t*>(a) != 0) == (swfValueToBoolean(b) != 0)"),
        ("compare dirty boolean upper bits", "static_cast<uint8_t>(swfValueToBoolean(b))", "swfValueToBoolean(b)"),
        ("compare integer to tag", "static_cast<int32_t>(a->payload)", "static_cast<int32_t>(a->tag)"),
        ("invert float equality", "return left == right;", "return left != right;"),
        ("coerce every object payload", "b->tag == 5 ? b->payload : 0", "b->payload"),
        ("compare null-tag types", "return a->payload == b->payload;", "return a->tag == b->tag;"),
        ("invert strings", "std::strcmp(left, right) == 0", "std::strcmp(left, right) != 0"),
        ("truncate chunk chain", "chunk = chunk->next.get();", "chunk = nullptr;"),
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
