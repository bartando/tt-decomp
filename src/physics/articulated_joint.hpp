#pragma once
#include <stdint.h>

namespace rage {
// Dispatch interface of joints stored at joint-data +0xA8. Keep Xbox method
// order; no C++ destructor slots are inserted into this borrowed interface.
struct phArticulatedJointOps {
    virtual void PropagateMotion() = 0; // +0x00
    virtual void ReservedSlot1() = 0;
    virtual void ReservedSlot2() = 0;
    virtual int32_t GetConstraintCount() = 0; // +0x0C
    virtual void GetConstraintState(int32_t index, uint32_t* state, float* value,
                                    float* weight, float* limit, float* reference) = 0; // +0x10
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
    virtual void ClearForceConstraints() = 0; // +0x40
    virtual void ClearVelocityConstraints() = 0; // +0x44
    virtual void ReservedSlot18() = 0;
    virtual void PrepareForwardSolve() = 0; // +0x4C
    virtual void PrepareBackwardSolve() = 0; // +0x50
    virtual void GetBackwardMatrix(float* output) = 0; // +0x54
    virtual void GetForwardMatrix(float* output) = 0; // +0x58
    virtual void ReservedSlot23() = 0;
    virtual void ReservedSlot24() = 0;
    virtual void ReservedSlot25() = 0;
    virtual void ReservedSlot26() = 0;
    virtual void ResolveParentResponse(const float* input, float* output) = 0; // +0x6C
    virtual void ResolveChildResponse(const float* input, float* output) = 0; // +0x70
};
}
