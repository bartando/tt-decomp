#include "rage/localized_font.hpp"

extern "C" void rage_free(void* pointer); // @ 0x820C00C0

namespace {
struct FontEffect {
    uint8_t reserved[0x10];
    rage::ptr32<void> data;
    rage::ptr32<void> standaloneData;
    rage::ptr32<FontEffect> first;
    rage::ptr32<FontEffect> second;
    uint32_t references;
};
static_assert(sizeof(FontEffect) == 0x24);
}

// @ 0x82151268
uint32_t localizedFontEffectRelease(void* raw) {
    auto* effect = static_cast<FontEffect*>(raw);
    const uint32_t remaining = --effect->references;
    if (remaining == 0) {
        localizedFontEffectDestroy(effect, 1);
        return 0;
    }
    return remaining;
}

// Flags are not consumed by the retail destructor body.
// @ 0x821512B8
void* localizedFontEffectDestroy(void* raw, uint32_t /*flags*/) {
    auto* effect = static_cast<FontEffect*>(raw);
    if (effect->second) localizedFontEffectRelease(effect->second.get());
    rage_free(effect->data.get());
    if (!effect->first && !effect->second) rage_free(effect->standaloneData.get());
    if (effect->first) localizedFontEffectRelease(effect->first.get());
    rage_free(effect);
    return effect;
}
