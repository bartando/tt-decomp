#pragma once

namespace rage {
// Dispatch interface of joints stored at joint-data +0xA8. Keep Xbox method
// order; no C++ destructor slots are inserted into this borrowed interface.
struct phArticulatedJointOps {
    virtual void PropagateMotion() = 0; // +0x00
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
    virtual void ClearForceConstraints() = 0; // +0x40
    virtual void ClearVelocityConstraints() = 0; // +0x44
};
}
