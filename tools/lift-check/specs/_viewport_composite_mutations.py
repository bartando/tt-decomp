"""Patch cache copies only; every mutation must produce behavioral FAIL (1).

Run: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_viewport_composite_mutations.py
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = (
    ("omit all products", "    m_modelViewMtx =", "    return;\n    m_modelViewMtx ="),
    ("reverse model/view", "m_transformMtx44, m_viewMtx", "m_viewMtx, m_transformMtx44"),
    ("wrong projection source", "m_modelViewMtx, m_projectionMtx", "m_modelViewMtx, m_viewMtx"),
    ("omit screen product", "    m_modelScreenMtx = MultiplyViewportMatrices(m_modelViewProjectionMtx, m_screenMtx);", ""),
    ("transpose right matrix", "b[k][col]", "b[col][k]"),
    ("drop homogeneous lane", "k < 4", "k < 3"),
    ("round every addition", "double sum = 0.0;", "float sum = 0.0f;"),
    ("skip denormal flushing", "if ((bits & 0x7F800000u) == 0)", "if (false)"),
    ("invert current test", "g_currentViewport == this", "g_currentViewport != this"),
    ("omit upload", "        grcViewportUploadMatrices(this);", "        (void)this;"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/game/camera/pong_camera.cpp").read_text()
    start = source.index("namespace {\nfloat FlushViewportVmx")
    end = source.index("\n}\n", source.index("void grcViewport::RebuildCompositeMatrices()", start)) + 2
    body = source[start:end]
    for label, old, new in CASES:
        assert body.count(old) == 1, label
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name("grcviewport_rebuild_composite_matrices.py"),
                         Options(seed=1, patches=((body, body.replace(old, new)),))).run()
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} viewport mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
