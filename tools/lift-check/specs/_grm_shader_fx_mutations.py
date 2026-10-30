"""Run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_grm_shader_fx_mutations.py

Mutations touch build-cache copies only. Only behavioral FAIL (exit 1) counts;
build, input-spec and unsupported-instruction errors do not count as caught.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options


DISPATCH = [
    ("omit active shader publication",
     "g_grmShaderFx_activeState = reinterpret_cast<uintptr_t>(this);",
     "/* active shader left stale */"),
    ("omit frame snapshot",
     "*reinterpret_cast<uint32_t*>(self + 44) = frame;",
     "/* frame snapshot left stale */"),
    ("publish frame after flush",
     "*reinterpret_cast<uint32_t*>(self + 44) = frame;",
     "/* frame snapshot delayed */"),
    ("ignore forced variant",
     "return static_cast<uint32_t>(forced);",
     "return g_grmShaderFx_defaultVariant;"),
    ("ignore override flag",
     "if (overrideFlag != 0)", "if (false)"),
    ("read fallback instead of override",
     "return *(&g_grmShaderFx_defaultVariant - 1);",
     "return g_grmShaderFx_defaultVariant;"),
    ("require both flush latches",
     "g_grmShaderFx_flushRequired != 0 ||", "g_grmShaderFx_flushRequired != 0 &&"),
    ("ignore force-reset latch",
     "g_grmShaderFx_forceResetFlag != 0) {", "false) {"),
    ("truncate flush latch to a byte",
     "g_grmShaderFx_flushRequired != 0 ||", "(g_grmShaderFx_flushRequired & 0xff) != 0 ||"),
    ("truncate force-reset latch to a byte",
     "g_grmShaderFx_forceResetFlag != 0) {", "(g_grmShaderFx_forceResetFlag & 0xff) != 0) {"),
    ("wrong effect slot",
     "const uint32_t effectSlot = reinterpret_cast<uintptr_t>(self + 16);",
     "const uint32_t effectSlot = reinterpret_cast<uintptr_t>(self + 20);"),
    ("wrong direct entry",
     "grmShaderInstance_Bind(effectSlot, directEntry, callerContext);",
     "grmShaderInstance_Bind(effectSlot, passIndex, callerContext);"),
    ("lose caller flags on table path",
     "grmShaderInstance_Bind(effectSlot, passEntry, callerContext);",
     "grmShaderInstance_Bind(effectSlot, passEntry, 0);"),
    ("wrong variant stride",
     "const uint32_t flatIndex = (variantIndex << 2) + passIndex;",
     "const uint32_t flatIndex = (variantIndex << 1) + passIndex;"),
    ("ignore pass index",
     "const uint32_t flatIndex = (variantIndex << 2) + passIndex;",
     "const uint32_t flatIndex = (variantIndex << 2);"),
]

CONSTANT_SLOT = [
    ("wrong descriptor prologue",
     "static_cast<uintptr_t>(paramArrayVA))[varIndex + 3];",
     "static_cast<uintptr_t>(paramArrayVA))[varIndex + 2];"),
    ("swap upload arguments",
     "rage_8C48(activeInstance, paramDesc);", "rage_8C48(paramDesc, activeInstance);"),
    ("omit descriptor upload",
     "rage_8C48(activeInstance, paramDesc);", "/* descriptor not uploaded */"),
    ("cache context in wrong field",
     "uint32_t* boundCtx = reinterpret_cast<uint32_t*>(self + 32);",
     "uint32_t* boundCtx = reinterpret_cast<uint32_t*>(self + 28);"),
    ("ignore context changes",
     "if (currentCtx != nextCtx)", "if (false)"),
    ("omit context cache write",
     "*boundCtx = nextCtx;", "/* context left stale */"),
    ("skip commit when either cache matches",
     "if (!contextChanged && g_grmShaderFx_boundParam == liveInstance)",
     "if (!contextChanged || g_grmShaderFx_boundParam == liveInstance)"),
    ("always commit cached state",
     "if (!contextChanged && g_grmShaderFx_boundParam == liveInstance)",
     "if (false)"),
    ("omit instance cache publication",
     "g_grmShaderFx_boundParam = liveInstance;", "/* instance left stale */"),
    ("commit before instance cache publication",
     "g_grmShaderFx_boundParam = liveInstance;\n    grmShaderInstance_FilterAndUploadParameters(liveInstance);",
     "grmShaderInstance_FilterAndUploadParameters(liveInstance);\n    g_grmShaderFx_boundParam = liveInstance;"),
    ("omit parameter commit",
     "grmShaderInstance_FilterAndUploadParameters(liveInstance);", "/* parameters not committed */"),
]


def main():
    source = (Path(__file__).resolve().parents[3] / "src/rage/rage_grm.cpp").read_text()
    total = 0
    for spec_name, mutations in [("grm_shader_fx_dispatch", DISPATCH),
                                 ("grm_shader_fx_bind_constant_slot", CONSTANT_SLOT)]:
        for label, old, new in mutations:
            assert source.count(old) == 1, f"mutation anchor changed: {label}"
            patches = [(old, new)]
            if label == "publish frame after flush":
                anchor = "        grcDevice_FlushRenderState();\n    }"
                assert source.count(anchor) == 1
                patches.append((anchor, anchor + "\n    *reinterpret_cast<uint32_t*>(self + 44) = frame;"))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                             Options(seed=1, patches=tuple(patches))).run()
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
        total += len(mutations)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
