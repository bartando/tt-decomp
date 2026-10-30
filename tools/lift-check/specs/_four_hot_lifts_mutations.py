"""Behavioral mutation proof; run from the repo root:
PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python \
    tools/lift-check/specs/_four_hot_lifts_mutations.py

Patch only build-cache copies, scoped to the target function. Only behavioral
FAIL (exit 1) counts; BUILD, SPEC, UNSUPPORTED, and a passing mutant fail the
proof. Use the specs' default trial counts and seed 1.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options


CASES = [
    ("locomotion_state_anim_get_mapped_weight", "src/game/creature/pong_creature.cpp",
     "bool LocomotionStateAnim_GetMappedWeight(", [
         ("empty lift", "    (void)self;", "    return false;\n    (void)self;"),
         ("accept invalid modes", "if (mode > 1)", "if (mode > 2)"),
         ("skip rotation mode", "if (mode > 1)", "if (mode != 0)"),
         ("wrong map stride", "animPair[1])[index]", "animPair[1])[index * 2]"),
         ("ignore negative slots", "if (slot < 0)", "if (slot == -1)"),
         ("wrong weight bank", "animPair[3])[slot]", "animPair[1])[slot]"),
         ("missing output", "    *outWeight = weight;", "    (void)outWeight;"),
         ("accept zero", "return weight > 0.0f;", "return weight >= 0.0f;"),
         ("accept NaN", "return weight > 0.0f;", "return !(weight <= 0.0f);"),
     ]),
    ("rage_mat44_inverse_affine_in_place", "src/rage/math/mat44.cpp",
     "bool mat44InverseAffineInPlace(", [
         ("empty lift", "    alignas(16) float snapshot[16];", "    return false;\n    alignas(16) float snapshot[16];"),
         ("aliased inverse source", "mat44InverseAffine(matrix, snapshot)", "mat44InverseAffine(matrix, matrix)"),
         ("wrong snapshot lane", "snapshot[i] = matrix[i];", "snapshot[i] = matrix[i ^ 1];"),
         ("reverse destination/source", "mat44InverseAffine(matrix, snapshot)", "mat44InverseAffine(snapshot, matrix)"),
         ("lose bool return", "return mat44InverseAffine(matrix, snapshot);", "mat44InverseAffine(matrix, snapshot);\n    return false;"),
         ("clobber w lane", "    return mat44InverseAffine(matrix, snapshot);", "    matrix[15] = 1.0f;\n    return mat44InverseAffine(matrix, snapshot);"),
     ]),
    ("cm_node_get_dim", "src/rage/misc/rage_cm.cpp",
     "int32_t cmNode_GetDim(", [
         ("empty lift", "    switch (port->m_type)", "    return 0;\n    switch (port->m_type)"),
         ("reversed port layout", "switch (port->m_type)", "switch (*reinterpret_cast<const uint32_t*>(port))"),
         ("truncate direct result", "*reinterpret_cast<const int32_t*>(port->m_pData)", "*reinterpret_cast<const uint8_t*>(port->m_pData)"),
         ("wrong virtual slot", "node->vtable[5]", "node->vtable[1]"),
         ("ignore callback output", "        return tmp;", "        return 0;"),
         ("nonzero disconnected port", "        return 0;", "        return 1;"),
     ]),
    ("grc_set_normalized_viewport", "src/graphics/grc_gpu_resources.cpp",
     "void grcSetNormalizedViewport(", [
         ("empty lift", "    float fLeft", "    return;\n    float fLeft"),
         ("skip null device", "    grcDevice_SetViewport(device, viewportRect);", "    if (device) grcDevice_SetViewport(device, viewportRect);"),
         ("use width for top", "fTop * screenH", "fTop * screenW"),
         ("round instead of truncate", "screenW * fLeft", "screenW * fLeft + 0.5f"),
         ("wrong chip-ID branch", "lbl_825C9030 == 0x1A220197", "lbl_825C9030 != 0x1A220197"),
         ("wrong depth endpoint", "depthB = oneF - fMaxDepth;", "depthB = oneF - fMinDepth;"),
         ("swap viewport coordinates", "viewportRect[2] = pixRight;", "viewportRect[2] = pixBottom;"),
     ]),
    ("cm_node_get_dim_shim", "src/rage/animation/cm_shims.cpp",
     "int cmNode_GetDim_stub(", [
         ("empty shim", "    return rage::cmNode_GetDim", "    return 0;\n    return rage::cmNode_GetDim"),
         ("legacy reversed layout", "    return rage::cmNode_GetDim(static_cast<const rage::cmNodePort*>(port));",
          "    const auto* p = static_cast<const cmNodePortLite*>(port);\n"
          "    if (p->m_type == 1) return *static_cast<const int32_t*>(p->m_pData);\n"
          "    if (p->m_type == 2) {\n"
          "        auto vtable = *static_cast<void***>(p->m_pData);\n"
          "        int32_t tmp = 0;\n"
          "        reinterpret_cast<void(*)(void*, int32_t*)>(vtable[5])(p->m_pData, &tmp);\n"
          "        return tmp;\n"
          "    }\n"
          "    return 0;"),
     ]),
]


def main():
    root = Path(__file__).resolve().parents[3]
    total = 0
    for spec_name, source_path, signature, mutations in CASES:
        source = (root / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, f"mutation anchor changed: {spec_name}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(Path(__file__).with_name(spec_name + ".py"),
                                 Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            except BuildError as exc:
                print(f"MISSED {spec_name}: {label}: BUILD {exc}", flush=True)
                return 1
            first = output.getvalue().splitlines()[0]
            print(f"{'CAUGHT' if rc == 1 else 'MISSED'} {spec_name}: {label}: {first}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        total += len(mutations)
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)} mutations", flush=True)
    print(f"Caught {total}/{total} mutations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
