"""Only behavioral FAIL counts for gradient sampling and stroke state."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    "swf_sample_gradient": [
        ("radial low bit only", "fill->radial != 0", "(fill->radial & 1) != 0"),
        ("wrong transform axis", "std::fma(fill->matrix[2], y, ax)", "std::fma(fill->matrix[3], y, ax)"),
        ("wrong upper clamp", "position > 255.0f) position = 255.0f", "position > 254.0f) position = 254.0f"),
        ("signed interpolation", "((end - start) * offset) / span",
         "static_cast<int32_t>((end - start) * offset) / static_cast<int32_t>(span)"),
        ("mask overflowing channels", "(start + ((end - start) * offset) / span) << shift",
         "((start + ((end - start) * offset) / span) & 255) << shift"),
        ("exclude interval endpoints", "index > ratios[i + 1]", "index >= ratios[i + 1]"),
        ("wrong fallback color", "return colors[0];", "return colors[fill->count ? fill->count - 1 : 0];"),
    ],
    "swf_apply_stroke_style": [
        ("omit texture unbind", "g_swfBindFontTexture(nullptr);", "/* lost unbind */"),
        ("wrong texture binding", "g_swfBindFontTexture(nullptr);", "g_swfBindFontTexture(const_cast<void*>(stroke));"),
        ("unsigned color factors", "reinterpret_cast<const int8_t*>(state + 0x38)", "reinterpret_cast<const uint8_t*>(state + 0x38)"),
        ("unsigned color additions", "reinterpret_cast<const int8_t*>(state + 0x3C)", "reinterpret_cast<const uint8_t*>(state + 0x3C)"),
        ("omit alpha tint", "if (channel == 3) value = value * state[0x47] / 255;", "/* lost tint */"),
        ("wrong packed channel", "16 - channel * 8", "channel * 8"),
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
