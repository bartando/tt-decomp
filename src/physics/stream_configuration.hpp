#pragma once
#include <cstdint>
#include "rage/ptr32.hpp"

struct phStreamConfigurationOps {
    virtual void ReservedSlot0() = 0;
    virtual void ReservedSlot1() = 0;
    virtual void ReservedSlot2() = 0;
    virtual void ReservedSlot3() = 0;
    virtual void ReservedSlot4() = 0;
    virtual void ReservedSlot5() = 0;
    virtual void ReservedSlot6() = 0;
    virtual void ReservedSlot7() = 0;
    virtual void ReservedSlot8() = 0;
    virtual void ReservedSlot9() = 0;
    virtual void ReservedSlot10() = 0;
    virtual void ReservedSlot11() = 0;
    virtual void ReservedSlot12() = 0;
    virtual void ReservedSlot13() = 0;
    virtual void ReservedSlot14() = 0;
    virtual void ReservedSlot15() = 0;
    virtual int32_t SetInterval(float interval) = 0;
    virtual void ReservedSlot17() = 0;
    virtual int32_t GetRecord(rage::ptr32<uint8_t>* output) = 0;
};

int32_t phStream_Configure(void* stream, const uint32_t* configuration, uint32_t mode); // @ 0x824662F8
int32_t phStream_ConfigurePrimary(void* owner, const uint32_t* configuration, uint32_t mode); // @ 0x82466A50

int32_t phStream_GetRecordField(void* owner, uint32_t* output); // @ 0x824668D8
int32_t phStream_ConfigurePacked(void* owner, const uint32_t* configuration, uint32_t mode); // @ 0x82468AA0
