#include "localized_font_internal.hpp"
#include "rage/grc_texture.hpp"
#include <cstring>

extern "C" {
void rage_free(void* pointer); // @ 0x820C00C0
uint32_t rage_FindSingleton(void* pointer); // @ 0x820F90D0
void sysMemAllocator_InitThreadHeap(); // @ 0x820C0038
}
void nop_8240E6D0(const char*, ...); // @ 0x8240E6D0

namespace {
template <typename T>
void freeBlock(T* pointer) {
    if (pointer && static_cast<uint8_t>(rage_FindSingleton(pointer)) == 0)
        currentFontAllocator()->Free(pointer);
}

template <typename T>
void releaseBlock(rage::ptr32<T>& slot) {
    freeBlock(slot.get());
    slot = nullptr;
}

void releaseElements(LocalizedFont* font) {
    for (unsigned i = 0; i < font->textures.count; ++i) {
        if (void* texture = font->textures.data.get()[i].get())
            rage::Release(static_cast<rage::grcTexture*>(texture));
        if (void* texture = font->auxiliaryTextures.data.get()[i].get())
            rage::Release(static_cast<rage::grcTexture*>(texture));
    }
    for (unsigned i = 0; i < font->effects.count; ++i) {
        if (void* effect = font->effects.data.get()[i].get()) {
            auto& references = *reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(effect) + 0x20);
            if (--references == 0) localizedFontEffectDestroy(effect, 1);
        }
        if (void* effect = font->auxiliaryEffects.data.get()[i].get()) {
            auto& references = *reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(effect) + 0x20);
            if (--references == 0) localizedFontEffectDestroy(effect, 1);
        }
    }
}

template <typename T>
void clearArray(LocalizedFontArray<T>& array) {
    releaseBlock(array.data);
    array.count = 0;
    array.capacity = 0;
}
}

// @ 0x82409338
void* localizedFontConstruct(void* storage) {
    auto* font = static_cast<LocalizedFont*>(storage);
    font->textures = {};
    font->effects = {};
    font->auxiliaryTextures = {};
    font->auxiliaryEffects = {};
    font->pages = {};
    LocalizedFont* previous = g_localizedFontHead.get();
    if (!previous) {
        auto& registry = g_localizedFontShutdownRegistry;
        unsigned i = 0;
        for (; i < registry.count; ++i) {
            const auto& record = registry.records.get()[i];
            if (record.callback == &localizedFontShutdown && !record.object) break;
        }
        if (i == registry.count) {
            LocalizedFontShutdownRecord record{};
            record.callback = &localizedFontShutdown;
            record.flags = 1;
            registry.records.get()[registry.count] = record;
            ++registry.count;
        }
    }
    font->next = previous;
    font->name = nullptr;
    font->references = 1;
    font->field2C = 1;
    font->field3C = 0;
    font->size = 32;
    font->height = 32;
    font->spacing = 32;
    font->field38 = 0;
    for (auto& value : font->border) value = 0;
    for (auto& value : font->field50) value = 0;
    font->lod = 0;
    font->glyphs = nullptr;
    font->glyphCount = 0;
    font->glyphIndex[0] = 0;
    g_localizedFontHead = font;
    font->fallbackGlyph = 0;
    return font;
}

// Formerly misidentified as atContainer_Teardown in memory/atSingleton.cpp.
// @ 0x82409F08
void localizedFontClearResources(void* raw) {
    auto* font = static_cast<LocalizedFont*>(raw);
    releaseElements(font);
    clearArray(font->textures);
    clearArray(font->auxiliaryTextures);
    clearArray(font->effects);
    clearArray(font->auxiliaryEffects);
    clearArray(font->pages);
    releaseBlock(font->name);
    releaseBlock(font->glyphs);
    font->glyphCount = 0;
}

// Incoming flags/name are not read by the retail reset routine.
// @ 0x82409578
void localizedFontReset(void* raw, uint32_t /*flags*/, const char* /*name*/) {
    auto* font = static_cast<LocalizedFont*>(raw);
    releaseElements(font);
    clearArray(font->textures);
    clearArray(font->auxiliaryTextures);
    clearArray(font->effects);
    clearArray(font->auxiliaryEffects);
    clearArray(font->pages);
    // Keep the old name field visible through the allocator callback.
    freeBlock(font->name.get());
    const uint32_t bytes = static_cast<uint32_t>(std::strlen(g_localizedFontResetName)) + 1;
    sysMemAllocator_InitThreadHeap();
    void* thread = rage::load_ptr32<void>(g_sda_base, 0);
    auto* allocator = rage::load_ptr32<FontAllocator>(thread, 4);
    auto* name = static_cast<char*>(allocator->Allocate(bytes, 16));
    font->name = static_cast<char*>(std::memcpy(name, g_localizedFontResetName, bytes));
    auto* glyphs = font->glyphs.get();
    if (glyphs && static_cast<uint8_t>(rage_FindSingleton(glyphs)) == 0) {
        // Retail retains this TLS block, then reloads its allocator after the
        // ownership callback; it does not reload the root from r13 here.
        rage::load_ptr32<FontAllocator>(thread, 4)->Free(glyphs);
    }
    font->glyphs = nullptr;
    font->glyphCount = 0;
    std::memset(font->glyphIndex, 0, sizeof(font->glyphIndex));
    font->fallbackGlyph = 0;
}

// @ 0x82409490
void localizedFontDestroy(void* raw) {
    auto* font = static_cast<LocalizedFont*>(raw);
    localizedFontClearResources(font);
    auto* current = g_localizedFontHead.get();
    if (current == font) {
        g_localizedFontHead = font->next.get();
    } else {
        while (current) {
            if (current->next == font) {
                current->next = font->next.get();
                break;
            }
            current = current->next.get();
        }
    }
    rage_free(font->name.get());
    if (font->pages.capacity) rage_free(font->pages.data.get());
    if (font->auxiliaryEffects.capacity) rage_free(font->auxiliaryEffects.data.get());
    if (font->auxiliaryTextures.capacity) rage_free(font->auxiliaryTextures.data.get());
    if (font->effects.capacity) rage_free(font->effects.data.get());
    if (font->textures.capacity) rage_free(font->textures.data.get());
}

// @ 0x82409278
void localizedFontRelease(void* raw) {
    auto* font = static_cast<LocalizedFont*>(raw);
    if (!font) return;
    const uint32_t references = font->references;
    if (references == 1) {
        auto* current = g_localizedFontHead.get();
        if (current == font) {
            g_localizedFontHead = font->next.get();
            localizedFontDestroy(font);
            rage_free(font);
            return;
        }
        while (current) {
            if (current->next == font) {
                current->next = font->next.get();
                localizedFontDestroy(font);
                rage_free(font);
                return;
            }
            current = current->next.get();
        }
        nop_8240E6D0(g_localizedFontReleaseError);
    }
    font->references = references - 1;
}

// @ 0x8240A208
void localizedFontShutdown() {
    while (g_localizedFontHead) localizedFontRelease(g_localizedFontHead.get());
}
