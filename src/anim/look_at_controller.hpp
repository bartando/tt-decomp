#pragma once
#include <cstdint>

struct pongLookAtController;

// Borrowed retail dispatch interface. No destructor slots are inserted.
struct pongLookAtTargetOps {
    virtual void ReservedSlot0() = 0;
    virtual void ReservedSlot1() = 0;
    virtual void ReservedSlot2() = 0;
    virtual void SaveTarget(const float* target) = 0; // +0x0c
    virtual void SetTarget(const float* target, int which) = 0; // +0x10
    virtual void ReservedSlot5() = 0;
    virtual void ReservedSlot6() = 0;
    virtual void ReservedSlot7() = 0;
    virtual uint32_t IsEnabled() = 0; // +0x20
};

void game_28F0(pongLookAtController* controller, const float* target, int which); // @ 0x820D28F0
void game_2A40(pongLookAtController* controller); // @ 0x820D2A40
