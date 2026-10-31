# Game-memory pointers

New and edited lifts must preserve the Xbox 360's four-byte pointer fields.
Include `rage/ptr32.hpp` and use `rage::ptr32<T>` for every pointer stored in a
game-memory layout (including pointer arrays). Use `.get()` / `.set()` or the
pointer operators at the boundary to native C++ code:

```cpp
struct BodyLink {
    rage::ptr32<Body> body; // four bytes on PPC32, i686, and 64-bit hosts
};
Body* body = link.body.get();
link.body = otherBody;
```

For a raw byte-offset field, use
`rage::load_ptr32<Body>(base, 0x28 + index * 4)`. Offsets are **bytes**; native
pointer parameters and local variables are fine. Do not load game pointers with
`uintptr_t(uint32)` casts, cast pointers down to `uint32_t` on stores, or put
native `void*` (or other native pointer) fields in game layout structs. Do not
reinterpret a four-byte pointer array as `T**` on a 64-bit host.

On 32-bit builds, `ptr32<T>` stores a native pointer with no address translation.
On 64-bit builds, startup must reserve the arena and call
`rage::set_ptr32_arena_base(base)` once before accessing game pointers. All game
objects and stored pointer targets must live in that same 4 GiB arena; offset
zero is reserved for null and cannot hold an object. The base must remain stable
while any game memory is live. Invalid stores or non-null loads before arena
setup trap, including in release builds. This type does not allocate an arena,
relocate an original image, swap endianness, or translate executable addresses.

Run `python3 tools/check_ptr32.py origin/main..HEAD` before submitting lifts.
With no range, it checks tracked staged and unstaged changes against `HEAD`.
The cheap checker catches added pointer/integer conversions and native `void*`
members, including multiline declarations; it is not a complete C++ parser.
For an intentional host address conversion or host-only member, annotate the
statement with `// ptr32-check: host` and explain why it is host-only. Do not use
that annotation to bypass game layout rules.

Check the pointer API and diff guard with
`python3 -m unittest discover -s tools/tests -v`.

Run affected lift-check specs with both `--seed 1` and `--seed 2`. Create its
real environment with `cd tools/lift-check && uv venv --python 3.13 .venv &&
uv pip install --python .venv/bin/python unicorn`; never symlink a venv. Stage
only intended files explicitly; never use `git add -A`.
