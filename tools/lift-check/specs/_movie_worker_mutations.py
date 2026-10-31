import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options

CASES = [
    ("movie_ring_commit_write", "wrong wrap", "ring->writeIndex = next >=", "ring->writeIndex = next >"),
    ("movie_ring_commit_write", "wrong counter direction", "__atomic_fetch_sub(&ring->freeSlots, 1u", "__atomic_fetch_add(&ring->freeSlots, 1u"),
    ("movie_ring_commit_write", "wrong index", "ring->writeIndex =", "ring->readIndex ="),
    ("movie_ring_release_read", "wrong wrap", "ring->readIndex = next >=", "ring->readIndex = next >"),
    ("movie_ring_release_read", "wrong counter direction", "__atomic_fetch_add(&ring->freeSlots, 1u", "__atomic_fetch_sub(&ring->freeSlots, 1u"),
    ("movie_ring_release_read", "wrong index", "ring->readIndex =", "ring->writeIndex ="),
    ("movie_store_thread_id", "lose existing-owner query", "if (*threadId != 0) xe_GetCurrentThreadId();", "/* lost query */"),
    ("movie_store_thread_id", "wrong owner offset", "+ 0x2888", "+ 0x2884"),
    ("movie_worker_fill_a", "wrong virtual", "->MediaControl_Pause();", "->MediaControl_Stop();"),
    ("movie_worker_fill_b", "wrong virtual", "->MediaControl_Stop();", "->MediaControl_Pause();"),
    ("movie_worker_write_a", "wrong virtual", "->MediaControl_GetState();", "->MediaControl_StopWhenReady();"),
    ("movie_worker_write_b", "wrong virtual", "->MediaControl_StopWhenReady();", "->MediaControl_GetState();"),
    ("movie_worker_fill_a", "wrong result", "return 0;", "return 1;"),
]

def main():
    for spec, label, old, new in CASES:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = Checker(Path(__file__).with_name(spec + ".py"),
                         Options(seed=1, patches=((old, new),))).run()
        first = output.getvalue().splitlines()[0]
        ok = rc == 1 and first.startswith("FAIL ")
        print(f"{'CAUGHT' if ok else 'MISSED'} {spec}: {label}: {first}", flush=True)
        if not ok:
            print(output.getvalue())
            return 1
    print(f"Caught {len(CASES)}/{len(CASES)} mutations")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
