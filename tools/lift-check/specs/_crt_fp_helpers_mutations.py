import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("crt_fp_classify", "infinity sign", "return 2;", "return 1;"),
    ("crt_fp_classify", "quiet NaN", "return 3;", "return 4;"),
    ("crt_fp_classify", "signaling NaN", "return 4;", "return 0;"),
    ("crt_fp_adjust_exponent", "wrong delta", "static_cast<uint32_t>(delta)", "static_cast<uint32_t>(delta + 1u)"),
    ("crt_fp_adjust_exponent", "lose mantissa", "bits & 0x0000FFFFFFFFFFFFULL", "bits & 0x00000000FFFFFFFFULL"),
    ("crt_fp_round", "wrong shift", "0x1p52", "0x1p51"),
    ("crt_fp_round", "wrong negative path", "return shifted + integralLimit;", "return shifted - integralLimit;"),
    ("crt_fp_sqrt", "wrong argument", "__builtin_sqrt(value)", "__builtin_sqrt(__builtin_fabs(value))"),
]

def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        ok = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if ok else 'MISSED'} {spec}: {label}: {first}", flush=True)
        if not ok:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
