/**
 * rage/ui_context.c — UI Context Registration System
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Implements the UI context registration system used by credits, dialog,
 * leaderboard, and other UI screens. Also includes render mode configuration.
 *
 * Functions:
 *   rage_RenderDebugOverlay — debug FPS overlay (stub in this build)
 *   rage_SetRenderMode      — configures render pipeline and FPS target
 */

#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* ─────────────────────────────────────────────────────────────────────────────
 * External functions
 * ───────────────────────────────────────────────────────────────────────────── */

/* RAGE UI factory singleton accessor — retrieves the global UI factory. */
extern void rage_GetUIFactory(void* pFactory);

/* Factory build — creates a UI object from the factory using a type name
 * and stack buffer for construction.
 * @ uses UIPageGroup type string internally */
extern void* rageObjectFactory_Build(void* pFactory, void* pStackBuf,
                                     uint32_t bufSize, const char* typeName,
                                     uint32_t flags, const char* nameStr);

/* Texture loader — loads a texture from an XML layout path and fills
 * in width/height dimensions. */
extern void* rage_LoadTexture(const char* path, uint32_t* pWidth,
                               uint32_t* pHeight);

/* grcTextureInfo initialization — constructs a 16-byte texture info
 * struct on the stack with the given dimensions.
 * @ 0x82188190 | size: 0x90 */
extern void grcTextureInfo_Init(void* pTexInfo, uint32_t width, uint32_t height);

/* UIPageGroup texture binding — binds a loaded texture to a page group.
 * @ 0x823F9EA0 | size: 0x10C */
extern void UIPageGroup_BindTexture(void* pPageGroup, void* pTexInfo);

/* grcTextureInfo cleanup — releases any resources held by the texture info.
 * @ 0x82188220 | size: 0x60 */
extern void grcTextureInfo_Cleanup(void* pTexInfo);

/* UI context category query — returns non-zero if the context should
 * create a category entry for the category manager.
 * @ 0x822EB2A8 | size: 0x78 */
extern void* uiContext_ShouldCreateCategory(void* pContext);

/* RAGE heap allocator. */
extern void* rage_alloc(uint32_t size);

/* Category entry creation — creates and initializes a 172-byte category
 * entry from config data fields and a page group.
 * @ 0x823F8D08 | size: 0x2E8 */
extern void* uiCategoryEntry_Create(void* pPageGroup, uint32_t field1,
                                     uint32_t field2, uint32_t field3,
                                     uint32_t field4, uint32_t categoryId);

/* UI context registration notification — notifies the context that
 * registration is complete.
 * @ 0x822EB320 | size: 0x60 */
extern void uiContext_NotifyRegistered(void* pContext);

/* Debug logging (no-op in release builds). */
extern void rage_DebugLog(const char* fmt, ...);

/* CRT snprintf. */
extern int _snprintf(char* buf, size_t size, const char* fmt, ...);

/* ─────────────────────────────────────────────────────────────────────────────
 * External globals
 * ───────────────────────────────────────────────────────────────────────────── */

/* RAGE UI factory singleton (1544 bytes). */
extern void* g_pUIFactory;              /* @ 0x825D0080 */

/* Render device pointer (inside large render device data block). */
extern void* g_pRenderDevice;           /* @ 0x825BF938 */

/* Render flags byte — controls various render mode options. */
extern uint8_t g_renderFlags;           /* @ 0x826063DB */





/* ═══════════════════════════════════════════════════════════════════════════════
 *  rage_RenderDebugOverlay
 *
 *  @ 0x82228C68 | size: 0x194 (404 bytes)
 *
 *  Renders debug FPS overlay on screen.  Set as a config callback during
 *  initialization.  The full implementation renders debug text twice with
 *  different blend modes for visibility — requires HUD flash system.
 * ═══════════════════════════════════════════════════════════════════════════════ */
void rage_RenderDebugOverlay(void)
{
    /* Open: the 404-byte body @ 0x82228C68 renders the debug overlay
     * through hudFlashBase twice (drop-shadow pass + main pass) with
     * different blend modes. Deferred until hudFlashBase::Update /
     * SetPropertyById are lifted and the Flash text-draw helper is
     * available; the release build no-ops this callback so the stub
     * below is functionally correct for non-debug runs. */
    rage_DebugLog("rage_RenderDebugOverlay called");
}


/* ═══════════════════════════════════════════════════════════════════════════════
 *  rage_SetRenderMode
 *
 *  @ 0x8214F9A8 | size: 0xB0 (176 bytes)
 *
 *  Configures the render mode and FPS target.  Called during gameLoop
 *  initialization to set up the rendering pipeline.
 *
 *  Sequence:
 *    1. Check if already initialized (flag at g_pRenderDeviceState+4)
 *    2. Store target FPS and render flags
 *    3. Initialize grcDevice render pipeline:
 *       BeginRenderConfig → InitializeRenderConfig → SetupRenderFiber →
 *       CleanupRenderTargets → ConfigureRenderTargets → FinalizeRenderSetup
 * ═══════════════════════════════════════════════════════════════════════════════ */
void rage_SetRenderMode(int32_t targetFPS, int32_t flags)
{
    extern void* g_pRenderDeviceState;  /* @ 0x825C9A90 */
    extern int32_t g_nTargetFPS;        /* @ 0x825D903C */
    extern void* g_pRenderConfig;       /* @ 0x825EB900 */

    extern void grcDevice_BeginRenderConfig(void);
    extern void grcDevice_InitializeRenderConfig(void);
    extern void grcDevice_SetupRenderFiber(void* pDevice);
    extern void grcDevice_CleanupRenderTargets(void* pDevice);
    extern int  grcDevice_ConfigureRenderTargets(void* pDevice, void* pConfig);
    extern void grcDevice_FinalizeRenderSetup(void);

    uint32_t* pState;
    uint32_t initFlag;
    int result;

    /* Check if already initialized */
    pState = (uint32_t*)g_pRenderDeviceState;
    initFlag = *(uint32_t*)(pState + 1);

    if (initFlag != 0) {
        return;  /* Already initialized */
    }

    /* Store target FPS and render flags */
    g_nTargetFPS = targetFPS;
    g_renderFlags = (uint8_t)flags;

    /* Initialize grcDevice render pipeline if device present */
    if (g_pRenderDevice != NULL) {
        grcDevice_BeginRenderConfig();
        grcDevice_InitializeRenderConfig();
        grcDevice_SetupRenderFiber(g_pRenderDevice);
        grcDevice_CleanupRenderTargets(g_pRenderDevice);

        result = grcDevice_ConfigureRenderTargets(g_pRenderDevice,
                                                   g_pRenderConfig);

        if (result == 0) {
            /* Configuration failed — clean up */
            grcDevice_CleanupRenderTargets(g_pRenderDevice);
        }

        grcDevice_FinalizeRenderSetup();
    }
}
