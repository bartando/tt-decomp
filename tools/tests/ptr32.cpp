// Native host test; tools/tests/test_ptr32.py also checks the two 32-bit ABIs.
#include "rage/ptr32.hpp"
#include <type_traits>
#include <new>
#include <cstring>

struct Item { int value; };
struct Layout { unsigned tag; rage::ptr32<Item> item; unsigned tail; };
static_assert(sizeof(rage::ptr32<Item>) == 4);
static_assert(alignof(rage::ptr32<Item>) == 4);
static_assert(sizeof(Layout) == 12);
static_assert(offsetof(Layout, tail) == 8);
static_assert(std::is_trivially_copyable<rage::ptr32<Item>>::value);
static_assert(std::is_standard_layout<rage::ptr32<Item>>::value);

#define CHECK(expression) do { if (!(expression)) return __LINE__; } while (false)

int main(int argc, char** argv) {
    alignas(16) unsigned char arena[128] = {};
    Item* item = new (arena + 16) Item{42};
    rage::ptr32<Item> pointer;
    CHECK(!pointer && pointer == nullptr && nullptr == pointer);
    CHECK(rage::ptr32<void>() == nullptr);
    uint32_t bits = 0;
    memcpy(&bits, &pointer, 4);
    CHECK(bits == 0);

#if __SIZEOF_POINTER__ == 8
    // Invalid cases are launched separately; all must trap even with NDEBUG.
    if (argc > 1 && argv[1][0] == 'u') {
        pointer.set(item); // unset arena
        return 0;
    }
    if (argc > 1 && argv[1][0] == 'l') {
        bits = 16;
        memcpy(&pointer, &bits, 4);
        return pointer.get() != nullptr ? 0 : 1; // non-null load before setup
    }
    rage::set_ptr32_arena_base(arena);
    if (argc > 1) {
        uintptr_t base = reinterpret_cast<uintptr_t>(arena);
        if (argv[1][0] == 'z') pointer.set(reinterpret_cast<Item*>(base));
        if (argv[1][0] == 'b') pointer.set(reinterpret_cast<Item*>(base - 1));
        if (argv[1][0] == 'o') pointer.set(reinterpret_cast<Item*>(base + 0x100000000ULL));
        return 0;
    }
    rage::ptr32<void> last(reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(arena) + 0xffffffffu));
    memcpy(&bits, &last, 4);
    CHECK(bits == 0xffffffffu);
    CHECK(last.get() == reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(arena) + 0xffffffffu));
#endif

    pointer.set(item);
    CHECK(pointer.get() == item && pointer->value == 42 && (*pointer).value == 42);
    CHECK(pointer && pointer != nullptr && nullptr != pointer);
    CHECK(pointer == item && item == pointer);
    rage::ptr32<Item> copy = pointer;
    CHECK(copy == pointer && !(copy != pointer));
    rage::ptr32<const Item> constant(item);
    CHECK(constant->value == 42);
    rage::ptr32<void> untyped(item);
    CHECK(untyped.get() == item);
    memcpy(&bits, &pointer, 4);
#if __SIZEOF_POINTER__ == 8
    CHECK(bits == 16);
#else
    CHECK(bits == reinterpret_cast<uintptr_t>(item));
#endif
    unsigned char raw[9];
    memset(raw, 0xff, sizeof(raw));
    memcpy(raw + 1, &pointer, 4);
    CHECK(rage::load_ptr32<Item>(raw, 1) == item);
    memset(raw + 1, 0, 4);
    CHECK(rage::load_ptr32<Item>(raw, 1) == nullptr);
    CHECK(raw[0] == 0xff && raw[5] == 0xff); // exactly four bytes
    pointer = nullptr;
    CHECK(!pointer && pointer != copy && pointer != item && item != pointer);
    pointer = item;
    (*pointer).value = 17;
    CHECK(item->value == 17);
}
