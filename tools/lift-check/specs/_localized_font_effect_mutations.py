"""Only behavioral FAIL counts for recursive effect reference ownership."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "localized_font_effect_release": [
        ("increment references", "--effect->references", "++effect->references"),
        ("premature destruction", "remaining == 0", "remaining <= 1"),
        ("omit destruction", "localizedFontEffectDestroy(effect, 1);", "/* lost destroy */"),
        ("return dead count", "return 0;", "return effect->references;"),
    ],
    "localized_font_effect_destroy": [
        ("omit second child", "if (effect->second) localizedFontEffectRelease(effect->second.get());", "/* lost second */"),
        ("omit first child", "if (effect->first) localizedFontEffectRelease(effect->first.get());", "/* lost first */"),
        ("always free standalone data", "if (!effect->first && !effect->second)", "if (true)"),
        ("omit primary data", "rage_free(effect->data.get());", "/* lost data */"),
        ("omit object release", "rage_free(effect);", "/* lost object */"),
        ("wrong return", "return effect;", "return nullptr;"),
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
