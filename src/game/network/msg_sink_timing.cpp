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
};
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
