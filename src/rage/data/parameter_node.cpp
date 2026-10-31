#include "rage/parameter_node.hpp"
#include "rage/ptr32.hpp"
#include "rage/operator_new.hpp"
#include <cstddef>
#include <cstring>

extern "C" void rage_free(void* pointer); // @ 0x820C00C0
extern "C" void* rage_strDuplicate(const char* text); // @ 0x820C29E0
extern "C" uint32_t rage_FindSingleton(void* pointer); // @ 0x820F90D0
extern "C" uint32_t* g_sda_base; // @ 0x82600000

namespace {
struct ParameterNode {
    rage::ptr32<const char> name;
    uint32_t value;
    uint8_t type;
    uint8_t flags;
    uint8_t reserved[2];
};
static_assert(sizeof(ParameterNode) == 12);
static_assert(offsetof(ParameterNode, flags) == 9);

struct PointerArray {
    rage::ptr32<rage::ptr32<void>> entries;
    uint16_t count;
    uint16_t capacity;
};
static_assert(sizeof(PointerArray) == 8);

// One retail destructor slot; a C++ destructor would add a second Itanium slot.
class ParameterAllocator {
public:
    virtual void Destroy() = 0;
    virtual void* Allocate(uint32_t bytes, uint32_t alignment) = 0;
    virtual void Free(void* pointer) = 0;
};

ParameterAllocator* currentAllocator() {
    void* thread = rage::load_ptr32<void>(g_sda_base, 0);
    return rage::load_ptr32<ParameterAllocator>(thread, 4);
}

void releaseText(ParameterNode* node) {
    if (node->type == 0 && (node->flags & 2))
        rage_free(rage::load_ptr32<void>(node, 4));
}

void storeText(ParameterNode* node, const char* text) {
    const rage::ptr32<const char> pointer(text);
    std::memcpy(&node->value, &pointer, sizeof(pointer));
}

ParameterNode* createNode(rage::ptr32<void>* slot) {
    auto* node = static_cast<ParameterNode*>(rage_Alloc(12));
    if (node) {
        node->name = nullptr;
        node->type = 0;
        node->flags = 0;
        node->value = 0;
    }
    *slot = node;
    return node;
}
} // namespace

// @ 0x8223A258 | size: 0x8C
void cmOperator_ClearName(void* raw) {
    auto* node = static_cast<ParameterNode*>(raw);
    if (node->flags & 1) rage_free(const_cast<char*>(node->name.get()));
    releaseText(node);
}

// @ 0x8223A2E8 | size: 0x88
void cmOperator_SetPrimaryName(void* raw, const char* name, int copy) {
    auto* node = static_cast<ParameterNode*>(raw);
    if (node->flags & 1) rage_free(const_cast<char*>(node->name.get()));
    if (static_cast<uint8_t>(copy)) {
        node->name = static_cast<char*>(rage_strDuplicate(name));
        node->flags |= 1;
    } else {
        node->name = name;
        node->flags &= uint8_t(~1u);
    }
}

// @ 0x8223A370 | size: 0xA0
void cmOperator_SetSecondaryName(void* raw, const char* text, uint32_t copy) {
    auto* node = static_cast<ParameterNode*>(raw);
    releaseText(node);
    if (static_cast<uint8_t>(copy)) {
        storeText(node, static_cast<const char*>(rage_strDuplicate(text)));
        node->flags |= 2;
    } else {
        storeText(node, text);
        node->flags &= uint8_t(~2u);
    }
    node->type = 0;
}

// @ 0x8223A410 | size: 0x78
void cmOperator_SetIntegerValue(void* raw, int32_t value) {
    auto* node = static_cast<ParameterNode*>(raw);
    releaseText(node);
    node->value = static_cast<uint32_t>(value);
    node->type = 1;
}

// @ 0x8223A488 | size: 0x78
void cmOperator_SetRealValue(void* raw, float value) {
    auto* node = static_cast<ParameterNode*>(raw);
    releaseText(node);
    std::memcpy(&node->value, &value, sizeof(value));
    node->type = 2;
}

// @ 0x8223A500 | size: 0x78
void cmOperator_SetBooleanValue(void* raw, uint32_t value) {
    auto* node = static_cast<ParameterNode*>(raw);
    releaseText(node);
    // stb writes only the first payload byte; the other three remain untouched.
    *reinterpret_cast<uint8_t*>(&node->value) = static_cast<uint8_t>(value);
    node->type = 3;
}

// @ 0x822665C0 | size: 0xD8
void* atFreeList_Alloc(void* raw, uint32_t /*unusedR4*/) {
    auto* array = static_cast<PointerArray*>(raw);
    if (array->count == array->capacity) {
        array->capacity = static_cast<uint16_t>(array->capacity + 16);
        auto* entries = static_cast<rage::ptr32<void>*>(rage_Alloc(uint32_t(array->capacity) * 4));
        for (uint16_t i = 0; i < array->count; ++i)
            entries[i] = array->entries.get()[i];
        auto* old = array->entries.get();
        if (old && (rage_FindSingleton(old) & 255) == 0)
            currentAllocator()->Free(old);
        array->entries = entries;
    }
    auto* slot = array->entries.get() + array->count;
    array->count = static_cast<uint16_t>(array->count + 1);
    return slot;
}

// @ 0x822395F0 | size: 0xA8
void cmOperator_SetInt(void* owner, const char* name, int value, uint32_t copyName) {
    auto* slot = static_cast<rage::ptr32<void>*>(atFreeList_Alloc(static_cast<uint8_t*>(owner) + 8, 16));
    auto* node = createNode(slot);
    cmOperator_SetPrimaryName(node, name, copyName);
    cmOperator_SetIntegerValue(slot->get(), value);
    static_cast<uint8_t*>(owner)[4] &= uint8_t(~2u);
}

// @ 0x82239698 | size: 0xB0
void cmOperator_SetFloat(void* owner, const char* name, uint32_t /*unusedR5*/, uint32_t copyName, float value) {
    auto* slot = static_cast<rage::ptr32<void>*>(atFreeList_Alloc(static_cast<uint8_t*>(owner) + 8, 16));
    auto* node = createNode(slot);
    cmOperator_SetPrimaryName(node, name, copyName);
    cmOperator_SetRealValue(slot->get(), value);
    static_cast<uint8_t*>(owner)[4] &= uint8_t(~2u);
}
