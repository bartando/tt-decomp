#pragma once
#include <stdint.h>

struct RTTITypeDescriptor {
    void* vtable;
    void* spare;
    char name[64];
};

extern RTTITypeDescriptor g_typeDescriptor_hsmEvent;             // @ 0x825E5448
extern RTTITypeDescriptor g_typeDescriptor_EvtMigrateSession;    // @ 0x825E43F0
extern RTTITypeDescriptor g_typeDescriptor_EvtChangePresence;    // @ 0x825E5188
extern RTTITypeDescriptor g_typeDescriptor_snGamer;              // @ 0x825DEEB0
extern RTTITypeDescriptor g_typeDescriptor_Gamer;                // @ 0x825DEECC

// MSVC RTTI dynamic cast. vfDelta locates the source subobject relative to its vfptr.
extern "C" void* RTDynamicCast(void* object, int32_t vfDelta, RTTITypeDescriptor* sourceType,
                                RTTITypeDescriptor* targetType, int32_t isReference); // @ 0x82430978
