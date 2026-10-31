#include "rage/hud_page_group.hpp"
#include "rage/fi_asset.hpp"
#include "rage/operator_new.hpp"
#include "rage/ptr32.hpp"
#include <cstddef>

extern "C" uint8_t g_fiAssetManager[]; // @ 0x825D0080
extern "C" uint8_t g_sda_660D; // @ 0x8260660D
extern const char g_flashAssetFolder[]; // @ 0x8205AE18
extern const char g_flashResourceFolder[]; // @ 0x8205AE04
extern const char g_flashExtension[]; // @ 0x8205AE54
extern const char g_flashPathFormat[]; // @ 0x8202F610
extern const char g_flashEmptyName[]; // @ 0x82027423
extern const char g_flashCreateError[]; // @ 0x8205AE58
extern "C" int _snprintf(char*, size_t, const char*, ...); // @ 0x820C0B40
extern "C" void rage_debugLog(const char*, ...); // @ 0x8240E6D0

void* pgStreamer_LoadResource(const char* path, uint32_t version,
                              uint32_t* imageBase, uint32_t* size); // @ 0x820F9380
void* datResourceScope_Construct(void* scope, void* file, uint32_t imageBase, uint32_t size); // @ 0x82188190
void datResourceScope_Destroy(void* scope); // @ 0x82188220
void* swfFile_Place(void* file, void* resourceScope); // @ 0x823F9EA0
void* swfPageGroup_Construct(void* memory, void* file, uint32_t width, uint32_t height,
                            uint32_t pool1, uint32_t pool2, uint32_t flags); // @ 0x823F8D08

namespace {
struct FlashLoadConfig {
    rage::ptr32<const char> name;
    uint16_t length;
    uint16_t capacity;
    uint32_t width, height, pool1, pool2, flags;
    uint8_t loadFlags;
};
struct FlashLoadHud {
    uint8_t pad00[0x40];
    rage::ptr32<FlashLoadConfig> config;
    uint8_t pad44[0x14];
    rage::ptr32<void> file;
    rage::ptr32<void> movie;
};
static_assert(offsetof(FlashLoadHud, movie) == 0x5C);
static_assert(offsetof(FlashLoadConfig, loadFlags) == 0x1C);
}

// @ 0x822EADF8
extern "C" void hudFlashBase_LoadPageGroup(void* object, uint32_t resourceVersion) {
    auto* hud = static_cast<FlashLoadHud*>(object);
    auto* config = hud->config.get();
    const char* name = config->length ? config->name.get() : g_flashEmptyName;
    if (!hud->file) {
        g_sda_660D = config->loadFlags;
        fiAssetManager_PushFolder(g_fiAssetManager, g_flashAssetFolder);
        char resolvedPath[128];
        fiPath_Build(g_fiAssetManager, resolvedPath, sizeof(resolvedPath), name, g_flashExtension, 0);
        char resourcePath[256];
        _snprintf(resourcePath, sizeof(resourcePath), g_flashPathFormat, g_flashResourceFolder, name);
        uint32_t imageBase, size;
        void* file = pgStreamer_LoadResource(resourcePath, resourceVersion, &imageBase, &size);
        hud->file = file;
        if (file) {
            alignas(4) uint8_t resourceScope[0x54];
            datResourceScope_Construct(resourceScope, file, imageBase, size);
            swfFile_Place(file, resourceScope);
            datResourceScope_Destroy(resourceScope);
        }
        auto* depth = reinterpret_cast<uint32_t*>(g_fiAssetManager + 0x600);
        --*depth;
        const uint8_t acquired = static_cast<uint8_t>(hudFlashBase_IsNetworkDirty(hud));
        void* movie = rage_Alloc(0xAC);
        if (movie) {
            config = hud->config.get();
            movie = swfPageGroup_Construct(movie, hud->file.get(),
                static_cast<uint16_t>(config->width), static_cast<uint16_t>(config->height),
                static_cast<uint16_t>(config->pool1), static_cast<uint16_t>(config->pool2), config->flags);
        }
        hud->movie = movie;
        if (acquired != 0) hudFlashBase_PublishPageGroup(hud);
    }
    if (!hud->movie) {
        config = hud->config.get();
        rage_debugLog(g_flashCreateError, config->length ? config->name.get() : g_flashEmptyName);
    }
    g_swfCommandHandler = hudFlashBase_ScriptCommand;
}
