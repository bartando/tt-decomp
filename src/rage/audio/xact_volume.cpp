#include "audio/xact_volume.hpp"
#include "rage/ptr32.hpp"
#include <cstring>

namespace rage {
extern const float g_xactFadeZero; // @ 0x82003DA8
extern const float g_xactFadeOne; // @ 0x82003DAC
namespace {
struct VolumeGroup {
    virtual void Unknown00() = 0;
    virtual void Unknown01() = 0;
    virtual void Unknown02() = 0;
    virtual void Unknown03() = 0;
    virtual void Unknown04() = 0;
    virtual void Unknown05() = 0;
    virtual uint32_t GetParent(uint32_t index) = 0;
};
struct VolumeTarget {
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
    virtual void Unknown13() = 0;
    virtual void Unknown14() = 0;
    virtual void Unknown15() = 0;
    virtual void SetVolume(float volume) = 0;
};
}

// @ 0x82448AB8 | size: 0xC0
float xactGroup_GetVolume(void* owner, uint32_t index) {
    auto* group = rage::load_ptr32<uint8_t>(owner, 0x7C);
    float volume = g_xactFadeOne;
    if (!group) return volume;
    uint16_t slot = static_cast<uint16_t>(index);
    const auto* muted = rage::load_ptr32<uint32_t>(group, 0x70);
    if (muted[slot] != 0) return g_xactFadeZero;
    if (*reinterpret_cast<uint32_t*>(group + 0x74) != 0 &&
        rage::load_ptr32<uint32_t>(group, 0x6C)[slot] == 0) return g_xactFadeZero;
    while (slot != 0xFFFF) {
        const float scale = rage::load_ptr32<float>(group, 0x78)[slot];
        volume = scale * volume;
        index = reinterpret_cast<VolumeGroup*>(group)->GetParent(index);
        slot = static_cast<uint16_t>(index);
    }
    return volume;
}

// @ 0x82454AC0 | size: 0x74
float xactSink_GetCombinedVolume(void* sink) {
    auto* bytes = static_cast<uint8_t*>(sink);
    const float local = *reinterpret_cast<float*>(bytes + 0x58);
    const float base = *reinterpret_cast<float*>(bytes + 8);
    const float fade = *reinterpret_cast<float*>(bytes + 0x70);
    uint16_t index;
    std::memcpy(&index, rage::load_ptr32<uint8_t>(sink, 0x1C) + 1, sizeof(index));
    const float group = xactGroup_GetVolume(rage::load_ptr32<void>(sink, 0x20), index);
    auto* session = rage::load_ptr32<uint8_t>(sink, 0x30);
    float volume = *reinterpret_cast<float*>(session + 0x1C) * local;
    volume = volume * group;
    volume = volume * fade;
    return volume * base;
}

// @ 0x82458D80 | size: 0x20
void xactSink_SetTargetVolume(void* sink, float volume) {
    auto* target = rage::load_ptr32<VolumeTarget>(sink, 0x24);
    if (target) target->SetVolume(volume);
}

// @ 0x82459C10 | size: 0x64
void xactChild_UpdateVolume(void* child) {
    auto* bytes = static_cast<uint8_t*>(child);
    if (!rage::load_ptr32<void>(child, 0x18)) return;
    const float local = *reinterpret_cast<float*>(bytes + 0x28);
    const float fade = *reinterpret_cast<float*>(bytes + 0x38);
    const float combined = xactSink_GetCombinedVolume(rage::load_ptr32<void>(child, 0x14));
    const float scaled = local * combined;
    xactSink_SetTargetVolume(rage::load_ptr32<void>(child, 0x18), scaled * fade);
}

// @ 0x82454020 | size: 0x24
void xactSink_SetVolume(void* sink, float volume) {
    const float zero = g_xactFadeZero;
    *reinterpret_cast<float*>(static_cast<uint8_t*>(sink) + 0x70) = volume >= zero ? volume : zero;
    msgMsgSink_3DC8_g(sink);
}
}

// @ 0x82453DC8 | size: 0x50
void msgMsgSink_3DC8_g(void* sink) {
    auto* head = static_cast<uint8_t*>(sink) + 0x24;
    auto* child = rage::load_ptr32<uint8_t>(sink, 0x28);
    while (child != head) {
        rage::xactChild_UpdateVolume(child);
        child = rage::load_ptr32<uint8_t>(child, 4);
    }
}
