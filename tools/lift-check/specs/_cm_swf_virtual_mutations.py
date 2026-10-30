"""Run from root: PYTHONPATH=tools/lift-check tools/lift-check/.venv/bin/python this-file.

Only cached translation units are patched. Baselines must pass; a mutant counts
only on behavioral FAIL (rc=1), never BUILD/SPEC/UNSUPPORTED. Full default spec
trials are available to each mutation; most fail in the first few trials.
"""
import contextlib
import io
from pathlib import Path

from liftcheck.build import BuildError
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CM = "src/rage/misc/rage_cm.cpp"
SWF = "src/rage/swf.cpp"
CASES = [
    ("cm_add_get_float", CM, "void cmAdd::GetFloat(", [
        ("multiply instead of add", "*out = a + b;", "*out = a * b;"),
        ("read first port twice", "cmNode_GetFloat(&portB)", "cmNode_GetFloat(&portA)"),
        ("reverse evaluation order",
         "float a = cmNode_GetFloat(&portA);\n    float b = cmNode_GetFloat(&portB);",
         "float b = cmNode_GetFloat(&portB);\n    float a = cmNode_GetFloat(&portA);"),
        ("write adjacent output", "*out = a + b;", "out[1] = a + b;"),
        ("reverse pointer/tag layout", "float a = cmNode_GetFloat(&portA);",
         "cmNodePort bad = {reinterpret_cast<void*>(static_cast<uintptr_t>(portA.m_type)),\n"
         "                      static_cast<cmPortType>(reinterpret_cast<uintptr_t>(portA.m_pData))};\n"
         "    float a = cmNode_GetFloat(&bad);"),
    ]),
    ("cm_multiply_get_float", CM, "void cmMultiply::GetFloat(", [
        ("add instead of multiply", "*out = a * b;", "*out = a + b;"),
        ("read first port twice", "cmNode_GetFloat(&portB)", "cmNode_GetFloat(&portA)"),
        ("omit first port evaluation", "float a = cmNode_GetFloat(&portA);", "float a = 1.0f;"),
        ("write adjacent output", "*out = a * b;", "out[1] = a * b;"),
        ("reverse pointer/tag layout", "float a = cmNode_GetFloat(&portA);",
         "cmNodePort bad = {reinterpret_cast<void*>(static_cast<uintptr_t>(portA.m_type)),\n"
         "                      static_cast<cmPortType>(reinterpret_cast<uintptr_t>(portA.m_pData))};\n"
         "    float a = cmNode_GetFloat(&bad);"),
    ]),
    ("cm_changed_tick", CM, "void cmChanged::Tick(", [
        ("dispatch on connection tag", "switch (cmNode_GetPortDim(&port))", "switch (port.m_type)"),
        ("truncate full-width dimension", "switch (cmNode_GetPortDim(&port))", "switch (cmNode_GetPortDim(&port) & 255)"),
        ("wrong dimension evaluator", "int32_t value = cmNode_GetDim(&port);", "int32_t value = cmNode_GetInt(&port);"),
        ("normalize boolean payload", "uint8_t value = cmNode_GetBool(&port);", "uint8_t value = cmNode_GetBool(&port) != 0;"),
        ("widen byte history write", "*static_cast<uint8_t*>(m_pPrevious) = value;", "*static_cast<uint32_t*>(m_pPrevious) = value;"),
        ("ignore initial suppression", "!m_suppress &&", ""),
        ("keep suppression flag", "m_suppress = 0;", "m_suppress = m_suppress;"),
        ("clear unsupported output", "default:\n        break;", "default:\n        *m_pChanged = 0;\n        break;"),
        ("keep old integer history", "*static_cast<int32_t*>(m_pPrevious) = value;", "(void)value;"),
    ]),
    ("swf_scriptobject_invoke", SWF, "void swfSCRIPTOBJECT::Invoke(", [
        ("bypass virtual lookup", "this->GetMember(", "this->swfSCRIPTOBJECT::GetMember("),
        ("wrong lookup key tag", "methodName, 1 }", "methodName, 7 }"),
        ("wrong empty result tag", "lookupResult = { 0, 7 }", "lookupResult = { 0, 0 }"),
        ("test full lookup return", "uint8_t(found) == 0", "found == 0"),
        ("wrong native arguments", "fn(this, args, argCount, outResult);", "fn(this, outResult, argCount, outResult);"),
        ("bypass virtual execution", "callableObj->Execute(", "callableObj->swfACTIONFUNC::Execute("),
        ("unsigned depth comparison",
         "static_cast<int32_t>(g_swfCallDepth) > static_cast<int32_t>(prevDepth)",
         "g_swfCallDepth > prevDepth"),
        ("omit post-lookup depth snapshot", "uint32_t prevDepth = g_swfCallDepth;", "uint32_t prevDepth = 0;"),
        ("pop directly into caller result", "swfPopResult(&popped)", "swfPopResult(outResult)"),
        ("omit popped type word",
         "*resultValue = *static_cast<swfValuePair*>(swfPopResult(&popped));",
         "resultValue->data = static_cast<swfValuePair*>(swfPopResult(&popped))->data;"),
    ]),
    ("swf_pop_result", SWF, "void* swfPopResult(void* dst) {", [
        ("omit stack decrement", "--depth;", "(void)depth;"),
        ("copy payload as type", "out[1] = stack[depth * 2 + 1];", "out[1] = stack[depth * 2];"),
        ("wrong empty-pop type", "stack[1] = 3;", "stack[1] = 7;"),
        ("wrong destination return", "return dst;", "return out + 1;"),
    ]),
]


def main():
    total = 0
    for spec_name, source_path, signature, mutations in CASES:
        spec = Path(__file__).with_name(spec_name + ".py")
        if Checker(spec, Options(seed=1)).run() != 0:
            return 1
        source = (ROOT / source_path).read_text()
        start = source.index(signature)
        end = source.index("\n}\n", start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert old in body, f"mutation anchor changed: {spec_name}: {label}"
            output = io.StringIO()
            try:
                with contextlib.redirect_stdout(output):
                    rc = Checker(spec, Options(seed=1, patches=((body, body.replace(old, new)),))).run()
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
    print(f"Caught {total}/{total} mutations", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
