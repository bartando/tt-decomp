"""Cached-body mutation proof; only behavioral failures count, never faults."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [('fi_stream_open_all',
  'void* fiStreamBuf_OpenAll(',
  [('stop after first root', 'root < *roots && !result', 'root < *roots && root < 1 && !result'),
   ('discard successful stream', 'return result;', 'return nullptr;'),
   ('drop open flags', 'fiStream_Open(path, flags)', 'fiStream_Open(path, 0)')]),
 ('fi_stream_read',
  'int32_t fiStreamBuf_Read(',
  [('wrong buffered count', 'copied = s->end - s->cursor;', 'copied = 0;'),
   ('skip absolute consumed advance',
    's->position += static_cast<uint32_t>(s->cursor);',
    's->position += 0;'),
   ('wrong direct threshold', 'bytes >= s->capacity', 'bytes > s->capacity'),
   ('drop direct return count', 'return got + copied;', 'return copied;'),
   ('omit cursor advance', 's->cursor += count;', 's->cursor += 0;'),
   ('ignore flush failure', 'fiStreamBuf_Finalize(s) < 0', 'fiStreamBuf_Finalize(s) > 0')]),
 ('fi_stream_finalize',
  'int32_t fiStreamBuf_Finalize(',
  [('seek to buffer origin', 's->position + static_cast<uint32_t>(s->cursor)', 's->position'),
   ('write wrong byte count', 's->buffer.get(), s->cursor', 's->buffer.get(), s->capacity'),
   ('skip reset cursor', 's->cursor = 0;', 's->cursor = cursor;'),
   ('lose flush result', 'return device->Flush(handle);', 'device->Flush(handle); return 0;')]),
 ('fi_stream_reset',
  'int32_t fiStreamBuf_Reset(',
  [('ignore finalize failure', 'fiStreamBuf_Finalize(s) < 0', 'fiStreamBuf_Finalize(s) > 0'),
   ('wrong seek origin',
    'device->Seek(s->handle, position, 0)',
    'device->Seek(s->handle, position, 1)'),
   ('omit new absolute position',
    's->position = static_cast<uint32_t>(position);',
    's->position = 0;')]),
 ('fi_stream_close',
  'int32_t fiStreamBuf_Close(',
  [('flush read window', 's->end == 0 && s->cursor != 0', 's->end != 0 && s->cursor != 0'),
   ('retain closed handle', 's->handle = 0xffffffffu;', 's->handle = 0;'),
   ('retain occupied pool slot', 's->device = nullptr;', '(void)s;')]),
 ('fi_stream_read_words',
  'int32_t fiStreamBuf_ReadWords(',
  [('request wrong byte count',
    'static_cast<uint32_t>(words) << 2',
    'static_cast<uint32_t>(words) << 1'),
   ('return bytes', 'return count;', 'return bytes;'),
   ('omit endian conversion', 'word = __builtin_bswap32(word);', 'word = word;')])]

def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/io/fiStreamBuf.cpp').read_text()
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
