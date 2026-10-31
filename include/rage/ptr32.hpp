#pragma once

#include <cstddef>
#include <cstdint>

namespace rage {

#if __SIZEOF_POINTER__ == 8
// Set once, before accessing game memory. Reserve offset zero for nullptr;
// every non-null game pointer must lie in (base, base + 0xffffffff].
inline void* g_ptr32ArenaBase = nullptr;

inline void set_ptr32_arena_base(void* base) noexcept {
    g_ptr32ArenaBase = base;
}
#endif

// A pointer stored in a game layout, not a host pointer or an endian wrapper.
// PPC32/i686 store a native pointer; 64-bit hosts store an arena-relative offset.
template <typename T>
class ptr32 {
public:
    ptr32() noexcept = default;
    ptr32(T* pointer) noexcept { set(pointer); }

    T* get() const noexcept {
#if __SIZEOF_POINTER__ == 4
        return value_;
#else
        if (value_ == 0)
            return nullptr;
        if (!g_ptr32ArenaBase)
            __builtin_trap();
        return reinterpret_cast<T*>(reinterpret_cast<uintptr_t>(g_ptr32ArenaBase) + value_);
#endif
    }

    void set(T* pointer) noexcept {
#if __SIZEOF_POINTER__ == 4
        value_ = pointer;
#else
        if (!pointer) {
            value_ = 0;
            return;
        }
        const uintptr_t base = reinterpret_cast<uintptr_t>(g_ptr32ArenaBase);
        const uintptr_t address = reinterpret_cast<uintptr_t>(pointer);
        // Never silently truncate an out-of-arena host pointer, even in release.
        if (!base || address <= base || address - base > 0xffffffffu)
            __builtin_trap();
        value_ = static_cast<uint32_t>(address - base);
#endif
    }

    ptr32& operator=(T* pointer) noexcept { set(pointer); return *this; }
    T* operator->() const noexcept { return get(); }
    template <typename U = T>
    U& operator*() const noexcept { return *get(); }
    explicit operator bool() const noexcept { return get() != nullptr; }

    friend bool operator==(ptr32 a, ptr32 b) noexcept { return a.value_ == b.value_; }
    friend bool operator!=(ptr32 a, ptr32 b) noexcept { return !(a == b); }
    friend bool operator==(ptr32 a, T* b) noexcept { return a.get() == b; }
    friend bool operator!=(ptr32 a, T* b) noexcept { return !(a == b); }
    friend bool operator==(T* a, ptr32 b) noexcept { return a == b.get(); }
    friend bool operator!=(T* a, ptr32 b) noexcept { return !(a == b); }

private:
#if __SIZEOF_POINTER__ == 4
    T* value_ = nullptr;
#elif __SIZEOF_POINTER__ == 8
    uint32_t value_ = 0;
#else
#error "ptr32 requires a 32-bit or 64-bit target"
#endif
};

static_assert(sizeof(ptr32<void>) == 4, "game pointer fields must occupy four bytes");
static_assert(sizeof(ptr32<const int>) == 4, "typed game pointer fields must occupy four bytes");

// Load a four-byte pointer field at a byte offset, including unaligned fields.
// memcpy avoids aliasing a uint32_t array as a ptr32<T> object.
template <typename T>
inline T* load_ptr32(const void* base, size_t offset) noexcept {
    static_assert(sizeof(ptr32<T>) == 4, "game pointer fields must occupy four bytes");
    ptr32<T> pointer;
    __builtin_memcpy(&pointer, static_cast<const unsigned char*>(base) + offset, sizeof(pointer));
    return pointer.get();
}

} // namespace rage
