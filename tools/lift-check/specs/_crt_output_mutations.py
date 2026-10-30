"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_crt_output_mutations.py

Mutate only build-cache copies of crtOutput. A caught mutation must produce a
behavioral FAIL (exit 1); BUILD, SPEC, UNSUPPORTED and PASS all fail this runner.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


MUTATIONS = (
    ("wrong result", "    return count;", "    return count + 1;"),
    ("wrong invalid-argument result", "return invalidPrintArgument();", "return 0;"),
    ("accept Unicode stream mode", "(printIoEntry(stream)->textMode & 0xFE) != 0", "false"),
    ("negative star width stays right aligned", "flags |= Left;", "flags |= Plus;"),
    ("negative precision becomes zero", "if (precision < 0) precision = -1;", "if (precision < 0) precision = 0;"),
    ("drop plus flag", "case '+': flags |= Plus; break;", "case '+': flags |= Space; break;"),
    ("uppercase hex becomes lowercase", "case 'X': hexOffset = 7;", "case 'X': hexOffset = 39;"),
    ("pointer precision is not eight", "case 'p': precision = 8;", "case 'p': precision = 1;"),
    ("lose signed short extension", "static_cast<int16_t>(word)", "static_cast<uint16_t>(word)"),
    ("truncate 64-bit integers", "if (!(flags & (Int64 | LongLong))) value &= 0xFFFFFFFFu;", "value &= 0xFFFFFFFFu;"),
    ("explicit precision keeps zero padding", "flags &= ~Zero;", "flags |= Zero;"),
    ("zero still has hex prefix", "if (value == 0) prefixLength = 0;", "if (false) prefixLength = 0;"),
    ("octal alternate prefix disappears", "if ((flags & Octal) && (length == 0 || *text != '0'))", "if (false)"),
    ("numeric zero precision still prints a digit", "if (precision < 0) precision = 1;",
     "if (precision <= 0) precision = 1;"),
    ("padding ignores sign prefix", "width - length - prefixLength", "width - length"),
    ("zero padding emits spaces", "crtWriteChar('0', stream, &count);", "crtWriteChar(' ', stream, &count);"),
    ("wide strings read bytes", "if (wide && length > 0)", "if (false)"),
    ("counted wide length is bytes", "wide ? value->length / 2 : value->length", "value->length"),
    ("percent hn writes full word", "*static_cast<int16_t*>(destination) = static_cast<int16_t>(count);",
     "*static_cast<int*>(destination) = count;"),
    ("bypass percent n gate", "if (!crtCountOutputEnabled())", "if (crtCountOutputEnabled() == -1)"),
    ("float default precision is wrong", "if (precision < 0) precision = 6;", "if (precision < 0) precision = 5;"),
    ("omit float zero cropping", "if (ch == 'g' && !(flags & Alternate))", "if (false)"),
    ("forget float allocation cleanup", "crtFree(allocated);", "(void)allocated;"),
    ("wrong debug truncation result", "result = 511;", "result = 510;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/crt/printf.cpp").read_text()
    # Keep the preamble/helpers unchanged, including their argument checks.
    marker = '// @ 0x824348D0 | size: 0xB84\n'
    preamble, target = source.split(marker)
    spec = Path(__file__).with_name("crt_output.py")
    caught = 0
    for name, old, new in MUTATIONS:
        assert old in target, f"mutation anchor changed: {name}"
        mutated = preamble + marker + target.replace(old, new)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(seed=1, patches=((source, mutated),))).run()
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
