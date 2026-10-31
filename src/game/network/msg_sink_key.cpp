#include "game/message_sink_key.hpp"
#include "../misc/pong_misc.hpp"
#include "rage/ptr32.hpp"

namespace {
struct KeySource {
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
    virtual void Unknown11() = 0;
    virtual void Unknown12() = 0;
    virtual void* Query(void* key) = 0;
};
}

// @ 0x82458D28 | size: 0x54
int32_t msgSink_MatchesKey(void* sink, void* key) {
    auto* source = rage::load_ptr32<KeySource>(sink, 0x24);
    // The probe remains in r4 for the virtual call, then the result is compared.
    return source && source->Query(key) == key;
}

// @ 0x82459B98 | size: 0x78
int32_t atSingleton_9B98_p39(void* child, void* key) {
    void* first = rage::load_ptr32<void>(child, 0x18);
    if (first && msgSink_MatchesKey(first, key)) return 1;
    void* second = rage::load_ptr32<void>(child, 0x1C);
    return second && msgSink_MatchesKey(second, key);
}

// @ 0x82453D70 | size: 0x58
uint32_t msgMsgSink_3D70_p39(void* sink, void* key) {
    auto* head = static_cast<uint8_t*>(sink) + 0x24;
    auto* child = rage::load_ptr32<uint8_t>(sink, 0x28);
    while (child != head) {
        if (atSingleton_9B98_p39(child, key)) return 1;
        child = rage::load_ptr32<uint8_t>(child, 4);
    }
    return 0;
}

// @ 0x8244E148 | size: 0x18
uint32_t msgMsgSink::GetNestedObjectValue(void* key) {
    void* nested = rage::load_ptr32<void>(this, 0x34);
    return nested ? msgMsgSink_3D70_p39(nested, key) : 0;
}
