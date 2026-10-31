#pragma once

// Shared channel interface recovered from the getters/setters around C358/C418.
// No C++ destructor: the deleting entry occupies a single slot in this ABI.
struct AnimationChannel {
    virtual void slot0() = 0;
    virtual void slot1() = 0;
    virtual void slot2() = 0;
    virtual void slot3() = 0;
    virtual void slot4() = 0;
    virtual void slot5() = 0;
    virtual void slot6() = 0;
    virtual void slot7() = 0;
    virtual void slot8() = 0;
    virtual void slot9() = 0;
    virtual void slot10() = 0;
    virtual void slot11() = 0;
    virtual void slot12() = 0;
    virtual void slot13() = 0;
    virtual const float* GetTranslation() = 0; // slot 14
    virtual const float* GetQuaternion() = 0;  // slot 15
    virtual void slot16() = 0;
    virtual void SetVector(const float* value) = 0;     // slot 17
    virtual void SetQuaternion(const float* value) = 0; // slot 18
};
