#include "pong_gameplay_queries.hpp"

void SinglesNetworkClient_51C8_g(void* shot); // @ 0x821D51C8 — full shot reset
extern "C" const float lbl_825C5938; // @ 0x825C5938

namespace {
template<class T> T& field(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
void zeroVmxRow(void* object, unsigned offset) {
    auto* row = static_cast<uint8_t*>(object) + offset;
    // Local host alignment for stvx; the resulting pointer is never stored.
    auto* aligned = reinterpret_cast<void*>(
        reinterpret_cast<uintptr_t>(row) & ~uintptr_t(15)); // ptr32-check: host
    __builtin_memset(aligned, 0, 16);
}
}

// Reset a player's shot entry and its embedded full shot. The byte at +0x151
// and other padding are deliberately retained.
// @ 0x821D5F70 | size: 0xE0
void pongPlayer_5F70_g(void* entry) {
    field<float>(entry, 0x144) = 1.0f;
    field<uint32_t>(entry, 0xD0) = 0;
    field<uint8_t>(entry, 0xD7) = 0;
    zeroVmxRow(entry, 0xE0);
    zeroVmxRow(entry, 0xF0);
    field<float>(entry, 0x104) = 0.0f;
    field<float>(entry, 0x100) = 0.0f;
    zeroVmxRow(entry, 0x110);
    field<float>(entry, 0x118) = 0.5f;
    zeroVmxRow(entry, 0x120);
    field<float>(entry, 0x130) = 0.0f;
    field<float>(entry, 0x134) = lbl_825C5938;
    field<float>(entry, 0x14C) = 0.0f;
    SinglesNetworkClient_51C8_g(static_cast<uint8_t*>(entry) + 0x10);
    field<float>(entry, 0x13C) = 0.0f;
    field<float>(entry, 0x154) = 0.0f;
    field<uint8_t>(entry, 0x150) = 0;
    field<float>(entry, 0x158) = 0.0f;
    field<uint8_t>(entry, 0x152) = 0;
    field<float>(entry, 0x15C) = 0.0f;
    field<uint8_t>(entry, 0x160) = 0;
    field<uint8_t>(entry, 0xD8) = 1;
}
