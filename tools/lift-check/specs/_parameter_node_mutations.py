"""Cached-body mutation proof. Only behavioral FAILs count, never faults.
Run with PYTHONPATH=tools/lift-check and tools/lift-check/.venv/bin/python.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ('cm_operator_clear_name', 'void cmOperator_ClearName(', [
        ('wrong primary ownership bit', 'node->flags & 1', 'node->flags & 2'),
        ('omit value cleanup', '    releaseText(node);', '    (void)node;'),
    ]),
    ('cm_operator_set_primary_name', 'void cmOperator_SetPrimaryName(', [
        ('skip old name release', 'if (node->flags & 1)', 'if (false)'),
        ('skip byte truncation', 'static_cast<uint8_t>(copy)', 'copy'),
        ('drop borrowed name', 'node->name = name;', 'node->name = nullptr;'),
        ('clear unrelated flags', 'node->flags &= uint8_t(~1u);', 'node->flags = 0;'),
    ]),
    ('cm_operator_set_secondary_name', 'void cmOperator_SetSecondaryName(', [
        ('skip old text release', '    releaseText(node);', '    (void)node;'),
        ('skip byte truncation', 'static_cast<uint8_t>(copy)', 'copy'),
        ('wrong owned bit', 'node->flags |= 2;', 'node->flags |= 1;'),
        ('retain old type', '    node->type = 0;', '    (void)node;'),
    ]),
    ('cm_operator_set_integer_value', 'void cmOperator_SetIntegerValue(', [
        ('wrong type', 'node->type = 1;', 'node->type = 2;'),
        ('wrong value', 'static_cast<uint32_t>(value);', 'static_cast<uint32_t>(value) + 1;'),
        ('omit owned text cleanup', '    releaseText(node);', '    (void)node;'),
    ]),
    ('cm_operator_set_real_value', 'void cmOperator_SetRealValue(', [
        ('wrong type', 'node->type = 2;', 'node->type = 1;'),
        ('zero value', 'std::memcpy(&node->value, &value, sizeof(value));', 'node->value = 0;'),
        ('omit owned text cleanup', '    releaseText(node);', '    (void)node;'),
    ]),
    ('cm_operator_set_boolean_value', 'void cmOperator_SetBooleanValue(', [
        ('overwrite padding', '*reinterpret_cast<uint8_t*>(&node->value) = static_cast<uint8_t>(value);', 'node->value = static_cast<uint8_t>(value);'),
        ('normalize boolean', 'static_cast<uint8_t>(value);', 'value != 0;'),
        ('wrong type', 'node->type = 3;', 'node->type = 1;'),
        ('omit owned text cleanup', '    releaseText(node);', '    (void)node;'),
    ]),
    ('cm_operator_clear_name', 'void releaseText(', [
        ('free non-text payload', 'node->type == 0 && ', ''),
        ('wrong value ownership bit', '(node->flags & 2)', '(node->flags & 1)'),
    ]),
    ('parameter_pointer_array_append', 'void* atFreeList_Alloc(', [
        ('wrong growth', 'array->capacity + 16', 'array->capacity + 8'),
        ('drop existing entries', 'i < array->count', 'i < 0'),
        ('ignore low byte ownership', '(rage_FindSingleton(old) & 255) == 0', 'rage_FindSingleton(old) == 0'),
        ('skip counter update', 'array->count + 1', 'array->count'),
        ('wrong return slot', 'return slot;', 'return slot + 1;'),
    ]),
    ('cm_operator_set_int', 'ParameterNode* createNode(', [
        ('wrong initial type', 'node->type = 0;', 'node->type = 1;'),
        ('wrong initial flags', 'node->flags = 0;', 'node->flags = 255;'),
    ]),
    ('cm_operator_set_int', 'void cmOperator_SetInt(', [
        ('ignore redirected slot', 'cmOperator_SetIntegerValue(slot->get(), value);', 'cmOperator_SetIntegerValue(node, value);'),
        ('wrong value', 'slot->get(), value);', 'slot->get(), value + 1);'),
        ('omit dirty flag clear', 'static_cast<uint8_t*>(owner)[4] &= uint8_t(~2u);', '(void)owner;'),
    ]),
    ('cm_operator_set_float', 'void cmOperator_SetFloat(', [
        ('ignore redirected slot', 'cmOperator_SetRealValue(slot->get(), value);', 'cmOperator_SetRealValue(node, value);'),
        ('wrong value', 'slot->get(), value);', 'slot->get(), 0.0f);'),
        ('clear all flags', 'static_cast<uint8_t*>(owner)[4] &= uint8_t(~2u);', 'static_cast<uint8_t*>(owner)[4] = 0;'),
    ]),
]

def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/data/parameter_node.cpp').read_text()
    total = 0
    for spec, signature, mutations in CASES:
        start = source.index(signature)
        end = source.index('\n}\n', start) + 2
        body = source[start:end]
        for label, old, new in mutations:
            assert body.count(old) == 1, (spec, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'), Options(seed=1, patches=((body, body.replace(old, new)),))).run()
            report = output.getvalue()
            caught = rc == 1 and 'faulted' not in report
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {label}: {report.splitlines()[0]}", flush=True)
            if not caught:
                print(report)
                return 1
            total += 1
    print(f'Caught {total}/{total} behavioral mutations', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
