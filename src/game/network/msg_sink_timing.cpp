#include "../misc/pong_misc.hpp"
#include "game/message_sink_time.hpp"
#include "rage/ptr32.hpp"
#include <cstdint>

uint32_t atSingleton_6F98_g(); // @ 0x82566F98

namespace {
struct ClockMessageTarget {
    virtual void Unknown00() = 0;
    virtual void Unknown01() = 0;
    virtual void Unknown02() = 0;
    virtual void Unknown03() = 0;
    virtual void Unknown04() = 0;
    virtual void Unknown05() = 0;
    virtual void Unknown06() = 0;
    virtual void Unknown07() = 0;
    virtual void Unknown08() = 0;
    virtual void Dispatch(uint32_t flags) = 0;
    virtual void Unknown10() = 0;
    virtual void Unknown11() = 0;
    virtual uint32_t GetState() = 0;
};
}

// @ 0x82454158 | size: 0x64
int32_t msgSink_HasCompletedSession(void* sink) {
    void* attached = rage::load_ptr32<void>(sink, 0x28);
    if (!attached) return 0;
    void* owner = rage::load_ptr32<void>(attached, 0x18);
    auto* target = rage::load_ptr32<ClockMessageTarget>(owner, 0x24);
    return target && static_cast<uint8_t>(target->GetState()) == 0xFF;
}

// @ 0x824564D8 | size: 0x78
int32_t msgSink_GetDeadlineOverrun(void* sink) {
    auto* bytes = static_cast<uint8_t*>(sink);
    if (*reinterpret_cast<uint32_t*>(bytes + 0x16C) == 0) return 0;
    const uint32_t now = atSingleton_6F98_g();
    const int32_t pausedAt = *reinterpret_cast<int32_t*>(bytes + 0x174);
    const uint32_t paused = pausedAt > 0 ? now - static_cast<uint32_t>(pausedAt) : 0;
    return static_cast<int32_t>(now - *reinterpret_cast<uint32_t*>(bytes + 0x170) - paused -
                                *reinterpret_cast<uint32_t*>(bytes + 0x16C));
}

// @ 0x82456550 | size: 0x5C
int32_t msgSink_GetAdjustedDeadlineOverrun(void* sink) {
    auto* bytes = static_cast<uint8_t*>(sink);
    if (*reinterpret_cast<uint32_t*>(bytes + 0x16C) == 0) return 0;
    const uint32_t overrun = static_cast<uint32_t>(msgSink_GetDeadlineOverrun(sink));
    auto* context = rage::load_ptr32<uint8_t>(bytes, 0x38);
    return static_cast<int32_t>(overrun + *reinterpret_cast<uint32_t*>(context + 0x28));
}

// @ 0x824566B0 | size: 0x160
int32_t msgSink_IsPeerReady(void* sink) {
    auto* bytes = static_cast<uint8_t*>(sink);
    auto word = [&](uint32_t offset) { return *reinterpret_cast<int32_t*>(bytes + offset); };
    auto peer = [&](uint32_t offset) { return rage::load_ptr32<uint8_t>(bytes, offset); };
    auto peerKind = [&]() { return *reinterpret_cast<uint16_t*>(peer(0x198) + 0x18) & 0xE0; };
    if (peer(0x190) || (word(0x158) != 8 && word(0x3C) != 1) || word(0x19C) != 1)
        return 0;
    bool ready = true;
    if (word(0x17C) != 0) {
        const int32_t overrun = msgSink_GetAdjustedDeadlineOverrun(sink);
        if (word(0x178) > overrun) ready = false;
    } else {
        auto* primary = peer(0x34);
        if (primary && peerKind() == 0x80) {
            const int32_t state = *reinterpret_cast<int32_t*>(primary + 0x50);
            if (state != 5 && state != 6 && !msgSink_HasCompletedSession(primary)) ready = false;
        }
        if (peer(0x34) && peerKind() == 0x60) ready = false;
        const uint32_t code = peerKind() >> 5;
        if ((code == 1 || code == 2) && word(0x184) != 0) ready = false;
    }
    auto* secondary = peer(0x18C);
    if (secondary && *reinterpret_cast<int32_t*>(secondary + 0x50) != 3) ready = false;
    auto* tertiary = peer(0x188);
    if (tertiary && *reinterpret_cast<int32_t*>(tertiary + 0x50) != 3) return 0;
    return ready;
}

// @ 0x824542D0 | size: 0x30
void msgMsgSink::DispatchVirtualMethod(uint32_t flags) {
    void* attached = rage::load_ptr32<void>(this, 0x28);
    if (!attached) return;
    void* owner = rage::load_ptr32<void>(attached, 0x18);
    auto* target = rage::load_ptr32<ClockMessageTarget>(owner, 0x24);
    if (target) target->Dispatch(flags);
}

// @ 0x82456810 | size: 0x110
void msgMsgSink::vfn_65(void* key) {
    auto* bytes = reinterpret_cast<uint8_t*>(this);
    auto slot = [&](uint32_t offset) -> rage::ptr32<void>& {
        return *reinterpret_cast<rage::ptr32<void>*>(bytes + offset);
    };
    if (slot(0x34) == key) {
        slot(0x34) = nullptr;
        *reinterpret_cast<int16_t*>(bytes + 0x194) = -1;
        slot(0x28) = nullptr;
        if (*reinterpret_cast<int32_t*>(bytes + 0x19C) != 1) return;
        if (*reinterpret_cast<int32_t*>(bytes + 0x17C) != 0) return;
        auto* peer = rage::load_ptr32<uint8_t>(bytes, 0x198);
        const uint16_t raw = *reinterpret_cast<uint16_t*>(peer + 0x18);
        const uint32_t code = (raw >> 5) & 7;
        if (code != 4 && code != 3) return;
        *reinterpret_cast<int32_t*>(bytes + 0x178) = msgSink_GetDeadlineOverrun(this);
        *reinterpret_cast<uint32_t*>(bytes + 0x17C) = 1;
    } else if (slot(0x18C) == key) {
        *reinterpret_cast<int16_t*>(bytes + 0x196) = -1;
        slot(0x18C) = nullptr;
    } else if (slot(0x188) == key) {
        slot(0x188) = nullptr;
    } else if (slot(0x190) == key) {
        slot(0x190) = nullptr;
    }
}

// @ 0x82456920 | size: 0x48
void msgMsgSink::vfn_66(msgMsgSink* peer) {
    peer->DispatchVirtualMethod(0);
    auto* bytes = reinterpret_cast<uint8_t*>(this);
    *reinterpret_cast<int32_t*>(bytes + 0x178) = msgSink_GetDeadlineOverrun(this);
    *reinterpret_cast<uint32_t*>(bytes + 0x17C) = 1;
}

// @ 0x82456968 | size: 0x40
void msgMsgSink::vfn_67() {
    auto* bytes = reinterpret_cast<uint8_t*>(this);
    *reinterpret_cast<uint32_t*>(bytes + 0x184) = 0;
    *reinterpret_cast<int32_t*>(bytes + 0x178) = msgSink_GetDeadlineOverrun(this);
    *reinterpret_cast<uint32_t*>(bytes + 0x17C) = 1;
}
