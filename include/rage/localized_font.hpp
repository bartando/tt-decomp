#pragma once
#include "rage/ptr32.hpp"
#include <cstddef>
#include <cstdint>

template <typename T>
struct LocalizedFontArray {
    rage::ptr32<T> data;
    uint16_t count, capacity;
};

struct LocalizedFontGlyph {
    uint32_t code;
    uint8_t metrics[6];
    uint8_t reserved[2];
};

struct LocalizedFont {
    LocalizedFontArray<rage::ptr32<void>> textures;
    LocalizedFontArray<rage::ptr32<void>> effects;
    LocalizedFontArray<rage::ptr32<void>> auxiliaryTextures;
    LocalizedFontArray<rage::ptr32<void>> auxiliaryEffects;
    LocalizedFontArray<uint32_t> pages;
    int32_t size, field2C, height, spacing;
    uint32_t field38, field3C;
    int32_t border[4];
    uint32_t field50[4];
    uint8_t lod;
    uint8_t reserved61[3];
    rage::ptr32<LocalizedFontGlyph> glyphs;
    uint32_t glyphCount;
    uint8_t glyphIndex[256];
    uint16_t fallbackGlyph;
    uint8_t reserved16E[2];
    rage::ptr32<char> name;
    rage::ptr32<LocalizedFont> next;
    uint32_t references;
};
static_assert(sizeof(LocalizedFont) == 0x17C);
static_assert(offsetof(LocalizedFont, glyphs) == 0x64);
static_assert(offsetof(LocalizedFont, name) == 0x170);

struct LocalizedFontShutdownRecord {
    rage::ptr32<void> object;
    rage::ptr32<void()> callback;
    uint32_t argument, flags;
};
struct LocalizedFontShutdownRegistry {
    rage::ptr32<LocalizedFontShutdownRecord> records;
    uint16_t count, capacity;
};
static_assert(sizeof(LocalizedFontShutdownRecord) == 16);
static_assert(sizeof(LocalizedFontShutdownRegistry) == 8);

extern "C" {
extern rage::ptr32<LocalizedFont> g_localizedFontHead; // @ 0x826066E0
extern LocalizedFontShutdownRegistry g_localizedFontShutdownRegistry; // @ 0x825CB9A0
extern const char g_localizedFontReleaseError[]; // @ 0x8207580C
extern const char g_localizedFontResetName[]; // @ 0x82027C50
}

void* localizedFontCreate(const char* name); // @ 0x82409128
void localizedFontRelease(void* font); // @ 0x82409278
void* localizedFontConstruct(void* storage); // @ 0x82409338
void localizedFontDestroy(void* font); // @ 0x82409490
void localizedFontReset(void* font, uint32_t flags, const char* name); // @ 0x82409578
uint32_t localizedFontLoad(void* font, const char* name, uint32_t flags); // @ 0x824098E8
void localizedFontClearResources(void* font); // @ 0x82409F08
void localizedFontShutdown(); // @ 0x8240A208
uint32_t localizedFontEffectRelease(void* effect); // @ 0x82151268
void* localizedFontEffectDestroy(void* effect, uint32_t flags); // @ 0x821512B8
void localizedFontResizeArray(void* array, uint32_t count); // @ 0x8240A250
