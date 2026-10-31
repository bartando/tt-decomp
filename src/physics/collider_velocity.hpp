#pragma once
#include <cstdint>

// Borrowed retail virtual interface. No native pointers are stored in layouts.
struct phColliderMotionOps {
    virtual void ReservedSlot0() = 0;
    virtual void ReservedSlot1() = 0;
    virtual void ClearForces() = 0;
    virtual void ReservedSlot3() = 0;
    virtual void ReservedSlot4() = 0;
    virtual void ReservedSlot5() = 0;
    virtual void ReservedSlot6() = 0;
    virtual void SynchronizeTransform() = 0;
    virtual void ReservedSlot8() = 0;
    virtual void ReservedSlot9() = 0;
    virtual void IntegrateCorrections() = 0;
    virtual void ReservedSlot11() = 0;
    virtual void ReservedSlot12() = 0;
    virtual void GetInertia(float* output, int bone) = 0;
    virtual void ReservedSlot14() = 0;
    virtual void ReservedSlot15() = 0;
    virtual void ReservedSlot16() = 0;
    virtual void ReservedSlot17() = 0;
    virtual void ReservedSlot18() = 0;
    virtual void ReservedSlot19() = 0;
    virtual void ReservedSlot20() = 0;
    virtual void ReservedSlot21() = 0;
    virtual void ReservedSlot22() = 0;
    virtual void ReservedSlot23() = 0;
    virtual void ReservedSlot24() = 0;
    virtual void ReservedSlot25() = 0;
    virtual void ReservedSlot26() = 0;
    virtual void ReservedSlot27() = 0;
    virtual void ReservedSlot28() = 0;
    virtual void ReservedSlot29() = 0;
    virtual void ReservedSlot30() = 0;
    virtual void ReservedSlot31() = 0;
    virtual void ReservedSlot32() = 0;
    virtual void ReservedSlot33() = 0;
    virtual void ReservedSlot34() = 0;
    virtual void ReservedSlot35() = 0;
    virtual void ReservedSlot36() = 0;
    virtual void ReservedSlot37() = 0;
    virtual void ReservedSlot38() = 0;
    virtual void ReservedSlot39() = 0;
    virtual void ReservedSlot40() = 0;
    virtual void ReservedSlot41() = 0;
    virtual void ReservedSlot42() = 0;
    virtual void ReservedSlot43() = 0;
    virtual void ReservedSlot44() = 0;
    virtual void ReservedSlot45() = 0;
    virtual void ReservedSlot46() = 0;
    virtual void ReservedSlot47() = 0;
    virtual void ReservedSlot48() = 0;
    virtual void ReservedSlot49() = 0;
    virtual void ReservedSlot50() = 0;
    virtual void ReservedSlot51() = 0;
    virtual void ReservedSlot52() = 0;
    virtual void ReservedSlot53() = 0;
    virtual void ReservedSlot54() = 0;
    virtual void ReservedSlot55() = 0;
    virtual void ReservedSlot56() = 0;
    virtual void ReservedSlot57() = 0;
    virtual void ReservedSlot58() = 0;
    virtual void ReservedSlot59() = 0;
    virtual void ReservedSlot60() = 0;
    virtual void ReservedSlot61() = 0;
    virtual void ReservedSlot62() = 0;
    virtual void ReservedSlot63() = 0;
    virtual void ReservedSlot64() = 0;
    virtual void ReservedSlot65() = 0;
    virtual void ReservedSlot66() = 0;
    virtual void OnLinearVelocityChanged() = 0;
    virtual void OnAngularVelocityChanged() = 0;
};

void phCollider_Reset(void* collider); // @ 0x822CABE0
void phCollider_SetAngularVelocity(void* collider, const float* velocity); // @ 0x822CCD28
void phCollider_RefreshLinearVelocity(void* collider); // @ 0x822CCDF0
void phCollider_RefreshAngularVelocity(void* collider); // @ 0x822CCE58
void phCollider_ClampLinearSpeed(void* collider); // @ 0x822CAE18
void phCollider_ClampAngularSpeed(void* collider); // @ 0x822CAEA8
void phCollider_PublishTransform(void* collider); // @ 0x822CB680

struct phInstMotionOps {
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
    virtual void ReservedSlot16() = 0;
    virtual void ReservedSlot17() = 0;
    virtual void ReservedSlot18() = 0;
    virtual void ReservedSlot19() = 0;
    virtual void ReservedSlot20() = 0;
    virtual void ReservedSlot21() = 0;
    virtual void ReservedSlot22() = 0;
    virtual void ReservedSlot23() = 0;
    virtual void ReservedSlot24() = 0;
    virtual void ReservedSlot25() = 0;
    virtual void ReservedSlot26() = 0;
    virtual void ReservedSlot27() = 0;
    virtual void SynchronizeBounds() = 0;
};

void phVector_AccumulateProjected(float* current, const float* delta); // @ 0x8223ACB0
