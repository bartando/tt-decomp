#pragma once
#include <cstdint>
#include <cstddef>

// Compact construction view shared by mover sampling helpers. Dispatch stays
// in the existing DOF/channel operations; values retain 16-byte alignment.
struct alignas(16) MoverDofStorage {
    const void* vtable;
    uint8_t flags;
    uint8_t type;
    uint16_t id;
    uint8_t reserved[12 - sizeof(void*)];
    float value[4];
};
static_assert(offsetof(MoverDofStorage, value) == 0x10, "mover DOF value offset");
static_assert(sizeof(MoverDofStorage) == 0x20, "mover DOF size");
#if UINTPTR_MAX == 0xFFFFFFFFu
static_assert(offsetof(MoverDofStorage, flags) == 4, "mover DOF flags offset");
static_assert(offsetof(MoverDofStorage, type) == 5, "mover DOF type offset");
static_assert(offsetof(MoverDofStorage, id) == 6, "mover DOF id offset");
#endif
