#include "game/message_sink_children.hpp"
#include "rage/ptr32.hpp"

void game_A650_h(void* child); // @ 0x8245A650

namespace {
struct DeletableSink {
    virtual void Unknown00() = 0;
    virtual void Delete(uint32_t flags) = 0;
};
struct NestedSinkTarget {
    virtual void Unknown00() = 0;
    virtual void Unknown01() = 0;
    virtual void Unknown02() = 0;
    virtual void Unknown03() = 0;
    virtual void Unknown04() = 0;
    virtual void Unknown05() = 0;
    virtual void Unknown06() = 0;
    virtual void Unknown07() = 0;
    virtual void Unknown08() = 0;
    virtual void Unknown09() = 0;
    virtual void Unknown10() = 0;
    virtual uint32_t HasPending() = 0;
    virtual void Unknown12() = 0;
    virtual void Unknown13() = 0;
    virtual void Unknown14() = 0;
    virtual void Unknown15() = 0;
    virtual void Unknown16() = 0;
    virtual void Unknown17() = 0;
    virtual void Unknown18() = 0;
    virtual void Unknown19() = 0;
    virtual void Unknown20() = 0;
    virtual int32_t SetPaused(uint32_t paused) = 0;
};
}

// @ 0x82458E60 | size: 0x24
uint32_t msgMsgSink_8E60_sp(void* sink) {
    auto* target = rage::load_ptr32<NestedSinkTarget>(sink, 0x24);
    return target ? target->HasPending() : 0;
}

// @ 0x82458E88 | size: 0x24
int32_t msgMsgSink_8E88_sp(void* sink, uint32_t paused) {
    auto* target = rage::load_ptr32<NestedSinkTarget>(sink, 0x24);
    return target ? target->SetPaused(paused) : 0;
}

// @ 0x82459D58 | size: 0x18
uint32_t msgChild_HasPendingTarget(void* child) {
    void* sink = rage::load_ptr32<void>(child, 0x18);
    return sink ? msgMsgSink_8E60_sp(sink) : 0;
}

// @ 0x82459D70 | size: 0x18
int32_t msgChild_SetPaused(void* child, uint32_t paused) {
    void* sink = rage::load_ptr32<void>(child, 0x18);
    return sink ? msgMsgSink_8E88_sp(sink, paused) : 0;
}

// @ 0x82453F68 | size: 0x68
int32_t msgSink_HasPendingChildren(void* sink) {
    auto* head = static_cast<uint8_t*>(sink) + 0x24;
    auto* child = rage::load_ptr32<uint8_t>(sink, 0x28);
    while (child != head) {
        if (msgChild_HasPendingTarget(child)) return 1;
        child = rage::load_ptr32<uint8_t>(child, 4);
    }
    return 0;
}

// @ 0x82454550 | size: 0x88
void msgMsgSink_4550_g(void* sink) {
    auto* bytes = static_cast<uint8_t*>(sink);
    if (*reinterpret_cast<int32_t*>(bytes + 0x50) == 6 && !msgSink_HasPendingChildren(sink)) {
        reinterpret_cast<DeletableSink*>(sink)->Delete(1);
        return;
    }
    auto* head = bytes + 0x24;
    auto* child = rage::load_ptr32<uint8_t>(bytes, 0x28);
    while (child != head) {
        game_A650_h(child);
        child = rage::load_ptr32<uint8_t>(child, 4);
    }
}
