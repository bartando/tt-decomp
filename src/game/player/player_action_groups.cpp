// Action-group enable/reset propagation from the outer player.
#include <cstdint>

namespace {
// The reset callback occupies the second entry in this object's PPC vtable.
struct ActionResetTarget {
    virtual void Reserved0() = 0;
    virtual void Reset() = 0;
};

template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
}

// @ 0x8218BBE0 | size: 0xF8
void pongPlayer_BBE0_g(void* player, uint32_t flags) {
    const uint8_t enable = static_cast<uint8_t>(flags);
    const float weight = at<int32_t>(player, 0x1CC) == 7 ? 0.0f : 0.75f;
    for (uint32_t i = 0; i < at<uint16_t>(player, 0x1818); ++i) {
        void* group = at<void**>(player, 0x1814)[i];
        if (at<uint8_t>(group, 0x3D)) continue;
        at<float>(group, 0x38) = weight;
        at<uint8_t>(group, 0x34) = enable;
        if (at<uint8_t>(group, 0x3C) || !enable || at<float>(group, 0x30) != 0.0f)
            continue;
        // Callbacks may change either array's live count; reload it each time.
        for (uint32_t j = 0; j < at<uint16_t>(group, 8); ++j)
            at<ActionResetTarget**>(group, 4)[j]->Reset();
    }
}
