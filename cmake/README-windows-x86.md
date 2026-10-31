# 32-bit Windows with clang

The default build still selects the host compiler and installed SDL2/GLEW.
The `windows-x86-clang` preset selects the GNU Windows ABI, clang/lld, `-m32`,
32-bit SDL2 and a static GLEW built from source. Every game translation unit
checks `sizeof(void*) == 4` through `platform/layout.h`.

On the online Apple Silicon Mac:

```sh
brew install llvm mingw-w64 cmake ninja
cmake -P cmake/PrepareWin32Deps.cmake
cmake --preset windows-x86-clang
cmake --build --preset windows-x86-clang
```

The full game currently compiles but does **not** link: missing game lifts
also block the macOS build. Do not suppress unresolved symbols or add fake
implementations to produce an executable. lld's error limit is disabled so
one link attempt reports the entire missing-symbol inventory.

The platform test links independently of the incomplete game:

```sh
cmake --build --preset windows-x86-clang --target tt_platform_test
```

`build/windows-x86-clang/tt_platform_test.exe` is a PE32/i386 console executable.
Copy it to Windows and run it, or run `ctest --test-dir build/windows-x86-clang
--output-on-failure` after building there. It checks event reset modes,
previous event states, semaphore consumption/overflow, relative waits, thread
handles, TLS isolation/exhaustion, recursive lock contention, compact guest
lock storage, system time and spinlocks. Building it on macOS does not verify
Windows runtime behavior. The host counterpart can be run on macOS:

```sh
cmake -S . -B build/macos -G Ninja -DTT_BUILD_PLATFORM_TESTS=ON
cmake --build build/macos --target tt_platform_test
ctest --test-dir build/macos --output-on-failure
```

The macOS checks also run the platform layer's existing SDK synchronization,
TLS, IRQL, allocation and wait/error contract tests. Both checks passed after
merging `5faf20b`. All 256 game translation units compiled as COFF i386 with
the pointer-size guard. The full Windows link reported 706 distinct undefined
game symbols, compared with 707 on macOS. There were no Windows-only missing
symbols. The one macOS-only diagnostic was `typeinfo for pongTrainingDrill`:
`llvm-nm` confirms that the Windows drill object defines this RTTI record,
while the macOS drill object references it without defining it. This is a
compiler/RTTI emission difference, rather than a missing Windows platform API.
The inventories are snapshots; rerun the helper after merging further lifts.

## Offline/native Windows setup

Transfer `build/win32-deps/` along with the sources. A native Windows LLVM
installation (clang, clang++, lld), Ninja, CMake 3.21+, and an **i686 GNU
mingw-w64 toolchain/sysroot** must already be installed. The Mac's Homebrew
compiler executables cannot run on Windows. In PowerShell, point the same
preset at native installations:

```powershell
$env:TT_LLVM_ROOT = 'C:/tools/llvm'
$env:TT_MINGW_ROOT = 'C:/tools/mingw32'
cmake --preset windows-x86-clang
cmake --build --preset windows-x86-clang
```

Use a fresh build directory when changing hosts. Paths can also be supplied
as CMake cache variables `TT_LLVM_ROOT`, `TT_MINGW_ROOT`, `TT_WIN32_DEPS` and
`GLEW_ROOT`. The sysroot must supply 32-bit C/C++ headers, startup objects,
import libraries and libstdc++. This toolchain uses SJLJ C++ exceptions to
match Homebrew's i686 GCC runtime; use a matching SJLJ mingw distribution on
Windows. libstdc++, libgcc and their winpthread dependency are linked
statically; application synchronization itself uses Win32, with no pthread
backend on Windows. SDL2.dll remains a runtime dependency and is copied
beside the game automatically once its link succeeds.
The tested Homebrew sysroot uses the Windows Universal CRT; that runtime must
be present on the destination Windows installation. The test EXE imports only
Windows system/UCRT DLLs, with no libgcc, libstdc++ or winpthread DLL imports.

The Windows backend keeps SDK/stdcall imports in `src/platform/win32.c` and
guest/cdecl exports in `src/xam/kernel_win32.c`. NT event/wait/semaphore
functions preserve native statuses and 100ns relative/absolute timeouts.
Critical sections use native recursive locks keyed by guest addresses; native
lock storage never overwrites the compact locks embedded in lifted objects.

To capture and compare fresh linker inventories:

```sh
cmake --build --preset windows-x86-clang > /tmp/tt-win32-build.log 2>&1
cmake --build build/macos > /tmp/tt-macos-build.log 2>&1
python3 tools/compare-native-undefined.py /tmp/tt-win32-build.log /tmp/tt-macos-build.log
```

The helper writes distinct, sorted linker diagnostic spellings to
`/tmp/tt-win32-undefined.txt` and `/tmp/tt-macos-undefined.txt`. Both clang
toolchains use Itanium C++ mangling and a leading underscore for C symbols,
so the diagnostic names can be compared directly. It prints each target's
unique symbols; a successful link produces an empty list.
