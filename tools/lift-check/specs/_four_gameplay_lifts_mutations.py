"""Mutation proof for the four gameplay lifts; patches only build-cache copies.

Run from the repository root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_four_gameplay_lifts_mutations.py
Only behavioral FAIL (exit 1) counts; BUILD/SPEC/UNSUPPORTED are not catches.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

CASES = [
    ("interpolate_court_grid_position", "src/game/player/pong_player.cpp",
     "void pongPlayer_InterpolateCourtGridPosition(float* lerpFactors, uint32_t flip, float* outPos,", [
         ("empty lift", "    // Load court height", "    return;\n    // Load court height"),
         ("invert flip", "if (static_cast<uint8_t>(flip))", "if (!static_cast<uint8_t>(flip))"),
         ("test all flip bits", "if (static_cast<uint8_t>(flip))", "if (flip)"),
         ("omit output w", "lane < 4", "lane < 3"),
         ("scalar add without VMX flushing", "flushVmx(flushVmx(outPos[lane]) + flushVmx(offset[lane]))",
          "outPos[lane] + offset[lane]"),
         ("wrong Z factor", "lerpFactors[1] * rangeZ", "lerpFactors[0] * rangeZ"),
         ("omit height bias", "courtHeight + g_kCourtHeightOffset", "courtHeight"),
     ]),
    ("viewport_get_aspect_ratio", "src/game/camera/pong_camera.cpp",
     "float grcViewport::GetAspectRatio() const {", [
         ("constant return", "    extern const float lbl_8202D108;", "    return 1.0f;\n    extern const float lbl_8202D108;"),
         ("drop explicit aspect", "return m_aspect;", "return lbl_8202D108;"),
         ("wrong default", "return lbl_8202D108;", "return lbl_8202D110;"),
         ("swap window dimensions", "static_cast<float>(m_windowWidth) * m_viewportScaleX",
          "static_cast<float>(m_windowHeight) * m_viewportScaleX"),
         ("unsigned dimensions", "static_cast<float>(m_windowHeight) * m_viewportScaleY",
          "static_cast<float>(static_cast<uint32_t>(m_windowHeight)) * m_viewportScaleY"),
     ]),
    ("viewport_update_screen_matrix", "src/game/camera/pong_camera.cpp",
     "void grcViewport::UpdateScreenMatrix() {", [
         ("empty lift", "    extern uint32_t g_nScreenWidth;", "    return;\n    extern uint32_t g_nScreenWidth;"),
         ("ignore height changes", "m_windowWidth == width && m_windowHeight == height", "m_windowWidth == width"),
         ("divide instead of arithmetic shift", "static_cast<float>(-h >> 1)", "static_cast<float>(-h / 2)"),
         ("halve before pixel quantization", "static_cast<float>(w >> 1)", "static_cast<float>(w) * 0.5f"),
         ("overwrite untouched third row", "    m_screenMtx.d =", "    m_screenMtx.c = {};\n    m_screenMtx.d ="),
         ("omit dimension cache", "m_windowHeight = height;", "(void)height;"),
     ]),
    ("ph_update_object_update_drawable", "src/physics/ph_update_object.cpp",
     "void phUpdateObject::UpdateDrawable(void* frameData, uint32_t flags) {", [
         ("empty lift", "    if (!m_bActive", "    return;\n    if (!m_bActive"),
         ("ignore activity gate", "if (!m_bActive || !m_pDrawable)", "if (!m_pDrawable)"),
         ("wrong pose array owner", "reinterpret_cast<uint8_t**>(collider + 24)", "reinterpret_cast<uint8_t**>(state + 24)"),
         ("always use first pose", "static_cast<uint32_t>(index) * 8", "0"),
         ("truncate large pose", "void* buffer = __builtin_alloca(size);", "if (size > 4096) size = 4096;\n        void* buffer = __builtin_alloca(size);"),
         ("skip animation", "if (animation[24])", "if (false)"),
         ("wrong dispatch slot", "m_pDrawable))[5]", "m_pDrawable))[4]"),
         ("drop visibility flags", "buffer, flags, m_visFlags, 0", "buffer, flags, 0, 0"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        # Skip the forward declaration, if present.
        start = source.index(signature)
        if source.find(";", start) < source.find("{", start):
            start = source.index(signature, start + len(signature))
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"mutation anchor changed: {spec}: {label}"
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + ".py"),
                             Options(trials=128, seed=1,
                                     patches=((body, body.replace(old, new)),))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{spec}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
