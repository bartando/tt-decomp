"""Cached-body mutation proof; only behavioral failures count, never faults."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [('fi_path_concat',
  'void rage_strcat_bounded(',
  [('reserve no terminator', '- length - 1', '- length - 0'),
   ('ignore existing text', 'destination ? std::strlen(destination) : 0', '0')]),
 ('fi_path_remove_parent',
  'int32_t fiPath_RemoveParentDir(',
  [('search wrong delimiter', "std::strchr(path, '.')", "std::strchr(path, ':')"),
   ('wrong collapse return', 'return 1;', 'return 0;')]),
 ('fi_path_append_name',
  'void fiPath_AppendName(',
  [('duplicate matching extension',
    "_stricmp(std::strrchr(name, '.') + 1, extension) != 0",
    "_stricmp(std::strrchr(name, '.') + 1, extension) == 0"),
   ('wrong basename threshold', '> 42', '> 41'),
   ('skip replacement option', 'if (g_fiLongNameOptionValue)', 'if (false)')]),
 ('fi_path_build',
  'void fiPath_Build(',
  [('wrong root stride', 'root * 128', 'root * 64'),
   ('skip dollar prefix', 'name += 2;', 'name += 0;'),
   ('omit normalization', 'while (fiPath_RemoveParentDir(out)) {}', '(void)out;')])]

def main():
    source = (Path(__file__).resolve().parents[3] / 'src/rage/io/fiPath.cpp').read_text()
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
