#include "bound_lookup.hpp"
#include "crt/rtti.h"
#include <string.h>

extern RTTITypeDescriptor g_typeDescriptor_phBound; // @ 0x825D2C78
extern RTTITypeDescriptor g_typeDescriptor_phBoundComposite; // @ 0x825D2C94

namespace {
// The serialized physics layouts store 32-bit pointers even in the native port.
void* boundPointerAt(const void* object, unsigned offset) {
    uint32_t pointer;
    memcpy(&pointer, static_cast<const char*>(object) + offset, sizeof(pointer));
    return reinterpret_cast<void*>(uintptr_t(pointer));
}

uint16_t compositeChildCount(const void* bound) {
    uint16_t count;
    memcpy(&count, static_cast<const char*>(bound) + 0x82, sizeof(count));
    return count;
}

bool isComposite(const void* bound) {
    return bound && static_cast<const uint8_t*>(bound)[4] == 9;
}
}

namespace rage {
// Includes direct children (also null entries) and every nested composite's
// descendants. The iteration count is reloaded after recursion, as in the PPC.
// phBoundComposite_E750 @ 0x8228E750 | size: 0x68
uint32_t phBoundComposite_E750(void* bound) {
    uint32_t count = compositeChildCount(bound);
    for (unsigned i = 0; i < compositeChildCount(bound); ++i) {
        const void* children = boundPointerAt(bound, 0x70);
        void* child = boundPointerAt(children, i * 4);
        if (isComposite(child))
            count += phBoundComposite_E750(child);
    }
    return count;
}

// Flattened indices first enumerate this composite's direct children, followed
// by each nested subtree. Resolve a descendant back to its immediate child.
// The map calls this pongCreatureInst_F5C8; its actual receiver is a composite.
// phBoundComposite_ResolveBoundIndex @ 0x8228F5C8 | size: 0xA0
int32_t phBoundComposite_ResolveBoundIndex(void* bound, int32_t index) {
    const int32_t count = compositeChildCount(bound);
    if (index < count)
        return index;
    uint32_t remaining = static_cast<uint32_t>(index) - static_cast<uint32_t>(count);
    const void* children = count > 0 ? boundPointerAt(bound, 0x70) : nullptr;
    for (int32_t i = 0; i < count; ++i) {
        void* child = boundPointerAt(children, static_cast<unsigned>(i) * 4);
        if (isComposite(child)) {
            const uint32_t descendants = phBoundComposite_E750(child);
            if (static_cast<int32_t>(remaining) < static_cast<int32_t>(descendants))
                return i;
            remaining -= descendants;
        }
    }
    return 0;
}
}

// Resolve a flattened bound index, then map the direct child to its joint body.
// phArticulatedCollider_E668 @ 0x8224E668 | size: 0x70
int phArticulatedCollider_E668(rage::phArticulatedCollider* collider, int boneIndex) {
    void* instance = boundPointerAt(collider, 0x10);
    void* archetype = boundPointerAt(instance, 4);
    void* bound = boundPointerAt(archetype, 0xC);
    void* composite = RTDynamicCast(bound, 0, &g_typeDescriptor_phBound,
                                   &g_typeDescriptor_phBoundComposite, 0);
    const int32_t child = rage::phBoundComposite_ResolveBoundIndex(composite, boneIndex);
    int32_t bodyIndex;
    memcpy(&bodyIndex, reinterpret_cast<const char*>(collider) + 0x204 + child * 4,
           sizeof(bodyIndex));
    return bodyIndex;
}
