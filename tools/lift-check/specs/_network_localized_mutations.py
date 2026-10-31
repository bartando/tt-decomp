"""Ensure localization specs reject UTF-8, hash/cache and fallback regressions."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
SOURCE = 'src/rage/data/localized_text.cpp'
CASES = {
    'network_localized_copy': [
        ('capacity', 'written + count >= limit', 'written + count > limit'),
        ('UTF-8 boundary', 'character < 0x800', 'character < 0x801'),
        ('continuation bits', 'encoded[2] = static_cast<char>(0x80 | (character & 0x3F));', 'encoded[2] = static_cast<char>(0x80 | (character & 0x1F));'),
        ('control replacement', "destination[i] = '\\r';", "destination[i] = '\\n';"),
        ('terminator', 'destination[written] = 0;', 'destination[written + 1] = 0;'),
    ],
    'network_localized_hash': [
        ('signed bytes', 'const int8_t character = static_cast<int8_t>(*key++)', 'const uint8_t character = static_cast<uint8_t>(*key++)'),
        ('shift', 'hash * 16 +', 'hash * 8 +'),
    ],
    'network_localized_wide_length': [
        ('length', 'static_cast<uint32_t>(end - text);', 'static_cast<uint32_t>(end - text) + 1;'),
    ],
    'network_localized_wide_duplicate': [
        ('terminator', 'localizedWideLength(text) + 1;', 'localizedWideLength(text);'),
        ('allocation bytes', 'rage_Alloc(count > 0x7FFFFFFFu ? UINT32_MAX : count * 2)', 'rage_Alloc(count > 0x7FFFFFFFu ? UINT32_MAX : count * 2 + 2)'),
    ],
    'network_localized_insert': [
        ('count', '++table->count;', '--table->count;'),
        ('entry hash', 'added->hash = hash;', 'added->hash = hash + 1;'),
    ],
    'network_localized_lookup': [
        ('lookup hash', 'if (node->hash == hash) {', 'if (node->hash != hash) {'),
        ('fallback byte', 'fallback[i] = static_cast<uint8_t>(key[i]);', 'fallback[i] = static_cast<int8_t>(key[i]);'),
        ('fallback scale', 'text->scaleX = 1.0f;', 'text->scaleX = 0.0f;'),
        ('fallback flag', 'text->field16 = 1;', 'text->field16 = 0;'),
        ('font name', 'localizedFontCreate(g_localizationDefaultFontName.get())', 'localizedFontCreate(key)'),
    ],
}

def main():
    source = (Path(__file__).resolve().parents[3] / SOURCE).read_text()
    total = 0
    for spec, mutations in CASES.items():
        for label, old, new in mutations:
            assert source.count(old) == 1, (spec, label, source.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=192, seed=1, patches=((old,new),))).run()
            print(f"{spec}: {'CAUGHT' if rc == 1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}", flush=True)
            if rc != 1:
                print(output.getvalue())
                return 1
            total += 1
    print(f'Caught {total}/{total} mutations', flush=True)
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
