#include "rage/ptr32.hpp"
#include "localized_font_internal.hpp"
#include <cstdint>
#include <cstring>

extern "C" {
void sysMemAllocator_InitThreadHeap(); // @ 0x820C0038
extern void* g_sda_base; // @ 0x82600000
extern const char g_localizedFallbackFont[]; // @ 0x82075804
void rage_free(void* pointer); // @ 0x820C00C0
void* rage_strDuplicate(const char* text); // @ 0x820C29E0
}

// @ 0x82409128
void* localizedFontCreate(const char* name) {
    char normalized[80];
    if (!name) {
        std::strncpy(normalized, g_localizedFallbackFont, sizeof(normalized));
    } else {
        for (unsigned i = 0; i < sizeof(normalized); ++i) {
            const unsigned char character = static_cast<unsigned char>(name[i]);
            normalized[i] = static_cast<char>(character >= 'A' && character <= 'Z'
                                              ? character + ('a' - 'A') : character);
            if (character == 0) break;
        }
    }
    sysMemAllocator_InitThreadHeap();
    auto* heap = currentFontAllocator();
    void* font = heap->Allocate(0x17C, 16);
    if (font) font = localizedFontConstruct(font);
    // Allocation failure still reaches Load(nullptr, ...), just as in retail.
    if (static_cast<uint8_t>(localizedFontLoad(font, normalized, 0)) == 0) {
        if (static_cast<uint8_t>(localizedFontLoad(font, g_localizedFallbackFont, 0)) == 0) {
            if (font) {
                localizedFontDestroy(font);
                rage_free(font);
            }
            return nullptr;
        }
        auto& fontName = *reinterpret_cast<rage::ptr32<char>*>(static_cast<uint8_t*>(font) + 0x170);
        rage_free(fontName.get());
        fontName = static_cast<char*>(rage_strDuplicate(normalized));
    }
    return font;
}
