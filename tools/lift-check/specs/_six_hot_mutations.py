"""Run from the repo root with PYTHONPATH=tools/lift-check and its venv Python.
Patches affect build copies only; only behavioral FAIL counts as caught.
"""
import contextlib
import io
import sys
from pathlib import Path
from liftcheck.runner import Checker, Options

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    "cr_anim_dof_quaternion_evaluate": [
        ("wrong output", "crAnimDof_BlendQuaternion(outQuat, animContext,", "crAnimDof_BlendQuaternion(this, animContext,"),
        ("wrong context", "crAnimDof_BlendQuaternion(outQuat, animContext,", "crAnimDof_BlendQuaternion(outQuat, this,"),
        ("wrong quaternion offset", "reinterpret_cast<char*>(this) + 16));", "reinterpret_cast<char*>(this) + 20));"),
    ],
    "cr_anim_dof_quaternion_set_value": [
        ("omit second pair", "__builtin_memcpy(quat + 8, &pair, 8);", "(void)pair;"),
        ("swap pairs", "__builtin_memcpy(&pair, source + 8, 8);", "__builtin_memcpy(&pair, source, 8);"),
        ("snapshot overlapping source", "__builtin_memcpy(&pair, source, 8);\n    __builtin_memcpy(quat, &pair, 8);\n    __builtin_memcpy(&pair, source + 8, 8);\n    __builtin_memcpy(quat + 8, &pair, 8);", "__builtin_memmove(quat, source, 16);"),
    ],
    "grm_shader_fx_clear_active": [
        ("leave state set", "g_grmShaderFx_activeState = 0;", "g_grmShaderFx_activeState = 1;"),
        ("wrong unbind argument", "grmShaderInstance_Unbind(oldInstance);", "grmShaderInstance_Unbind(0);"),
        ("omit final clear", "g_grmShaderFx_activeInstance = 0;", "(void)oldInstance;"),
    ],
    "sysmem_simple_allocate_locked": [
        ("omit lock", "sysMemSimpleAllocator_SpinAcquire(&g_sysMemAllocatorInitLock);", "(void)0;"),
        ("wrong size", "Allocate(size, alignment);", "Allocate(size + 1, alignment);"),
        ("wrong alignment", "Allocate(size, alignment);", "Allocate(size, alignment ^ 1);"),
        ("omit unlock", "g_sysMemAllocatorInitLock = 0;", "(void)0;"),
        ("lose result", "return result;", "return nullptr;"),
    ],
    "rage_free": [
        ("remove null guard", "if (!ptr || (uint8_t)rage_FindSingleton(ptr))", "if ((uint8_t)rage_FindSingleton(ptr))"),
        ("invert singleton test", "if (!ptr || (uint8_t)rage_FindSingleton(ptr))", "if (!ptr || !(uint8_t)rage_FindSingleton(ptr))"),
        ("wrong allocator argument", "allocator->vtable->Free(allocator, ptr);", "allocator->vtable->Free(allocator, allocator);"),
    ],
    "xe_get_current_thread_id": [
        ("wrong thread field", "thread + 0x14C", "thread + 0x148"),
        ("wrong sda field", "g_sda_base + 0x100", "g_sda_base + 0xFC"),
        ("truncate ID", "return *(const uint32_t*)(thread + 0x14C);", "return *(const uint32_t*)(thread + 0x14C) & 255;"),
    ],
}


def main():
    for name, cases in CASES.items():
        if len(sys.argv) > 1 and name not in sys.argv[1:]:
            continue
        spec = Path(__file__).with_name(name + ".py")
        namespace = {}
        exec(spec.read_text(), namespace)
        source = (ROOT / namespace["SOURCE"]).read_text()
        # Scope patches to the target function, since several TUs reuse snippets.
        marker = namespace["FUNCTION"].removeprefix("rage::") + "("
        start = source.index(marker)
        end = source.index("\n}", start) + 2
        function = source[start:end]
        for label, old, new in cases:
            assert function.count(old) == 1, (name, label)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(spec, Options(trials=1000, seed=1,
                    patches=((function, function.replace(old, new, 1)),))).run()
            print(f"{name}: {'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
