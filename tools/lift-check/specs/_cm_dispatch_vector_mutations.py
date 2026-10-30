"""Run with PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python this file.

Patches affect cached build copies only. Only a behavioral FAIL (exit 1),
never a build or input error, proves a mutation was caught.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "src/rage/misc/rage_cm.cpp"
CASES = {
    "cm_node_get_vector": [
        ("missing w lane",
         "dst[0] = src[0]; dst[1] = src[1]; dst[2] = src[2]; dst[3] = src[3];",
         "dst[0] = src[0]; dst[1] = src[1]; dst[2] = src[2];"),
        ("wrong direct source",
         "const float* src = reinterpret_cast<const float*>(port->m_pData);",
         "const float* src = reinterpret_cast<const float*>(port->m_pData) + 1;"),
        ("wrong virtual slot",
         "reinterpret_cast<GetVecFn>(node->vtable[2])(node, dst);",
         "reinterpret_cast<GetVecFn>(node->vtable[3])(node, dst);"),
        ("nonzero disconnected vector",
         "dst[0] = dst[1] = dst[2] = dst[3] = 0.0f;",
         "dst[0] = dst[1] = dst[2] = dst[3] = 1.0f;"),
        ("wrong returned pointer",
         "    return dst;\n}\n\n/**\n * cmNode_GetFloat",
         "    return dst + 1;\n}\n\n/**\n * cmNode_GetFloat"),
    ],
    "cm_node_set_from_port_dispatch": [
        ("wrong tag source",
         "    switch (obj->m_dim) {",
         "    switch (port->m_type) {"),
        ("swapped integer dispatch targets",
         "    case 1:\n        obj->m_int = cmNode_GetDim(port);",
         "    case 1:\n        obj->m_int = cmNode_GetInt(port);"),
        ("bool overwrites adjacent bytes",
         "        obj->m_bool = cmNode_GetBool(port);",
         "        obj->m_int = cmNode_GetBool(port);"),
        ("missing vector copy",
         "        __builtin_memcpy(obj->m_vec4, result, sizeof(value));",
         "        (void)result;"),
        ("bypassed vector temporary",
         "        float* result = cmNode_GetVector(value, port);",
         "        float* result = cmNode_GetVector(obj->m_vec4, port);"),
        ("invalid tags write data",
         "    default:\n        break;\n    }\n}\n\n// ─────────────────────────────────────────────────────────────────────────────\n//  POLYNOMIAL SINE",
         "    default:\n        obj->m_int = 0;\n        break;\n    }\n}\n\n// ─────────────────────────────────────────────────────────────────────────────\n//  POLYNOMIAL SINE"),
    ],
}


def main():
    source = (ROOT / SOURCE).read_text()
    for spec_name, mutations in CASES.items():
        spec = Path(__file__).with_name(spec_name + ".py")
        # Ensure this setup can pass before interpreting any mutant failure.
        if Checker(spec, Options(trials=128, seed=1)).run() != 0:
            return 1
        for name, old, new in mutations:
            assert source.count(old) == 1, (name, source.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(spec, Options(trials=128, seed=1,
                                          patches=((old, new),))).run()
            status = "CAUGHT" if rc == 1 else "MISSED"
            print(f"{spec_name}: {status} {name}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
        print(f"{spec_name}: caught {len(mutations)}/{len(mutations)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
