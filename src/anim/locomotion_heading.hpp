#pragma once
#include <cstdint>

struct LocomotionHeadingVector { float x, y, z, w; };
struct LocomotionHeadingOps {
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
    virtual float GetAnimationDuration() = 0;
    virtual uint32_t GetBounds(LocomotionHeadingVector* lower, LocomotionHeadingVector* upper) = 0;
    virtual LocomotionHeadingVector GetPosition() = 0;
    virtual uint32_t IsForwardSide() = 0;
};

float LocomotionStateAnim_ClampHeading(void* state, float heading); // @ 0x820E6E90
float LocomotionStateAnim_6DD8_w(void* state, float maxWeight, float heading); // @ 0x820E6DD8
