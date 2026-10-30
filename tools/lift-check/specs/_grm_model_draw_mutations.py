"""Behavioral mutation proof; edits touch only lift-check's build-cache copies.

Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_grm_model_draw_mutations.py
Only FAIL (exit 1) counts; BUILD, SPEC and UNSUPPORTED never count.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

MUTATIONS = (
    ("truncate geometry count", "i < m_geometryCount;", "i < static_cast<uint8_t>(m_geometryCount);"),
    ("cache count across callback", "uint32_t i = 0; i < m_geometryCount;",
     "uint32_t i = 0, count = m_geometryCount; i < count;"),
    ("truncate shader index", "shaderGroup->m_pShaders[m_pShaderIndices[i]];",
     "shaderGroup->m_pShaders[static_cast<uint8_t>(m_pShaderIndices[i])];"),
    ("wrong filter argument", "if (type != shaderFilter)", "if (type != matrixCount)"),
    ("truncate filter", "if (type != shaderFilter)", "if (type != (shaderFilter & 31))"),
    ("wrong shader type bits", "(shader->m_flags >> 5) & 31", "(shader->m_flags >> 4) & 31"),
    ("ignore forced bit zero", "(shader->m_flags & 1) != 0", "false"),
    ("apply bit zero to ordinary shaders", "forcedShader != nullptr && (shader->m_flags & 1) != 0",
     "(shader->m_flags & 1) != 0"),
    ("ignore forced shader", "grmShader* shader = forcedShader != nullptr ? forcedShader :",
     "grmShader* shader = false ? forcedShader :"),
    ("omit queue override", "if (drawQueue != nullptr)", "if (false)"),
    ("wrong queued geometry", "grmDrawQueue_AddGeometry(drawQueue, shader, this, i);",
     "grmDrawQueue_AddGeometry(drawQueue, shader, this, i + 1);"),
    ("always end run", "bool endOfRun = i + 1 == m_geometryCount;", "bool endOfRun = true;"),
    ("omit forced final run end", "bool endOfRun = i + 1 == m_geometryCount;", "bool endOfRun = false;"),
    ("invert adjacent key test", "shader->m_drawKey != next->m_drawKey", "shader->m_drawKey == next->m_drawKey"),
    ("wrong virtual slot", "shader->vtable[4]", "shader->vtable[3]"),
    ("swap matrix count and lod", "draw(shader, this, i, transforms, matrixCount, lod, endOfRun);",
     "draw(shader, this, i, transforms, lod, matrixCount, endOfRun);"),
    ("omit forced shader reload", "forcedShader = static_cast<grmShader*>(g_currentGeometry);",
     "/* stale forced shader */"),
    ("omit queue reload", "drawQueue = g_iccProfilePtr;", "/* stale draw queue */"),
    ("cache shader indices", "for (uint32_t i = 0; i < m_geometryCount; ++i) {",
     "auto* cachedIndices = m_pShaderIndices;\n    for (uint32_t i = 0; i < m_geometryCount; ++i) {"),
    ("cache shader array", "for (uint32_t i = 0; i < m_geometryCount; ++i) {",
     "auto** cachedShaders = shaderGroup->m_pShaders;\n    for (uint32_t i = 0; i < m_geometryCount; ++i) {"),
)


def main():
    root = Path(__file__).resolve().parents[3]
    source = (root / "src/rage/rage_grm.cpp").read_text()
    spec = Path(__file__).with_name("grm_model_draw.py")
    for name, old, new in MUTATIONS:
        # Reload anchors also occur in their initialized declarations. Match
        # indentation to mutate only the assignment after the virtual call.
        if name in ("omit forced shader reload", "omit queue reload"):
            old, new = "        " + old, "        " + new
        assert source.count(old) == 1, f"mutation anchor changed: {name}"
        patches = ((old, new),)
        if name == "cache shader indices":
            patches += (("m_pShaderIndices[i]", "cachedIndices[i]"),
                        ("m_pShaderIndices[i + 1]", "cachedIndices[i + 1]"))
        elif name == "cache shader array":
            patches += (("shaderGroup->m_pShaders[", "cachedShaders["),)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(spec, Options(trials=1000, seed=1, patches=patches)).run()
        first = output.getvalue().splitlines()[0]
        print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {name}: {first}", flush=True)
        if rc != 1:
            print(output.getvalue())
            return 1
    print(f"Caught {len(MUTATIONS)}/{len(MUTATIONS)} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
