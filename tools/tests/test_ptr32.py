"""Run from the checkout: python3 -m unittest discover -s tools/tests -v."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_ptr32", ROOT / "tools/check_ptr32.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CheckerTest(unittest.TestCase):
    def check(self, source, lines=None):
        return checker.violations(source, set(lines or range(1, len(source.splitlines()) + 1)))

    def test_multiline_and_direct_loads(self):
        for source in [
            "auto p = reinterpret_cast<Body*>(\n uintptr_t(\n data[4]));",
            "auto p = (void*)(uintptr_t)word;",
            "auto p = (void*)*(uint32_t*)(base + 8);",
            "auto p = reinterpret_cast<void*>(*reinterpret_cast<const uint32_t*>(base + 8));",
            "word = (uint32_t)(uintptr_t)p;",
        ]:
            with self.subTest(source=source):
                self.assertTrue(self.check(source))

    def test_members_not_locals_or_methods(self):
        self.assertTrue(self.check("struct A {\n void\n *field;\n};"))
        self.assertTrue(self.check("class A { public: void *items[2]; };"))
        self.assertFalse(self.check("void* local;\nvoid f(void* p);"))
        self.assertFalse(self.check("struct A { void* f(); void f(void* p) { void* local; } };"))
        self.assertFalse(self.check("struct A { rage::ptr32<void> field; };"))

    def test_only_added_statements_and_host_exemption(self):
        source = "auto old = (void*)(uintptr_t)word;\nint added = 2;\n"
        self.assertFalse(self.check(source, {2}))
        self.assertTrue(self.check(source, {1}))
        self.assertFalse(self.check("struct A { void* host; // ptr32-check: host (native API)\n};"))
        self.assertFalse(self.check('// uintptr_t(word)\nconst char* s = "uintptr_t(word)";'))

    def test_git_range_reads_committed_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def git(*args):
                subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

            git("init", "-q")
            git("config", "user.name", "Pointer test")
            git("config", "user.email", "test@example.invalid")
            (root / "src").mkdir()
            file = root / "src/layout.hpp"
            file.write_text("struct Layout {};\n")
            git("add", "src/layout.hpp")
            git("commit", "-qm", "base")
            file.write_text("struct Layout {\n void* body;\n};\n")
            git("add", "src/layout.hpp")
            git("commit", "-qm", "bad pointer")
            file.write_text("struct Layout {};\n") # range must ignore working copy
            result = subprocess.run(
                ["python3", str(ROOT / "tools/check_ptr32.py"), "HEAD~1..HEAD"],
                cwd=root, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("src/layout.hpp:2: native void* member", result.stdout)


class PointerTest(unittest.TestCase):
    def test_native_api_and_release_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = str(Path(directory) / "ptr32-test")
            subprocess.run([shutil.which("clang++") or "c++", "-std=c++17", "-O2", "-DNDEBUG",
                            "-Wall", "-Wextra", "-Werror", "-I", str(ROOT / "include"),
                            str(ROOT / "tools/tests/ptr32.cpp"), "-o", binary], check=True)
            subprocess.run([binary], check=True)
            for mode in ("unset", "load", "zero", "below", "overflow"):
                with self.subTest(mode=mode):
                    result = subprocess.run([binary, mode], capture_output=True)
                    self.assertLess(result.returncode, 0, "invalid pointer must trap")

    def test_32_bit_native_storage(self):
        source = '''#include "rage/ptr32.hpp"
struct Item { int value; };
static_assert(sizeof(rage::ptr32<Item>) == 4);
extern "C" Item* read(const rage::ptr32<Item>* p) { return p->get(); }
extern "C" void write(rage::ptr32<Item>* p, Item* x) { p->set(x); }
extern "C" Item* raw(const void* p) { return rage::load_ptr32<Item>(p, 4); }
'''
        compiler = shutil.which("clang++")
        if not compiler:
            self.skipTest("clang++ is needed for PPC32/i686 cross-compilation")
        for target in ("powerpc-unknown-elf", "i686-unknown-linux-gnu"):
            with self.subTest(target=target):
                result = subprocess.run(
                    [compiler, f"--target={target}", "-std=c++17", "-O2", "-ffreestanding",
                     "-nostdinc++", "-nostdlibinc", "-isystem", str(ROOT / "tools/lift-check/shim"),
                     "-I", str(ROOT / "include"), "-x", "c++", "-S", "-emit-llvm", "-o", "-", "-"],
                    input=source, text=True, capture_output=True, check=True,
                )
                self.assertNotIn("g_ptr32ArenaBase", result.stdout)
                self.assertNotIn("ptrtoint", result.stdout)
                self.assertNotIn("inttoptr", result.stdout.split("@raw(", 1)[0])
                self.assertNotIn("call ", result.stdout)
                self.assertNotIn("invoke ", result.stdout)


if __name__ == "__main__":
    unittest.main()
