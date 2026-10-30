#include <stdint.h>

#include "crt/rtti.h"

// Only pointer identity and the inline decorated name participate in this lift.
RTTITypeDescriptor g_typeDescriptor_hsmEvent = {nullptr, nullptr, ".?AVhsmEvent@rage@@"}; // @ 0x825E5448
RTTITypeDescriptor g_typeDescriptor_EvtMigrateSession = {nullptr, nullptr, ".?AUEvtMigrateSession@rage@@"}; // @ 0x825E43F0
RTTITypeDescriptor g_typeDescriptor_EvtChangePresence = {nullptr, nullptr, ".?AUEvtChangePresence@rage@@"}; // @ 0x825E5188
RTTITypeDescriptor g_typeDescriptor_snGamer = {nullptr, nullptr, ".?AVsnGamer@rage@@"}; // @ 0x825DEEB0
RTTITypeDescriptor g_typeDescriptor_Gamer = {nullptr, nullptr, ".?AVGamer@@"}; // @ 0x825DEECC

struct RTTIBaseClassDescriptor {
    RTTITypeDescriptor* type;
    uint32_t containedBases;
    int32_t memberDisplacement;
    int32_t vbtableDisplacement;
    int32_t displacementInsideVbtable;
    uint32_t attributes;
};

struct RTTIClassHierarchyDescriptor {
    uint32_t signature;
    uint32_t attributes;
    uint32_t baseCount;
    RTTIBaseClassDescriptor** bases;
};

struct RTTICompleteObjectLocator {
    uint32_t signature;
    uint32_t offset;
    uint32_t constructorDisplacementOffset;
    RTTITypeDescriptor* type;
    RTTIClassHierarchyDescriptor* hierarchy;
};

extern "C" RTTIBaseClassDescriptor* RTTIFindMITargetTypeInstance(
    void*, RTTICompleteObjectLocator*, RTTITypeDescriptor*, int32_t,
    RTTITypeDescriptor*); // @ 0x824305D0
extern "C" RTTIBaseClassDescriptor* RTTIFindVITargetTypeInstance(
    void*, RTTICompleteObjectLocator*, RTTITypeDescriptor*, int32_t,
    RTTITypeDescriptor*); // @ 0x82430768
extern "C" void* crtBadCastConstruct(void*, const char*); // @ 0x82430418
// This never returns in the real runtime. Its return is preserved for the checker
// when the exception machinery is stubbed, just as the original preserves r3.
extern "C" void* crtCxxThrowException(void*, const void*); // @ 0x82435A00

static bool SameType(RTTITypeDescriptor* a, RTTITypeDescriptor* b)
{
    if (a == b) return true;
    const char* left = a->name;
    const char* right = b->name;
    while (*left && *left == *right) {
        ++left;
        ++right;
    }
    return *left == *right;
}

// MSVC __RTDynamicCast; previously misidentified as SinglesNetworkClient_0978_g
// and lifted as the nullptr-only rlEvent_Init stub in pong_network_io.cpp.
// @ 0x82430978 | size: 0x1CC
extern "C" void* RTDynamicCast(void* object, int32_t vfDelta, RTTITypeDescriptor* sourceType,
                                RTTITypeDescriptor* targetType, int32_t isReference)
{
    if (!object) return nullptr;

    auto* input = static_cast<uint8_t*>(object);
    auto* locator = reinterpret_cast<RTTICompleteObjectLocator**>(
        *static_cast<void***>(object))[-1];
    uint8_t* complete = input - locator->offset;
    if (locator->constructorDisplacementOffset != 0) {
        complete += *reinterpret_cast<int32_t*>(input - locator->constructorDisplacementOffset);
    }

    RTTIBaseClassDescriptor* target = nullptr;
    auto* hierarchy = locator->hierarchy;
    if ((hierarchy->attributes & 1u) == 0) {
        for (uint32_t i = 0; i < hierarchy->baseCount; ++i) {
            auto* candidate = hierarchy->bases[i];
            if (SameType(candidate->type, targetType) && (candidate->attributes & 1u) == 0) {
                target = candidate;
                break;
            }
        }
    } else {
        int32_t sourceOffset = static_cast<int32_t>(input - vfDelta - complete);
        if ((hierarchy->attributes & 2u) == 0) {
            target = RTTIFindMITargetTypeInstance(complete, locator, sourceType, sourceOffset, targetType);
        } else {
            target = RTTIFindVITargetTypeInstance(complete, locator, sourceType, sourceOffset, targetType);
        }
    }

    if (target) {
        int32_t virtualOffset = 0;
        if (target->vbtableDisplacement >= 0) {
            auto* vbtable = *reinterpret_cast<uint8_t**>(complete + target->vbtableDisplacement);
            virtualOffset = target->vbtableDisplacement +
                *reinterpret_cast<int32_t*>(vbtable + target->displacementInsideVbtable);
        }
        return complete + virtualOffset + target->memberDisplacement;
    }
    if (isReference != 0) {
        uint8_t exception[16];
        crtBadCastConstruct(exception, reinterpret_cast<const char*>(0x820014F8u));
        return crtCxxThrowException(exception, reinterpret_cast<const void*>(0x8209AEA8u));
    }
    return nullptr;
}
