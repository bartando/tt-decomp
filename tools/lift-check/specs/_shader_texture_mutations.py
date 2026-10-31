"""Only behavioral FAIL counts, including virtual results and publication order."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
    'render_shader_set_texture': [
        ('lose counter increment', '    ++g_grmShaderFx_boundContext;\n    if (texture == nullptr)', '    if (texture == nullptr)'),
        ('drop null fallback', '        texture = g_grcDefaultTexture;', '        texture = nullptr;'),
        ('lose virtual result', 'memcpy(bank + slot, &resource, sizeof(resource));', '/* resource lost */'),
        ('retain descriptor high bits', 'const uint32_t slot = table->entries[(handle >> 18) * 2 + 1] & 0xFFFFu;\n    ShaderVector* bank', 'const uint32_t slot = table->entries[(handle >> 18) * 2 + 1];\n    ShaderVector* bank'),
        ('wrong dirty byte', 'table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7];\n    memcpy(bank + slot', 'table->dirtyBits[bit >> 4] |= g_shaderParameterDirtyMasks[bit & 7];\n    memcpy(bank + slot'),
        ('capture table before virtual', '    void* resource = static_cast<rage::grcTexture*>(texture)->GetShaderResource();\n    // The virtual can change the active table; capture it only after the call.\n    ShaderTable* table = lbl_825EBC40;', '    ShaderTable* table = lbl_825EBC40;\n    void* resource = static_cast<rage::grcTexture*>(texture)->GetShaderResource();'),
    ],
    'texture_reference_shader_resource': [
        ('drop resource result', 'return texture->GetShaderResource();', 'texture->GetShaderResource(); return nullptr;'),
        ('wrong virtual slot', 'return texture->GetShaderResource();', 'return texture->GetPlatformTexture();'),
        ('drop fallback', 'texture = static_cast<grcTexture*>(::g_grcDefaultTexture);\n    return texture->GetShaderResource();', 'texture = nullptr;\n    return texture->GetShaderResource();'),
    ],
    'texture_reference_apply_state': [
        ('drop state forwarding', 'texture->ApplyState(param);', '/* state lost */'),
        ('wrong state argument', 'texture->ApplyState(param);', 'texture->ApplyState(nullptr);'),
        ('drop fallback state', 'texture = static_cast<grcTexture*>(::g_grcDefaultTexture);\n    texture->ApplyState(param);', 'texture = nullptr;\n    texture->ApplyState(param);'),
    ],
    'texture_reference_width': [
        ('lose width result', 'return texture ? texture->GetWidth() : 0;', 'if (texture) texture->GetWidth(); return 0;'),
        ('wrong dimension slot', 'return texture ? texture->GetWidth() : 0;', 'return texture ? texture->GetHeight() : 0;'),
        ('wrong empty width', 'return texture ? texture->GetWidth() : 0;', 'return texture ? texture->GetWidth() : 1;'),
    ],
    'texture_reference_height': [
        ('lose height result', 'return texture ? texture->GetHeight() : 0;', 'if (texture) texture->GetHeight(); return 0;'),
        ('wrong dimension slot', 'return texture ? texture->GetHeight() : 0;', 'return texture ? texture->GetWidth() : 0;'),
        ('wrong empty height', 'return texture ? texture->GetHeight() : 0;', 'return texture ? texture->GetHeight() : 1;'),
    ],
}


def main():
    root = Path(__file__).resolve().parents[3]
    count = 0
    for spec, cases in CASES.items():
        file = 'src/game/pong_render.cpp' if spec.startswith('render_') else 'src/graphics/texture_reference.cpp'
        source = (root / file).read_text()
        for name, old, new in cases:
            assert source.count(old) == 1, name
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=256, seed=1, patches=((old, new),))).run()
            first = out.getvalue().splitlines()[0]
            caught = rc == 1 and first.startswith('FAIL ')
            print(f"{'CAUGHT' if caught else 'MISSED'} {spec}: {name}: {first}", flush=True)
            if not caught:
                print(out.getvalue())
                return 1
            count += 1
    print(f'Caught {count}/{sum(map(len, CASES.values()))} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
