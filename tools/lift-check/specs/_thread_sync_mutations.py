"""Only behavioral FAIL counts; patch build-cache copies, never tracked sources."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = {
 'sys_thread_timeout_value': [
  ('wrong infinite timeout', 'milliseconds == UINT32_MAX', 'milliseconds == 0x7FFFFFFFu'),
  ('wrong timeout units', '* 10000;', '* 1000;'),
  ('signed milliseconds', '-static_cast<int64_t>(milliseconds)', '-static_cast<int64_t>(static_cast<int32_t>(milliseconds))'),
 ],
 'sys_thread_map_status_error': [
  ('suppress on low byte only', '*reinterpret_cast<uint32_t*>(sda + 0x150) == 0', '(*reinterpret_cast<uint32_t*>(sda + 0x150) & 0xFFu) == 0'),
  ('omit error publication', '*reinterpret_cast<uint32_t*>(thread + 0x160) = error;', '/* error store lost */'),
  ('wrong TLS slot', 'sda + 0x100', 'sda + 0x104'),
  ('return input status', '    return error;', '    return static_cast<uint32_t>(status);'),
 ],
 'sys_thread_map_status_error_thunk': [
  ('omit error mapper', 'return sysThread_SetErrorFromStatus(status);', 'return 0;'),
  ('wrong thunk status', 'return sysThread_SetErrorFromStatus(status);', 'return sysThread_SetErrorFromStatus(status ^ 1);'),
 ],
 'sys_thread_wait_timeout': [
  ('make wait alertable', 'static_cast<uint32_t>(milliseconds), 0);', 'static_cast<uint32_t>(milliseconds), 1);'),
  ('drop forwarded timeout', 'handle, static_cast<uint32_t>(milliseconds), 0);', 'handle, 0, 0);'),
 ],
 'sys_thread_wait_timeout_ex': [
  ('wrong wait mode', 'handle, 1, alertable & 0xFFu, timeout', 'handle, 0, alertable & 0xFFu, timeout'),
  ('unmasked alert flag', 'handle, 1, alertable & 0xFFu, timeout', 'handle, 1, alertable, timeout'),
  ('retry low byte only', 'if (alertable == 0 || status != 0x101)', 'if ((alertable & 0xFFu) == 0 || status != 0x101)'),
  ('wrong retry status', 'if (alertable == 0 || status != 0x101)', 'if (alertable == 0 || status != 0x102)'),
  ('ignore failure mapping', '            sysThread_SetErrorFromStatus(status);', '            /* error mapping lost */'),
  ('return failure as success', '            return UINT32_MAX;', '            return 0;'),
 ],
 'sys_thread_release_semaphore': [
  ('omit release error mapping', '        sysThread_SetErrorFromStatusThunk(status);', '        /* error mapping lost */'),
  ('reject positive statuses', '    if (status < 0) {', '    if (status != 0) {'),
  ('wrong failure return', '        return 0;\n    }\n    return 1;', '        return 1;\n    }\n    return 1;'),
 ],
}


def main():
    source = (Path(__file__).resolve().parents[3] / 'src/xam/thread_sync.cpp').read_text()
    caught = 0
    for spec, cases in CASES.items():
        for name, old, new in cases:
            # Failure handling appears in both wait and release. Anchor the
            # release mutation at its function boundary to patch the right one.
            if name == 'reject positive statuses':
                old = 'int32_t status = NtReleaseSemaphore(handle, count, previousCount);\n    if (status < 0) {'
                new = 'int32_t status = NtReleaseSemaphore(handle, count, previousCount);\n    if (status != 0) {'
            assert source.count(old) == 1, (name, source.count(old))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                rc = Checker(Path(__file__).with_name(spec + '.py'),
                             Options(trials=256, seed=1, patches=((old, new),))).run()
            first = output.getvalue().splitlines()[0]
            detected = rc == 1 and first.startswith('FAIL ')
            print(f"{'CAUGHT' if detected else 'MISSED'} {spec}: {name}: {first}", flush=True)
            if not detected:
                print(output.getvalue())
                return 1
            caught += 1
    print(f'Caught {caught}/{sum(map(len, CASES.values()))} mutations')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
