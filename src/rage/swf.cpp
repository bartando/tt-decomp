/**
 * rage::swf* — Scaleform Flash UI System Implementation
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 * 
 * Implementation of the SWF/Scaleform Flash UI system classes.
 * These handle Flash content loading, ActionScript execution, and
 * display list management for the game's menu and HUD.
 */

#include "rage/swf.hpp"
#include "rage/memory.h"
#include <new>      // For placement new
#include <cstring>  // For strcmp
#include <cstdlib>  // For strtol
#include <cmath>    // For fused multiply-add
#include "rage/sys_callback.hpp"

void swfSetMember(void* list, const char* name, const uint32_t* value); // @ 0x823FB258
uint32_t swfHashMemberName(const char* name); // @ 0x8223A868
uint32_t* swfFindMember(void* list, const char* name); // @ 0x823FB3B8

void swfSetClipEvents(void* instance, uint32_t events, uint32_t records, int32_t count);  // @ 0x823FD320

// External functions
extern "C" {
    extern const char lbl_82074EE4[];  // @ 0x82074EE4
    extern const char lbl_82074EF0[];  // @ 0x82074EF0
    void swfDispatchClipEvents(void* instance, int event, const char* name);  // @ 0x823FD3E8
    void rage_free(void* ptr);                  // @ 0x820C00C0 — canonical heap free (see src/crt/heap.c)
    void swfContext_Cleanup(void* ctx);         // @ 0x823F9B80 — cleanup stub (no-op in final binary)
    void atHashMap_Clear(void* ptr);            // @ 0x8234C0E0 — iterates linked-list hash buckets, frees all nodes
    void swfFile_DestroyResources(void* ptr);   // @ 0x824035B0 — releases child resource array entries
    void swfInstance_Cleanup(void* ptr);        // @ 0x823FB670 — unlinks instance from display list
    void swfSymtab_Enumerate(void* symtab);     // @ 0x823FED10 — enumerate symtab members
    const char* swfInternString(const char* name, void* buffer, int maxLen);  // string interning
    void* swfInstanceConstruct(void* storage);  // @ 0x823FB570
    void rage_DebugLog(const char* msg, ...);    // debug log stub (no-op)
    void swfSymtab_Delete(void* symtab, const char* key);   // symtab key delete
    void* swfPopResult(void* dst);              // @ 0x82403270 — pop and return dst
    int _stricmp(const char*, const char*);     // case-insensitive string compare
    float swfComputeFramePosition(void* ctx, void* entry, float* outMin, float* outMax);
    const char* util_A768_1(const void* value, void* buffer, int maxLen);  // @ 0x823FA768 — SWF value to string
    int32_t swfValueToInteger(const void* value);  // @ 0x823FA5C8
    float swfValueToFloat(const void* value);  // @ 0x823FA688
    double atof(const char* text); // @ 0x82432B80
    int atoi(const char* text); // @ 0x82432120
    void util_F7E8(const uint8_t* code, void* target, void* context, uint32_t length,
                   void* registers, uint32_t keepStack); // @ 0x823FF7E8
    float util_EF98(void* instance, float* outMin);  // @ 0x823FEF98 — display width, optional minimum
    float swfINSTANCE_F0D8_w(void* instance, float* outMin);  // @ 0x823FF0D8 — display height, optional minimum
    void* util_B188(void* slots, int index);  // @ 0x823FB188
    uint8_t util_0068(void* record);  // @ 0x821E0068 — button released this frame
    int _snprintf(char* buffer, size_t count, const char* format, ...);  // @ 0x820C0B40
    extern void* g_sda_6404;  // @ 0x82606404 — shared texture lookup owner
    void hudFlashBase_76F8_g(int stage, int slot, void* texture);  // @ 0x820F76F8
    void hudFlashBase_B138_g();  // @ 0x8215B138
    void grcDevice_Present(uint32_t flags, int color, int clearDepth, float depth,
                           bool clearStencil, int stencil);  // @ 0x8214F088
    extern uint32_t g_grmShaderFx_flushRequired;  // @ 0x825EBB1C
    extern uint32_t g_grmShaderFx_forceResetFlag;  // @ 0x825EBAB4
    extern uint32_t g_swfAppliedRenderState[22];  // @ 0x825EBB80
    extern uint32_t g_grmShaderFx_variantTable[23];  // @ 0x825EBBD8
}

extern bool CheckButtonPressed(void* record);  // @ 0x821DFFF8

extern int rage_2A78(int primitiveType, int vertexCount);  // @ 0x82152A78
extern void fxEmitVertex2D(float x, float y); // @ 0x82406010
extern uint32_t g_fxVertexCursor;  // @ 0x825EBA74
extern uint32_t g_fxCountOnly;     // @ 0x825EBA84
extern uint32_t g_fxVertexCount;   // @ 0x825EBA88
extern uint32_t g_fxCurrentColor; // @ 0x825CA604
extern float g_fxVertexNormalX;   // @ 0x825EBA6C
extern float g_fxVertexNormalY;   // @ 0x825EBA80
extern float g_fxVertexNormalZ;   // @ 0x825EBA8C
extern float g_fxVertexU;         // @ 0x825EBA78
extern float g_fxVertexV;         // @ 0x825EBA70
extern const float g_fxVertexDepth; // @ 0x8202D110
extern const float g_swfAtlasUVScale; // @ 0x820290EC
extern float g_swfPixelScaleX;    // @ 0x82602824
extern float g_swfPixelScaleY;    // @ 0x8260283C
extern void (*g_swfBindFontTexture)(void* texture); // @ 0x82602820
extern void* g_binkVideoPlayer;   // @ 0x825EB988 — graphics device (legacy global name)
extern void fxEmitVertex2D(float x, float y); // @ 0x82406010

// @ 0x823FA5C8
extern "C" int32_t swfValueToInteger(const void* value) {
    const auto* words = static_cast<const uint32_t*>(value);
    switch (words[1]) {
    case 0: case 1:
        // Even the chunk-string tag is parsed directly, without flattening it.
        return std::atoi(reinterpret_cast<const char*>(static_cast<uintptr_t>(words[0])));
    case 2:
        return *static_cast<const uint8_t*>(value);
    case 3:
        return static_cast<int32_t>(words[0]);
    case 4: {
        float number;
        std::memcpy(&number, value, sizeof(number));
        // Match fctiwz for infinities, NaNs and out-of-range finite floats.
        if (number >= 2147483648.0f) return 2147483647;
        if (!(number >= -2147483648.0f)) return -2147483647 - 1;
        return static_cast<int32_t>(number);
    }
    default:
        return 0;
    }
}

// Formerly phBoundCapsule_A688_g; these are SWF VM tags, not physics data.
// @ 0x823FA688
extern "C" float swfValueToFloat(const void* value) {
    const auto* words = static_cast<const uint32_t*>(value);
    switch (words[1]) {
    case 0: case 1:
        return static_cast<float>(std::atof(reinterpret_cast<const char*>(static_cast<uintptr_t>(words[0]))));
    case 2:
        return static_cast<float>(*static_cast<const uint8_t*>(value));
    case 3:
        return static_cast<float>(static_cast<int32_t>(words[0]));
    case 4: {
        float number;
        std::memcpy(&number, value, sizeof(number));
        return number;
    }
    default:
        return 0.0f;
    }
}

// @ 0x823FB3B8
uint32_t* swfFindMember(void* list, const char* name) {
    uint32_t node = *static_cast<const uint32_t*>(list);
    const uint32_t hash = swfHashMemberName(name);
    while (node) {
        const auto* fields = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(node));
        // Identity is hash-only; the first collision wins.
        if (fields[4] == hash) {
            return reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(node + 4));
        }
        node = fields[3];
    }
    return nullptr;
}

// @ 0x823FD3E8
extern "C" void swfDispatchClipEvents(void* instance, int event, const char* name) {
    // Callers supply a diagnostic event name, but retail never reads it.
    (void)name;
    auto* object = static_cast<uint8_t*>(instance);
    uint32_t node = *reinterpret_cast<uint32_t*>(object + 0xC8);
    while (node) {
        auto* link = reinterpret_cast<uint32_t*>(static_cast<uintptr_t>(node));
        const auto* record = reinterpret_cast<const uint32_t*>(static_cast<uintptr_t>(link[0]));
        if (record[0] & static_cast<uint32_t>(event)) {
            auto* actions = reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(record[1]));
            util_F7E8(actions + 2, instance, actions, 0, nullptr, 0);
        }
        // Scripts can change this link: reload it after executing the actions.
        node = link[1];
    }
}

// @ 0x823FA768
extern "C" const char* util_A768_1(const void* value, void* buffer, int maxLen) {
    // The VM uses an 8-byte {payload, tag} pair, with 32-bit guest pointers.
    const uint32_t* words = static_cast<const uint32_t*>(value);
    char* output = static_cast<char*>(buffer);
    switch (words[1]) {
    case 0: {
        const uint8_t* chunk = reinterpret_cast<const uint8_t*>(static_cast<uintptr_t>(words[0]));
        if (!chunk) return nullptr;

        // Copy all twelve bytes, including embedded NULs. This path ignores maxLen.
        char* next = output;
        do {
            for (int i = 0; i < 12; ++i) {
                *next++ = chunk[i];
            }
            chunk = reinterpret_cast<const uint8_t*>(
                static_cast<uintptr_t>(*reinterpret_cast<const uint32_t*>(chunk + 12)));
        } while (chunk);
        *next = '\0';
        return output;
    }
    case 1:
        return reinterpret_cast<const char*>(static_cast<uintptr_t>(words[0]));
    case 2:
        // The boolean is the first byte, not the whole payload word.
        return *static_cast<const uint8_t*>(value) ? "true" : "false";
    case 3:
        _snprintf(output, static_cast<size_t>(maxLen), "%d", static_cast<int32_t>(words[0]));
        return output;
    case 4: {
        float number;
        std::memcpy(&number, value, sizeof(number));

        // fctiwz saturates before the int-to-float round trip. In particular,
        // +2^31 rounds back to itself from INT_MAX and selects the integral format.
        int32_t integer;
        if (number >= 2147483648.0f) {
            integer = 2147483647;
        } else if (!(number >= -2147483648.0f)) {
            integer = -2147483647 - 1;
        } else {
            integer = static_cast<int32_t>(number);
        }
        const char* format = number == static_cast<float>(integer) ? "%0.f" : "%f";
        _snprintf(output, static_cast<size_t>(maxLen), format, static_cast<double>(number));
        return output;
    }
    default:
        return nullptr;
    }
}

// Global SWF object pools (SDA - Small Data Area)
extern void* g_swfScriptObjectPool;  // @ SDA offset 19540
extern void* g_swfInstancePool;      // @ SDA offset 19536
extern void* g_swfScriptArrayPool;   // @ SDA offset 19552

namespace rage {

extern uint32_t g_swfCallDepth;       // @ 0x82604D1C
extern uint32_t g_swfValueStack[192]; // @ 0x82715C98 — 96 {payload, tag} pairs

struct swfAtlasGlyph {
    float u, v, width, height;  // Atlas texels.
    float left, top, right, bottom; // Glyph bounds relative to the text pen.
};
static_assert(sizeof(swfAtlasGlyph) == 32);

struct swfFontAtlas {
    void** textures;
    const swfAtlasGlyph* glyphs;
    uint32_t reserved;
    const uint8_t* textureIndices; // Optional per-glyph texture page; otherwise page 0.
};

struct swfGlyphRenderState {
    float matrix[6]; // a, b, c, d, tx, ty
    void* texture;
};
extern swfGlyphRenderState g_swfGlyphRenderState; // @ 0x82606120

struct swfLineRenderState {
    float uvMatrix[6]; // a, b, c, d, tx, ty
    float matrix[6];
};
extern swfLineRenderState g_swfLineRenderState; // @ 0x8260613C
extern const float g_swfTwipsToPixels; // @ 0x820290F0

namespace {
struct swfGlyphVertex {
    float position[3];
    float normal[3];
    uint32_t color;
    float uv[2];
};
static_assert(sizeof(swfGlyphVertex) == 36);
}

#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC push_options
#pragma GCC optimize("fp-contract=off")
#endif
// Formerly pongShadowMap_3970_w. Text renderers at 0x82404340 and 0x82404CF8
// supply a font atlas, pen coordinates, text scale and a resolved glyph index.
// @ 0x82403970
void swfDrawFontGlyph(const swfFontAtlas* atlas, float x, float y, float scale, int glyphIndex) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    if (!atlas->textures) return;
    void* texture = atlas->textures[atlas->textureIndices ? atlas->textureIndices[glyphIndex] : 0];
    if (g_swfGlyphRenderState.texture != texture) {
        g_swfGlyphRenderState.texture = texture;
        g_swfBindFontTexture(texture);
    }
    const swfAtlasGlyph* glyph = atlas->glyphs + glyphIndex;
    rage_2A78(4, 4);

    const float depth = g_fxVertexDepth;
    const float normalX = g_fxVertexNormalX;
    const float normalY = g_fxVertexNormalY;
    const float normalZ = g_fxVertexNormalZ;
    const uint32_t countOnly = g_fxCountOnly;
    for (unsigned corner = 0; corner < 4; ++corner) {
        const bool right = corner == 0 || corner == 2;
        const bool bottom = corner < 2;
        const float px = ((right ? glyph->right : glyph->left) + x) * scale;
        const float py = (bottom ? glyph->bottom + y : y + glyph->top) * scale;
        const float* m = g_swfGlyphRenderState.matrix;
        // fmuls rounds each x product before fmadds; translation and pixel
        // scaling also round separately. Do not contract the whole expression.
        const float xProduct = px * m[0];
        const float yProduct = px * m[1];
        const float screenX = (std::fma(py, m[2], xProduct) + m[4]) * g_swfPixelScaleX;
        const float screenY = (std::fma(py, m[3], yProduct) + m[5]) * g_swfPixelScaleY;
        const float u = (right ? glyph->u + glyph->width : glyph->u) * g_swfAtlasUVScale;
        const float v = (bottom ? glyph->height + glyph->v : glyph->v) * g_swfAtlasUVScale;
        if (corner == 3) {
            g_fxVertexU = u;
            g_fxVertexV = v;
        }
        if (countOnly == 0 || g_fxVertexCursor != 0) {
            auto* vertex = reinterpret_cast<swfGlyphVertex*>(static_cast<uintptr_t>(g_fxVertexCursor));
            g_fxVertexCursor += sizeof(swfGlyphVertex);
            vertex->position[0] = screenX;
            vertex->position[1] = screenY;
            vertex->position[2] = depth;
            vertex->normal[0] = normalX;
            vertex->normal[1] = normalY;
            vertex->normal[2] = normalZ;
            vertex->color = g_fxCurrentColor;
            vertex->uv[0] = u;
            vertex->uv[1] = v;
        }
    }
    g_fxVertexCount += 4;
    if (g_fxVertexCursor != 0) {
        g_fxVertexCursor = 0;
        auto* device = static_cast<uint32_t*>(g_binkVideoPlayer);
        device[0] = device[13652 / 4];
    }
    g_fxCountOnly = 0;
}
#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC pop_options
#endif

struct swfShapeFillState {
    uint32_t type;
    uint32_t color; // ARGB
    float textureMatrix[6];
    void* texture;
    void* gradient;
};

extern uint32_t swfSampleGradient(const void* gradient, float x, float y); // @ 0x824060B8
extern const float g_swfTwipScale; // @ 0x820290F0

#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC push_options
#pragma GCC optimize("fp-contract=off")
#endif
// Formerly pongShadowMap_6920_w. swfSHAPE::Render (0x82406C58) dispatches
// command 7 here; primitive 3 is a triangle list. The shape argument is unused.
// @ 0x82406920
uint32_t swfDrawShapeTriangles(const swfSHAPE*, const void* command,
                               const void* transform, const swfShapeFillState* fill) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    const auto* words = static_cast<const uint32_t*>(command);
    const uint32_t count = words[0];
    rage_2A78(3, static_cast<int32_t>(count));

    const auto* state = static_cast<const uint8_t*>(transform);
    const float* world = reinterpret_cast<const float*>(state + 24);
    const auto* multiply = reinterpret_cast<const int8_t*>(state + 56);
    const auto* add = reinterpret_cast<const int8_t*>(state + 60);
    for (int32_t i = 0; i < static_cast<int32_t>(count); ++i) {
        float x, y;
        std::memcpy(&x, words + 1 + 2 * i, sizeof(x));
        std::memcpy(&y, words + 2 + 2 * i, sizeof(y));
        const uint32_t color = fill->gradient ? swfSampleGradient(fill->gradient, x, y) : fill->color;

        uint32_t transformed = 0;
        for (unsigned channel = 0; channel < 4; ++channel) {
            // RGBA signed 2.6 multipliers and signed additions in units of four.
            const unsigned shift = channel == 3 ? 24 : 16 - channel * 8;
            int value = ((int((color >> shift) & 255) * multiply[channel]) >> 6) + int(add[channel]) * 4;
            value = value < 0 ? 0 : value > 255 ? 255 : value;
            if (channel == 3) value = value * state[71] / 255;
            transformed |= static_cast<uint32_t>(value) << shift;
        }
        g_fxCurrentColor = transformed;

        const float px = x * g_swfTwipScale;
        const float py = y * g_swfTwipScale;
        // Preserve the separate fmuls, fused second product, then translation.
        const float screenX = (std::fma(world[2], py, world[0] * px) + world[4]) * g_swfPixelScaleX;
        const float screenY = (std::fma(world[3], py, world[1] * px) + world[5]) * g_swfPixelScaleY;
        g_fxVertexU = std::fma(fill->textureMatrix[2], py, fill->textureMatrix[0] * px) + fill->textureMatrix[4];
        g_fxVertexV = std::fma(fill->textureMatrix[3], py, fill->textureMatrix[1] * px) + fill->textureMatrix[5];
        fxEmitVertex2D(screenX, screenY);
    }
    if (g_fxVertexCursor != 0) {
        g_fxVertexCursor = 0;
        auto* device = static_cast<uint32_t*>(g_binkVideoPlayer);
        device[0] = device[13652 / 4];
    }
    g_fxCountOnly = 0;
    return count * 2u + 1u;
}

// The command stream mixes float stroke/triangle coordinates with signed
// integer fan coordinates. Style indices are one-based; zero retains state.
// Mode is supplied by the instance renderer but unused by this implementation.
// @ 0x82406C58
void swfSHAPE::Render(const void* transform, int mode) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    (void)mode;
    extern void swfApplyStrokeStyle(const void* stroke, const void* transform); // @ 0x82406290
    const auto* state = static_cast<const uint8_t*>(transform);
    const auto* world = reinterpret_cast<const float*>(state + 24);
    swfShapeFillState defaultFill = {0, 0xFFFFFFFFu, {1, 0, 0, 1, 0, 0}, nullptr, nullptr};
    const swfShapeFillState* fill = &defaultFill;
    uint64_t stroke;
    auto* strokeBytes = reinterpret_cast<uint8_t*>(&stroke);
    uint16_t width = 20;
    std::memcpy(strokeBytes, &width, 2);
    const uint32_t white = 0xFFFFFFFFu;
    std::memcpy(strokeBytes + 4, &white, 4);
    std::memcpy(g_swfLineRenderState.matrix, world, 24);
    const uint32_t* command = commands;
    for (;;) {
        switch (*command++) {
        case 0:
            return;
        case 1: { // Connected polyline, including the initial point.
            swfApplyStrokeStyle(&stroke, transform);
            int32_t remaining = static_cast<int32_t>(*command++) - 1;
            const uint32_t* end = command + 2 * remaining;
            const uint32_t* point = command;
            while (remaining != 0) {
                float endpoints[4];
                std::memcpy(endpoints, point, sizeof(endpoints));
                swfDrawLine(endpoints[0], endpoints[1], endpoints[2], endpoints[3], static_cast<float>(width));
                --remaining;
                point += 2;
            }
            command = end + 2;
            break;
        }
        case 6: { // Independent pairs of endpoints.
            swfApplyStrokeStyle(&stroke, transform);
            int32_t remaining = static_cast<int32_t>(*command++);
            const uint32_t* point = command;
            command += 4 * remaining;
            while (remaining != 0) {
                float endpoints[4];
                std::memcpy(endpoints, point, sizeof(endpoints));
                swfDrawLine(endpoints[0], endpoints[1], endpoints[2], endpoints[3], static_cast<float>(width));
                --remaining;
                point += 4;
            }
            break;
        }
        case 2: case 7: {
            // Capture opcode before helpers can alter render state.
            const uint32_t opcode = command[-1];
            std::memcpy(g_swfLineRenderState.uvMatrix, fill->textureMatrix, 24);
            if (state[140] == 0) {
                g_swfBindFontTexture(fill->texture ? static_cast<void**>(fill->texture)[2] : nullptr);
            }
            if (opcode == 7) {
                command += swfDrawShapeTriangles(this, command, transform, fill);
                break;
            }
            int32_t remaining = static_cast<int32_t>(*command++);
            rage_2A78(5, remaining);
            // Retail's do/while requires a positive fan count.
            do {
                const float x = static_cast<float>(static_cast<int32_t>(command[0]));
                const float y = static_cast<float>(static_cast<int32_t>(command[1]));
                const uint32_t color = fill->gradient ? swfSampleGradient(fill->gradient, x, y) : fill->color;
                uint32_t transformed = 0;
                for (unsigned channel = 0; channel < 4; ++channel) {
                    const unsigned shift = channel == 3 ? 24 : 16 - channel * 8;
                    const int multiply = static_cast<int8_t>(state[56 + channel]);
                    const int add = static_cast<int8_t>(state[60 + channel]);
                    int value = ((int((color >> shift) & 255) * multiply) >> 6) + add * 4;
                    value = value < 0 ? 0 : value > 255 ? 255 : value;
                    if (channel == 3) value = value * state[71] / 255;
                    transformed |= uint32_t(value) << shift;
                }
                g_fxCurrentColor = transformed;
                const float px = static_cast<float>(static_cast<int32_t>(command[0])) * g_swfTwipsToPixels;
                const float py = static_cast<float>(static_cast<int32_t>(command[1])) * g_swfTwipsToPixels;
                const float* uv = g_swfLineRenderState.uvMatrix;
                const float* m = g_swfLineRenderState.matrix;
                const float v = std::fma(py, uv[3], uv[1] * px) + uv[5];
                const float u = std::fma(py, uv[2], uv[0] * px) + uv[4];
                const float screenX = std::fma(py, m[2], m[0] * px) + m[4];
                const float screenY = std::fma(py, m[3], m[1] * px) + m[5];
                g_fxVertexU = u;
                g_fxVertexV = v;
                fxEmitVertex2D(screenX * g_swfPixelScaleX, screenY * g_swfPixelScaleY);
                command += 2;
            } while (--remaining != 0);
            if (g_fxVertexCursor != 0) {
                g_fxVertexCursor = 0;
                auto* device = static_cast<uint32_t*>(g_binkVideoPlayer);
                device[0] = device[0x3554 / 4];
            }
            g_fxCountOnly = 0;
            break;
        }
        case 3:
            command += 2; // Metadata pair ignored by the renderer.
            break;
        case 4: {
            const uint32_t index = *command++;
            if (index != 0) fill = fills + index - 1;
            break;
        }
        case 5: {
            const uint32_t index = *command++;
            if (index != 0) {
                stroke = strokes[index - 1];
                std::memcpy(&width, &stroke, 2);
            }
            break;
        }
        default:
            break; // Unknown words are skipped, not treated as a terminator.
        }
    }
}

// Formerly pongShadowMap_6620_wrh: UVs follow the centerline, while position
// moves along X before the display transform. Keep each fmuls/fadds rounding.
// @ 0x82406620
void swfEmitLineVertexOffsetX(float x, float y, float offset) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    const float sx = x * g_swfTwipsToPixels;
    const float sy = y * g_swfTwipsToPixels;
    const float shiftedX = std::fma(offset, g_swfTwipsToPixels, sx);
    const float* uv = g_swfLineRenderState.uvMatrix;
    const float uProduct = uv[0] * sx;
    const float vProduct = uv[1] * sx;
    g_fxVertexU = std::fma(uv[2], sy, uProduct) + uv[4];
    g_fxVertexV = std::fma(uv[3], sy, vProduct) + uv[5];
    const float* m = g_swfLineRenderState.matrix;
    const float xProduct = m[0] * shiftedX;
    const float yProduct = m[1] * shiftedX;
    const float screenY = (std::fma(m[3], sy, yProduct) + m[5]) * g_swfPixelScaleY;
    const float screenX = (std::fma(m[2], sy, xProduct) + m[4]) * g_swfPixelScaleX;
    fxEmitVertex2D(screenX, screenY);
}

// Formerly pongShadowMap_66C8_wrh; the Y-offset counterpart of the above.
// @ 0x824066C8
void swfEmitLineVertexOffsetY(float x, float y, float offset) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    const float sx = x * g_swfTwipsToPixels;
    const float sy = y * g_swfTwipsToPixels;
    const float shiftedY = std::fma(offset, g_swfTwipsToPixels, sy);
    const float* uv = g_swfLineRenderState.uvMatrix;
    const float* m = g_swfLineRenderState.matrix;
    const float xProduct = m[0] * sx;
    const float yProduct = m[1] * sx;
    const float uProduct = uv[0] * sx;
    const float vProduct = uv[1] * sx;
    const float transformedY = std::fma(m[3], shiftedY, yProduct);
    const float transformedX = std::fma(m[2], shiftedY, xProduct);
    g_fxVertexU = std::fma(uv[2], sy, uProduct) + uv[4];
    g_fxVertexV = std::fma(uv[3], sy, vProduct) + uv[5];
    const float screenY = (transformedY + m[5]) * g_swfPixelScaleY;
    const float screenX = (transformedX + m[4]) * g_swfPixelScaleX;
    fxEmitVertex2D(screenX, screenY);
}

// Formerly pongShadowMap_6778_w. SWF shape opcodes 1 (polyline) and 6
// (independent segments) at 0x82406D6C/0x82406DDC pass endpoints and stroke width.
// Six vertices form a triangle fan with an axis-aligned cap at each endpoint.
// These descriptive names are inferred, not recovered debug symbols.
// @ 0x82406778
void swfDrawLine(float x0, float y0, float x1, float y1, float width) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    const float halfWidth = width * 0.5f;
    const float remainingWidth = width - halfWidth;
    const float dx = x1 - x0;
    const float dy = y1 - y0;
    const float absX = std::fabs(dx);
    const float absY = std::fabs(dy);
    rage_2A78(5, 6);
    if (absX > absY) {
        swfEmitLineVertexOffsetY(x0, y0, -halfWidth);
        swfEmitLineVertexOffsetY(x1, y1, -halfWidth);
        swfEmitLineVertexOffsetX(x1, y1, x1 > x0 ? remainingWidth : -remainingWidth);
        swfEmitLineVertexOffsetY(x1, y1, remainingWidth);
        swfEmitLineVertexOffsetY(x0, y0, remainingWidth);
        swfEmitLineVertexOffsetX(x0, y0, x0 < x1 ? -halfWidth : halfWidth);
    } else {
        // Equality and unordered comparisons both take this path on Xenon.
        swfEmitLineVertexOffsetX(x0, y0, -halfWidth);
        swfEmitLineVertexOffsetY(x0, y0, y0 < y1 ? -halfWidth : halfWidth);
        swfEmitLineVertexOffsetX(x0, y0, remainingWidth);
        swfEmitLineVertexOffsetX(x1, y1, remainingWidth);
        swfEmitLineVertexOffsetY(x1, y1, y1 > y0 ? remainingWidth : -remainingWidth);
        swfEmitLineVertexOffsetX(x1, y1, -halfWidth);
    }
    if (g_fxVertexCursor != 0) {
        g_fxVertexCursor = 0;
        g_fxCountOnly = 0;
        auto* device = static_cast<uint32_t*>(g_binkVideoPlayer);
        device[0] = device[13652 / 4];
    } else {
        g_fxCountOnly = 0;
    }
}
#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC pop_options
#endif

// @ 0x823FB018
void swfRebuildTransform(void* transform) {
    extern void swfMakeRotationMatrix(float* out, float degrees);  // @ 0x823FA2A0
    extern void swfConcatMatrix(float* out, const float* child, const float* parent);  // @ 0x823FA1E0
    extern float g_swfMaxShear;  // @ 0x825C8078 — shared 0.01 scale factor
    char* state = static_cast<char*>(transform);
    float* values = reinterpret_cast<float*>(state);
    float rotation[6];
    swfMakeRotationMatrix(rotation, values[19] == 0.0f ? values[18] : values[19]);
    const bool useBaseScale = values[24] == 100.0f && values[25] == 100.0f;
    float scale[6] = {
        values[useBaseScale ? 22 : 24] * g_swfMaxShear, 0.0f, 0.0f,
        values[useBaseScale ? 23 : 25] * g_swfMaxShear, 0.0f, 0.0f
    };
    float combined[6];
    swfConcatMatrix(combined, values + 28, rotation);
    swfConcatMatrix(rotation, scale, combined);
    std::memcpy(state, rotation, sizeof(rotation));
    values[4] = values[26] + values[20];
    values[5] = values[27] + values[21];
    state[0x8D] = 0;
}

namespace {
constexpr int SWF_INTERN_BUFFER_SIZE = 1024;
constexpr uint32_t SWF_ACTION_NODE_VISITED_BIT = 1;
constexpr ptrdiff_t SWF_DEFINITION_OFFSET = 0x04;
constexpr ptrdiff_t SWF_FILE_TOTAL_FRAMES_OFFSET = 0x08;
constexpr ptrdiff_t SWF_FILE_FRAME_TABLE_OFFSET = 0x0C;
constexpr ptrdiff_t SWF_FILE_RESOURCE_ARRAY_OFFSET = 0x14;
constexpr ptrdiff_t SWF_FILE_RESOURCE_COUNT_OFFSET = 0x2E;
constexpr ptrdiff_t SWF_INSTANCE_CURRENT_FRAME_OFFSET = 0xA4;
constexpr ptrdiff_t SWF_INSTANCE_IS_PLAYING_OFFSET = 0xAA;
constexpr ptrdiff_t SWF_INSTANCE_WRAP_RESET_FLAG_OFFSET = 0xAF;
constexpr ptrdiff_t SWF_INSTANCE_CHILD_LIST_OFFSET = 0xB4;
constexpr ptrdiff_t SWF_INSTANCE_NEXT_SIBLING_OFFSET = 0xB8;

struct swfValuePair {
    uint32_t data;
    uint32_t type;
};

inline void* SwfGetDefinition(const void* object) {
    return *reinterpret_cast<void* const*>(reinterpret_cast<const char*>(object) + SWF_DEFINITION_OFFSET);
}

inline uint16_t SwfGetTotalFrames(const void* fileDef) {
    return *reinterpret_cast<const uint16_t*>(reinterpret_cast<const char*>(fileDef) + SWF_FILE_TOTAL_FRAMES_OFFSET);
}

inline void* SwfGetFrameTable(const void* fileDef) {
    return *reinterpret_cast<void* const*>(reinterpret_cast<const char*>(fileDef) + SWF_FILE_FRAME_TABLE_OFFSET);
}

inline void** SwfGetResourceArray(const void* fileDef) {
    return *reinterpret_cast<void***>(const_cast<char*>(reinterpret_cast<const char*>(fileDef)) + SWF_FILE_RESOURCE_ARRAY_OFFSET);
}

inline uint16_t SwfGetResourceCount(const void* fileDef) {
    return *reinterpret_cast<const uint16_t*>(reinterpret_cast<const char*>(fileDef) + SWF_FILE_RESOURCE_COUNT_OFFSET);
}

inline uint16_t& SwfCurrentFrameRef(swfINSTANCE* instance) {
    return *reinterpret_cast<uint16_t*>(reinterpret_cast<char*>(instance) + SWF_INSTANCE_CURRENT_FRAME_OFFSET);
}

inline uint8_t& SwfIsPlayingRef(swfINSTANCE* instance) {
    return *reinterpret_cast<uint8_t*>(reinterpret_cast<char*>(instance) + SWF_INSTANCE_IS_PLAYING_OFFSET);
}

inline uint8_t& SwfWrapResetFlagRef(swfINSTANCE* instance) {
    return *reinterpret_cast<uint8_t*>(reinterpret_cast<char*>(instance) + SWF_INSTANCE_WRAP_RESET_FLAG_OFFSET);
}

inline swfINSTANCE* SwfChildList(const swfINSTANCE* instance) {
    return *reinterpret_cast<swfINSTANCE* const*>(reinterpret_cast<const char*>(instance) + SWF_INSTANCE_CHILD_LIST_OFFSET);
}

inline swfINSTANCE* SwfNextSibling(const swfINSTANCE* instance) {
    return *reinterpret_cast<swfINSTANCE* const*>(reinterpret_cast<const char*>(instance) + SWF_INSTANCE_NEXT_SIBLING_OFFSET);
}
}  // namespace

#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC push_options
#pragma GCC optimize("fp-contract=off")
#endif
// @ 0x82407C60
void swfSetTransformMatrix(void* transform, const float* matrix) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    extern double swfAsin(double value);  // @ 0x82430E88
    extern void swfMakeRotationMatrix(float* out, float degrees);  // @ 0x823FA2A0
    extern void swfConcatMatrix(float* out, const float* child, const float* parent);  // @ 0x823FA1E0
    extern float g_swfMinShear;  // @ 0x825C90C8 — shared -0.01 tolerance
    extern float g_swfMaxShear;  // @ 0x825C8078 — shared +0.01 tolerance

    // r3 is the swfINSTANCE's embedded transform (instance + 8), not the instance.
    char* state = static_cast<char*>(transform);
    for (int i = 0; i < 6; ++i) {
        std::memcpy(state + 4 * i, matrix + i, sizeof(float));
    }
    float& rotation = *reinterpret_cast<float*>(state + 0x48);
    rotation = 0.0f;
    float working[6];
    std::memcpy(working, matrix, sizeof(working));

    float c;
    float d;
    for (;;) {
        c = working[2];
        d = working[3];
        // Preserve both normalizations and the single-precision fmadds. Each
        // product outside the explicit fma rounds before the following operation.
        float negativeC = -c;
        const float dSquared = d * d;
        float lengthSquared = std::fma(negativeC, negativeC, dSquared);
        float inverseLength = lengthSquared == 0.0f ? 0.0f : 1.0f / std::sqrt(lengthSquared);
        float normalizedD = inverseLength * d;
        negativeC = inverseLength * negativeC;
        const float normalizedDSquared = normalizedD * normalizedD;
        lengthSquared = std::fma(negativeC, negativeC, normalizedDSquared);
        inverseLength = lengthSquared == 0.0f ? 0.0f : 1.0f / std::sqrt(lengthSquared);
        normalizedD = inverseLength * normalizedD;
        const float normalizedC = inverseLength * negativeC;
        const float sine = -std::fma(normalizedD, 0.0f, -normalizedC);
        const float radians = static_cast<float>(swfAsin(sine));
        const float degrees = radians * 57.2957763671875f;  // 0x82079B44
        rotation = rotation + degrees;
        // PPC bge tests !LT, so an unordered (NaN) angle also exits the loop.
        if (!(degrees > 1.0e-6f) && !(degrees < -1.0e-6f)) {
            break;
        }
        float undoRotation[6];
        swfMakeRotationMatrix(undoRotation, -degrees);
        float previous[6];
        std::memcpy(previous, working, sizeof(previous));
        swfConcatMatrix(working, previous, undoRotation);
    }

    *reinterpret_cast<float*>(state + 0x58) = working[0] * 100.0f;
    *reinterpret_cast<float*>(state + 0x5C) = d * 100.0f;
    float* residual = reinterpret_cast<float*>(state + 0x70);
    residual[1] = working[1];
    residual[2] = c;
    residual[3] = 1.0f;
    residual[0] = 1.0f;
    // The original leaves residual[4..5] intact and includes them in concat.
    if (c < g_swfMinShear || c > g_swfMaxShear || working[1] < g_swfMinShear ||
        working[1] > g_swfMaxShear) {
        float halfRotation[6];
        swfMakeRotationMatrix(halfRotation, rotation * 0.5f);
        float previous[6];
        std::memcpy(previous, residual, sizeof(previous));
        swfConcatMatrix(residual, previous, halfRotation);
    }
    // Load both before either store: matrix can point inside the transform.
    const float translationX = matrix[4];
    const float translationY = matrix[5];
    *reinterpret_cast<float*>(state + 0x50) = translationX;
    *reinterpret_cast<float*>(state + 0x54) = translationY;
    state[0x8D] = 1;
    swfRebuildTransform(transform);
}
#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC pop_options
#endif

// ===========================================================================
// swfBASE — Base class for all SWF objects
// ===========================================================================

/**
 * swfBASE::~swfBASE() @ 0x823F8A98 | size: 0x48
 * 
 * Standard RAGE destructor pattern. Sets vtable pointer then conditionally
 * frees the object if the flags parameter has bit 0 set.
 * 
 * @param flags  Bit 0 set → free this pointer after destructor runs
 */
swfBASE::~swfBASE() {
    // Vtable pointer is set by derived class destructors
}

void swfBASE_ScalarDestructor(swfBASE* obj, int flags) {
    // Set vtable to swfBASE vtable (0x82074CCC → points to 0x82074D0C + offset)
    // The lis + addi pattern: lis r11,-32249; addi r11,r11,19660
    // Calculation: (-32249 << 16) + 19660 = 0x82074D0C
    
    if (flags & 0x1) {
        rage_free(obj);
    }
}


// ===========================================================================
// swfSCRIPTOBJECT — ActionScript object representation
// ===========================================================================

/**
 * swfSCRIPTOBJECT::swfSCRIPTOBJECT() @ 0x823F8AE0 | size: 0x64
 * 
 * Constructor. Initializes the script object and links it into the global
 * script object pool. The pool is a doubly-linked list maintained in SDA.
 */
swfSCRIPTOBJECT::swfSCRIPTOBJECT() {
    // Set vtable pointer (lis r11,-32249; addi r11,r11,19732)
    // Calculation: (-32249 << 16) + 19732 = 0x82074D14
    
    // Initialize linked list pointers
    m_pNext = nullptr;  // +0x04
    m_pPrev = nullptr;  // +0x08
    
    // Link into global script object pool
    void* pool = g_swfScriptObjectPool;  // SDA offset 19540
    if (pool) {
        void* currentTail = *((void**)((char*)pool + 12));  // pool->tail
        
        // Walk to end of list
        while (currentTail) {
            void* next = *((void**)((char*)currentTail + 12));  // currentTail->next
            if (!next) break;
            currentTail = next;
        }
        
        // Link this object at the end
        if (currentTail) {
            *((void**)((char*)currentTail + 0)) = this;  // currentTail->next = this
        }
        *((void**)((char*)pool + 12)) = this;  // pool->tail = this
        
        // Increment pool count
        uint16_t count = *((uint16_t*)((char*)pool + 6));
        *((uint16_t*)((char*)pool + 6)) = count + 1;
    }
    
    // Update vtable to final swfSCRIPTOBJECT vtable
    // lis r11,-32249; addi r11,r11,19660 = 0x82074D0C
}

/**
 * swfSCRIPTOBJECT::~swfSCRIPTOBJECT() @ 0x823F8B70 | size: 0x70
 * 
 * Destructor. Calls base constructor then conditionally frees if needed.
 * Also handles unlinking from the global script object pool.
 */
swfSCRIPTOBJECT::~swfSCRIPTOBJECT() {
    // Call base constructor (sets vtable)
    // The actual unlinking from pool happens in the scalar destructor
}

/**
 * swfSCRIPTOBJECT::EnumerateMembers @ 0x823FED10 | size: 0x8
 *
 * Delegates to the SYMTAB member table at +4 for property enumeration.
 */
void swfSCRIPTOBJECT::EnumerateMembers() {
    swfSymtab_Enumerate((char*)this + 4);
}

/**
 * swfSCRIPTOBJECT::GetMemberCount @ 0x823F8B48 | size: 0x24
 *
 * Returns the number of properties on this script object by walking
 * the SYMTAB linked list at +4. Each node's next pointer is at +12.
 */
int swfSCRIPTOBJECT::GetMemberCount() {
    int count = 0;
    void* node = m_pMemberTable;
    while (node) {
        count++;
        node = *(void**)((char*)node + 12);
    }
    return count;
}

/**
 * swfSCRIPTOBJECT::VisitMembers @ 0x823FC1A0 | size: 0x8
 *
 * No-op stub — intended for garbage collection or debug traversal.
 */
int swfSCRIPTOBJECT::VisitMembers() {
    // No-op
    return 0;
}

/**
 * swfSCRIPTOBJECT::GetMember @ 0x823FBFC0 | size: 0x1DC
 *
 * ActionScript GetMember — resolves a named property on this object.
 * Special-cases "this" (returns self as type 5/object) and "prototype"
 * (returns prototype chain entry at +12, allocating from pool if needed).
 * Falls back to SYMTAB lookup on the local member table, then the global
 * object table, then the global scope chain.
 *
 * @param name   SWF value containing the property name
 * @param result Output: {value, type} pair written on success
 * @return       true if found, false otherwise
 */
uint32_t swfSCRIPTOBJECT::GetMember(const char* name, void* result) {
    extern void* g_swfStringBuffer;       // @ 0x82604850
    extern void* g_swfGlobalObject;       // @ 0x82602818
    extern void* g_swfGlobalScope;        // @ 0x8260282C
    // Convert the SWF value to a property name
    const char* interned = util_A768_1(name, &g_swfStringBuffer, SWF_INTERN_BUFFER_SIZE);

    // Special case: "this" — return self as object
    if (strcmp(interned, "this") == 0) {
        *(void**)result = this;
        *((uint32_t*)result + 1) = SWF_VALUE_OBJECT;
        return true;
    }

    // Special case: "prototype" — return prototype chain object
    if (strcmp(interned, "prototype") == 0) {
        void* proto = *(void**)((char*)this + 12);  // m_pPrototype
        if (!proto) {
            // Allocate a new prototype object from the pool
            extern void* g_swfScriptObjectPool;
            void** pool = (void**)g_swfScriptObjectPool;
            void* freeObj = *(void**)((char*)pool + 12);
            uint16_t count = *(uint16_t*)((char*)pool + 6);
            void* next = *(void**)freeObj;

            *(uint16_t*)((char*)pool + 6) = count - 1;
            *(void**)((char*)pool + 12) = next;

            if (freeObj) {
                // Initialize the new object
                extern void* g_vtable_swfSCRIPTOBJECT;  // @ 0x82074D14
                *(void**)freeObj = &g_vtable_swfSCRIPTOBJECT;
                *((uint32_t*)((char*)freeObj + 8)) = 0;
                *((uint32_t*)((char*)freeObj + 4)) = 0;
                *((uint32_t*)((char*)freeObj + 12)) = 0;
            }
            *(void**)((char*)this + 12) = freeObj;
        }
        // Return prototype
        *((uint32_t*)result + 1) = SWF_VALUE_OBJECT;
        *(void**)result = *(void**)((char*)this + 12);
        return true;
    }

    // General case: search local SYMTAB
    void* entry = swfFindMember((char*)this + 4, interned);
    if (entry) {
        *(uint32_t*)result = *(uint32_t*)entry;
        *((uint32_t*)result + 1) = *((uint32_t*)entry + 1);
        return true;
    }

    // Fallback: search global object table
    entry = swfFindMember(g_swfGlobalObject, interned);
    if (entry) {
        *(uint32_t*)result = *(uint32_t*)entry;
        *((uint32_t*)result + 1) = *((uint32_t*)entry + 1);
        return true;
    }

    // Fallback: search global scope chain
    void* scopeSymtab = (char*)g_swfGlobalScope + 4;
    entry = swfFindMember(scopeSymtab, interned);
    if (entry) {
        *(uint32_t*)result = *(uint32_t*)entry;
        *((uint32_t*)result + 1) = *((uint32_t*)entry + 1);
        return true;
    }

    return false;
}

/**
 * swfSCRIPTOBJECT::SetMember @ 0x823FC8A8 | size: 0x5C
 *
 * Converts the tagged property name, inserts its value into the member
 * table at +4, and returns status 1.
 */
uint32_t swfSCRIPTOBJECT::SetMember(const char* name, void* value) {
    extern void* g_swfStringBuffer;  // @ 0x82604850

    const char* internedName = util_A768_1(name, &g_swfStringBuffer, SWF_INTERN_BUFFER_SIZE);
    swfSetMember((char*)this + 4, internedName, static_cast<const uint32_t*>(value));
    return 1;
}

/**
 * swfSCRIPTOBJECT::DeleteMember @ 0x823FC848 | size: 0x60
 *
 * Deletes a named property. Builds an {name, 1} "undefined" pair on
 * the stack, calls GetMember (vtable slot 10) to notify watchers,
 * then removes the key from the SYMTAB.
 */
void swfSCRIPTOBJECT::DeleteMember(const char* name) {
    // Build a stack pair: {name_ptr, type=1 (undefined)}
    struct { uint32_t nameRef; uint32_t type; } undefinedPair;
    undefinedPair.nameRef = (uint32_t)(uintptr_t)name;
    undefinedPair.type = SWF_VALUE_UNDEFINED;

    // Notify via GetMember (virtual slot 10) — virtual dispatch on this
    this->GetMember((const char*)&undefinedPair, &undefinedPair);

    // Remove from symbol table
    swfSymtab_Delete((char*)this + 4, name);
}

/**
 * swfSCRIPTOBJECT::Invoke @ 0x823FEA28 | size: 0x120
 *
 * ActionScript method invocation. Looks up the named method via
 * GetMember (vtable slot 10), then dispatches based on result type:
 *   type 6: native C function — direct call with (this, args, nArgs, outResult)
 *   type 5: script object — calls Execute (vtable slot 14) on it
 *   not found: logs "Unsupported script method: %s", sets result to {0, type=3}
 *
 * For type-5 calls, checks if the call stack depth increased (indicating
 * a return value was pushed), and copies the result from the stack.
 */
void swfSCRIPTOBJECT::Invoke(const char* methodName, void* args, int argCount, void* outResult) {

    // This ABI uses a type-1 direct string and a type-7 empty lookup value;
    // swfValueType's historical enum does not describe these two tags.
    swfValuePair lookupKey = { (uint32_t)(uintptr_t)methodName, 1 };
    swfValuePair lookupResult = { 0, 7 };
    auto* resultValue = static_cast<swfValuePair*>(outResult);

    uint32_t found = this->GetMember(reinterpret_cast<const char*>(&lookupKey), &lookupResult);
    if (uint8_t(found) == 0) {
        rage_DebugLog("Unsupported script method: %s", methodName);
        *resultValue = {0, 3};
        return;
    }

    *resultValue = {0, 5};
    if (lookupResult.type == 6) {
        using NativeFunc = void (*)(void*, void*, int, void*);
        auto fn = reinterpret_cast<NativeFunc>(static_cast<uintptr_t>(lookupResult.data));
        fn(this, args, argCount, outResult);
    } else if (lookupResult.type == 5) {
        auto* callableObj = reinterpret_cast<swfACTIONFUNC*>(static_cast<uintptr_t>(lookupResult.data));
        uint32_t prevDepth = g_swfCallDepth;
        callableObj->Execute(args, argCount, this, 0);
        if (static_cast<int32_t>(g_swfCallDepth) > static_cast<int32_t>(prevDepth)) {
            swfValuePair popped;
            *resultValue = *static_cast<swfValuePair*>(swfPopResult(&popped));
        }
    }
}

void swfSCRIPTOBJECT_ScalarDestructor(swfSCRIPTOBJECT* obj, int flags) {
    // Call constructor to reset vtable
    new (obj) swfSCRIPTOBJECT();
    
    if (flags & 0x1) {
        if (obj) {
            // Unlink from global pool
            void* pool = g_swfScriptArrayPool;  // SDA offset 19552
            void* tail = *((void**)((char*)pool + 12));
            *((void**)((char*)obj + 0)) = tail;
            
            uint16_t count = *((uint16_t*)((char*)pool + 6));
            *((uint16_t*)((char*)pool + 6)) = count + 1;
            *((void**)((char*)pool + 12)) = obj;
        }
    }
}


// ===========================================================================
// swfCONTEXT — Flash execution context
// ===========================================================================

/**
 * swfCONTEXT::~swfCONTEXT() @ 0x823F8FF0 | size: 0x50
 * 
 * Destructor. Cleans up the ActionScript execution context.
 */
swfCONTEXT::~swfCONTEXT() {
    swfContext_Cleanup(this);
}

void swfCONTEXT::ScalarDestructor(int flags) {
    swfContext_Cleanup(this);
    
    if (flags & 0x1) {
        rage_free(this);
    }
}

void swfCONTEXT::Execute() {
    // External function declaration
    extern void hudFlashBase_ExecuteFromContext(void* flashObj, void* param1, void* param2);  // @ 0x823F9CA8
    extern void* g_currentSwfContext;  // @ 0x8260281C (SDA offset 10268)
    
    // Store this context as the current global context
    g_currentSwfContext = this;
    
    // Call hudFlashBase processing with internal state
    // Offsets: +24 (flashObj), +28 (param1), +32 (param2)
    void* flashObj = *((void**)((char*)this + 24));
    void* param1 = *((void**)((char*)this + 28));
    void* param2 = *((void**)((char*)this + 32));
    
    hudFlashBase_ExecuteFromContext(flashObj, param1, param2);
    
    // Clear the global context pointer
    g_currentSwfContext = nullptr;
}



// ===========================================================================
// swfFILE — SWF file representation
// ===========================================================================

/**
 * swfFILE::~swfFILE() @ 0x823F8BE0 | size: 0xDC
 * 
 * Destructor. Cleans up all resources in the SWF file including sprites,
 * fonts, shapes, and other display objects.
 */
swfFILE::~swfFILE() {
    // Set vtable pointer (lis r11,-32249; addi r11,r11,19820)
    // Calculation: (-32249 << 16) + 19820 = 0x82074D8C

    void** resourceArray = SwfGetResourceArray(this);
    uint16_t resourceCount = SwfGetResourceCount(this);

    // Destroy all child resources via virtual destructor dispatch.
    // The resource array holds pointers to swfOBJECT-derived items.
    if (resourceCount > 0) {
        for (uint16_t i = 0; i < resourceCount; i++) {
            swfOBJECT* resource = reinterpret_cast<swfOBJECT*>(resourceArray[i]);
            if (resource) {
                resource->Destroy(1);
            }
        }
    }

    if (resourceArray) {
        rage_free(resourceArray);
    }
}


// @ 0x82403628
void swfFILE::AdvanceDefinitionFrame(swfINSTANCE* instance) {
    auto* file = reinterpret_cast<uint8_t*>(this);
    auto* state = reinterpret_cast<uint8_t*>(instance);
    *reinterpret_cast<swfINSTANCE**>(file + 0x10) = instance;

    const bool playing = state[0xAA] != 0;
    if (playing) {
        swfDispatchClipEvents(instance, 2, lbl_82074EF0);
    }

    auto* frames = *reinterpret_cast<uint8_t**>(file + 0x0C);
    uint16_t frame = *reinterpret_cast<uint16_t*>(state + 0xA4);
    void* command = *reinterpret_cast<void**>(frames + frame * 8 + 4);
    while (command) {
        void** vtable = *reinterpret_cast<void***>(command);
        using CommandFn = void (*)(void*, swfINSTANCE*);
        reinterpret_cast<CommandFn>(vtable[playing ? 1 : 3])(command, instance);
        command = *reinterpret_cast<void**>(static_cast<uint8_t*>(command) + 0x0C);
    }

    if (state[0xAC]) {
        state[0xAA] = 0;
        state[0xAC] = 0;
    }
    if (state[0xAB]) {
        state[0xAB] = 0;
        state[0xAA] = 1;
    }
    if (state[0xAA]) {
        void** vtable = *reinterpret_cast<void***>(instance);
        using AdvanceFn = void (*)(swfINSTANCE*, int);
        reinterpret_cast<AdvanceFn>(vtable[2])(instance, 0);
    }
}


/**
 * swfCMD::~swfCMD() @ 0x82407E90 | size: 0x48
 * 
 * Base destructor for SWF command objects. Sets vtable and conditionally
 * frees the object if the flags parameter has bit 0 set.
 */

swfCMD::~swfCMD() {
    // Vtable is set by derived destructors
}

void swfCMD_ScalarDestructor(swfCMD* obj, int flags) {
    if (flags & 0x1) {
        rage_free(obj);
    }
}

/**
 * swfCMD_DoAction::~swfCMD_DoAction() @ 0x82407ED8 | size: 0x88
 * 
 * Destructor for DoAction command. Decrements reference count on the
 * ActionScript bytecode buffer and frees it when count reaches zero.
 */
swfCMD_DoAction::~swfCMD_DoAction() {
    // Access the bytecode buffer at offset +16
    void* bytecodeBuffer = *((void**)((char*)this + 16));
    
    if (bytecodeBuffer) {
        // Decrement reference count (uint16_t at offset +0 of buffer)
        uint16_t* refCountPtr = (uint16_t*)bytecodeBuffer;
        uint16_t refCount = *refCountPtr;
        
        // Decrement: (refCount + 0x10000 - 1) & 0xFFFF
        refCount = (refCount - 1) & 0xFFFF;
        *refCountPtr = refCount;
        
        // Free buffer if refcount reached zero
        if (refCount == 0) {
            rage_free(bytecodeBuffer);
        }
    }
}

void swfCMD_DoAction_ScalarDestructor(swfCMD_DoAction* obj, int flags) {
    // Call destructor
    obj->~swfCMD_DoAction();
    
    if (flags & 0x1) {
        rage_free(obj);
    }
}

/**
 * swfCMD_DoInitAction::~swfCMD_DoInitAction() @ 0x82407F60 | size: 0x88
 * 
 * Destructor for DoInitAction command. Same pattern as DoAction - decrements
 * reference count on the ActionScript initialization bytecode buffer.
 */
swfCMD_DoInitAction::~swfCMD_DoInitAction() {
    // Access the bytecode buffer at offset +16
    void* bytecodeBuffer = *((void**)((char*)this + 16));
    
    if (bytecodeBuffer) {
        // Decrement reference count (uint16_t at offset +0 of buffer)
        uint16_t* refCountPtr = (uint16_t*)bytecodeBuffer;
        uint16_t refCount = *refCountPtr;
        
        // Decrement: (refCount + 0x10000 - 1) & 0xFFFF
        refCount = (refCount - 1) & 0xFFFF;
        *refCountPtr = refCount;
        
        // Free buffer if refcount reached zero
        if (refCount == 0) {
            rage_free(bytecodeBuffer);
        }
    }
}

void swfCMD_DoInitAction_ScalarDestructor(swfCMD_DoInitAction* obj, int flags) {
    // Call destructor
    obj->~swfCMD_DoInitAction();
    
    if (flags & 0x1) {
        rage_free(obj);
    }
}

/**
 * swfCMD_PlaceObject2::~swfCMD_PlaceObject2() @ 0x82407FF0 | size: 0x74
 * 
 * Destructor for PlaceObject2 command. Frees two allocated buffers
 * (likely color transform and matrix data).
 */
swfCMD_PlaceObject2::~swfCMD_PlaceObject2() {
    // Free color transform buffer at offset +24
    void* colorTransform = *((void**)((char*)this + 24));
    if (colorTransform) {
        rage_free(colorTransform);
    }
    
    // Free matrix buffer at offset +28
    void* matrix = *((void**)((char*)this + 28));
    if (matrix) {
        rage_free(matrix);
    }
}

void swfCMD_PlaceObject2_ScalarDestructor(swfCMD_PlaceObject2* obj, int flags) {
    // Call destructor
    obj->~swfCMD_PlaceObject2();
    
    if (flags & 0x1) {
        rage_free(obj);
    }
}

// @ 0x824081B0
void swfCMD_PlaceObject2::Execute(swfINSTANCE* parent) {
    extern void* g_swfCurrentFile;  // @ 0x82602838
    auto* command = reinterpret_cast<uint8_t*>(this);
    auto* container = reinterpret_cast<uint8_t*>(parent);
    const uint16_t resourceIndex = *reinterpret_cast<uint16_t*>(command + 0x14);
    uint8_t* child;
    if (resourceIndex != 0xFFFF) {
        auto* file = static_cast<uint8_t*>(g_swfCurrentFile);
        auto** resources = *reinterpret_cast<void***>(file + 0x14);
        void** vtable = *reinterpret_cast<void***>(parent);
        using PlaceFn = swfINSTANCE* (*)(swfINSTANCE*, uint32_t, uint32_t, void*);
        child = reinterpret_cast<uint8_t*>(reinterpret_cast<PlaceFn>(vtable[7])(
            parent, *reinterpret_cast<uint16_t*>(command + 0x10),
            *reinterpret_cast<uint16_t*>(command + 0x12), resources[resourceIndex]));
    } else {
        // A move-only tag searches the sorted display list without creating a child.
        const uint16_t depth = *reinterpret_cast<uint16_t*>(command + 0x10);
        child = *reinterpret_cast<uint8_t**>(container + 0xB4);
        while (child && *reinterpret_cast<uint16_t*>(child + 0xA6) < depth) {
            child = *reinterpret_cast<uint8_t**>(child + 0xB8);
        }
        if (child && *reinterpret_cast<uint16_t*>(child + 0xA6) != depth) {
            child = nullptr;
        }
    }
    if (!child) {
        rage_DebugLog(reinterpret_cast<const char*>(0x820755A4),
                      *reinterpret_cast<const char**>(container + 0xBC),
                      *reinterpret_cast<uint16_t*>(command + 0x10));
        return;
    }

    child[0xAF] = 1;
    const int16_t* packed = *reinterpret_cast<const int16_t**>(command + 0x18);
    if (packed) {
        // Optional signed 8.8 scale/shear pairs, followed by signed twip translation.
        const uint8_t flags = command[5];
        unsigned int index = 0;
        float matrix[6];
        if (flags & 1) {
            matrix[0] = static_cast<float>(packed[index++]) * 0.00390625f;
            matrix[3] = static_cast<float>(packed[index++]) * 0.00390625f;
        } else {
            matrix[0] = matrix[3] = 1.0f;
        }
        if (flags & 2) {
            matrix[1] = static_cast<float>(packed[index++]) * 0.00390625f;
            matrix[2] = static_cast<float>(packed[index++]) * 0.00390625f;
        } else {
            matrix[1] = matrix[2] = 0.0f;
        }
        matrix[4] = static_cast<float>(packed[index++]) * 0.05f;
        matrix[5] = static_cast<float>(packed[index]) * 0.05f;
        swfSetTransformMatrix(child + 8, matrix);
    }
    const void* color = *reinterpret_cast<void**>(command + 0x1C);
    if (color) {
        // The PPC loads all eight bytes before storing, including when source aliases child.
        uint64_t value;
        std::memcpy(&value, color, sizeof(value));
        std::memcpy(child + 0x38, &value, sizeof(value));
    }
}

// @ 0x824083D8
void swfCMD_PlaceObject2ClipEvent::Execute(swfINSTANCE* parent) {
    auto* command = reinterpret_cast<uint8_t*>(this);
    reinterpret_cast<swfCMD_PlaceObject2*>(this)->Execute(parent);

    const uint16_t depth = *reinterpret_cast<uint16_t*>(command + 0x10);
    auto* child = *reinterpret_cast<uint8_t**>(reinterpret_cast<uint8_t*>(parent) + 0xB4);
    while (child && *reinterpret_cast<uint16_t*>(child + 0xA6) < depth) {
        child = *reinterpret_cast<uint8_t**>(child + 0xB8);
    }
    if (!child || *reinterpret_cast<uint16_t*>(child + 0xA6) != depth) return;

    if (*reinterpret_cast<uint16_t*>(command + 0x14) != 0xFFFF &&
        *reinterpret_cast<void**>(command + 0x2C)) {
        struct Value { void* data; uint32_t type; };
        Value name = {*reinterpret_cast<void**>(command + 0x2C), 1};
        Value value = {child, 5};
        auto** vtable = *reinterpret_cast<void***>(parent);
        using SetMember = uint32_t (*)(swfINSTANCE*, const Value*, const Value*);
        reinterpret_cast<SetMember>(vtable[11])(parent, &name, &value);
        *reinterpret_cast<void**>(child + 0xBC) = *reinterpret_cast<void**>(command + 0x2C);
    }
    swfSetClipEvents(child, *reinterpret_cast<uint32_t*>(command + 0x20),
                     *reinterpret_cast<uint32_t*>(command + 0x28),
                     *reinterpret_cast<int32_t*>(command + 0x24));
    swfDispatchClipEvents(child, 1, lbl_82074EE4);
}

// Guest vtable slot 3 reapplies events without executing the placement command.
// @ 0x824084B0
void swfCMD_PlaceObject2ClipEvent::UpdateClipEvents(swfINSTANCE* parent) {
    const auto* command = reinterpret_cast<const uint8_t*>(this);
    const uint16_t depth = *reinterpret_cast<const uint16_t*>(command + 0x10);
    auto* child = *reinterpret_cast<uint8_t**>(reinterpret_cast<uint8_t*>(parent) + 0xB4);
    while (child && *reinterpret_cast<uint16_t*>(child + 0xA6) < depth) {
        child = *reinterpret_cast<uint8_t**>(child + 0xB8);
    }
    if (!child || *reinterpret_cast<uint16_t*>(child + 0xA6) != depth) return;

    swfSetClipEvents(child, *reinterpret_cast<const uint32_t*>(command + 0x20),
                     *reinterpret_cast<const uint32_t*>(command + 0x28),
                     *reinterpret_cast<const int32_t*>(command + 0x24));
    swfDispatchClipEvents(child, 2, lbl_82074EF0);
}

/**
 * swfCMD_PlaceObject2ClipEvent::~swfCMD_PlaceObject2ClipEvent() @ 0x82408160 | size: 0x50
 * 
 * Destructor for PlaceObject2 clip event. Calls cleanup helper first.
 */
swfCMD_PlaceObject2ClipEvent::~swfCMD_PlaceObject2ClipEvent() {
    // Call cleanup helper (frees event handler list)
    extern void swfPlaceObject2ClipEvent_Cleanup(void* ptr);  // @ 0x82408068
    swfPlaceObject2ClipEvent_Cleanup(this);
}

void swfCMD_PlaceObject2ClipEvent_ScalarDestructor(swfCMD_PlaceObject2ClipEvent* obj, int flags) {
    // Call destructor
    obj->~swfCMD_PlaceObject2ClipEvent();
    
    if (flags & 0x1) {
        rage_free(obj);
    }
}


/**
 * swfCMD_DoInitAction::Cleanup() @ 0x821EFC00 | size: 0x10
 * 
 * Virtual function slot 2 - tail calls to scalar destructor (slot 1).
 * This is a common RAGE pattern for cleanup functions.
 */
void swfCMD_DoInitAction::Cleanup() {
    // Tail-calls the scalar destructor (vtable slot 1) with flags=0
    // (destroy object contents but do not free the allocation).
    // Slot 1 is the compiler-synthesised scalar dtor, not declared in
    // the class header — retain explicit vtable indirection.
    void** vtable = *((void***)this);
    typedef void (*ScalarDtorFn)(swfCMD_DoInitAction*, int);
    ((ScalarDtorFn)vtable[1])(this, 0);
}



/**
 * swfFILE::FindExportFrame @ 0x823F9DC8 | size: 0xBC
 *
 * Searches the file's export/label table for a named frame label.
 * The export array is at +20, count at +46. Each entry with type
 * byte == 5 (at entry+4) has a name string at entry+192.
 * Comparison is case-insensitive via _stricmp.
 *
 * If found, computes the frame-relative position by calling a helper
 * that returns a normalized float, then scales by a global factor
 * and the input frameRate. If not found, logs an error and returns 0.0f.
 *
 * @param frameRate   Input time scale (passed in f1)
 * @param labelName   Frame label to search for
 * @param context     Timeline context for position computation
 * @return            Frame position scaled by frameRate, or 0.0f if not found
 */
float swfFILE::FindExportFrame(float frameRate, const char* labelName, void* context) {

    uint16_t exportCount = *(uint16_t*)((char*)this + 46);
    void** exportArray = *(void***)((char*)this + 20);

    for (int i = 0; i < exportCount; i++) {
        void* entry = exportArray[i];
        if (!entry) continue;

        uint8_t entryType = *(uint8_t*)((char*)entry + 4);
        if (entryType != 5) continue;

        const char* entryName = (const char*)((char*)entry + 192);
        if (_stricmp(entryName, labelName) == 0) {
            // Found — compute frame position and scale
            float outMin, outMax;
            float basePosition = swfComputeFramePosition(context, entry, &outMin, &outMax);
            // Scale: basePosition * globalFrameScale * inputFrameRate
            extern float g_swfFrameScale;  // @ 0x82079B90
            return basePosition * g_swfFrameScale * frameRate;
        }
    }

    // Not found — log and return zero
    // Error string @ 0x82076C80: "Couldn't find font with which..."
    // (reused for "not found" in this context)
    rage_DebugLog("Couldn't find frame label '%s'", labelName);
    return 0.0f;
}


// ===========================================================================
// swfINSTANCE — Flash display object instance
// ===========================================================================

/**
 * swfINSTANCE::~swfINSTANCE() @ 0x823FB600 | size: 0x70
 * 
 * Destructor. Cleans up a Flash display object instance and unlinks it
 * from the instance pool.
 */
swfINSTANCE::~swfINSTANCE() {
    swfInstance_Cleanup(this);
}

void swfINSTANCE_ScalarDestructor(swfINSTANCE* obj, int flags) {
    swfInstance_Cleanup(obj);
    
    if (flags & 0x1) {
        if (obj) {
            // Unlink from global instance pool
            void* pool = g_swfInstancePool;  // SDA offset 19536
            void* tail = *((void**)((char*)pool + 12));
            *((void**)((char*)obj + 0)) = tail;
            
            uint16_t count = *((uint16_t*)((char*)pool + 6));
            *((uint16_t*)((char*)pool + 6)) = count + 1;
            *((void**)((char*)pool + 12)) = obj;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// swfINSTANCE — Flash display list instance (MovieClip)
//
// Memory layout (key fields):
//   +0x00: vtable          +0x04: m_pDefinition (swfFILE/sprite def)
//   +0x48: m_pActionList    +0xA0: m_pSprite (child sprite/shape)
//   +0xA4: m_currentFrame   +0xA6: m_depth
//   +0xA8: m_clipDepth      +0xAA: m_bIsPlaying (bool)
//   +0xAB: m_bDirty         +0xAC: m_bVisible
//   +0xB0: m_pParent        +0xB4: m_pChildList
//   +0xB8: m_pNextSibling
// ─────────────────────────────────────────────────────────────────────────────

/**
 * swfINSTANCE::GotoFrame @ 0x823FB7A8 | size: 0xF8
 *
 * Advances the timeline to target frame, executing frame commands along
 * the way. Out-of-range targets are ignored. Stepping past the last frame
 * wraps to 0 and clears child flags at +0xAF. On each step, executes the
 * frame's command list (DoAction tags) if skipActions==0.
 */
void swfINSTANCE::GotoFrame(uint32_t targetFrame, uint32_t skipActions) {
    targetFrame = static_cast<uint16_t>(targetFrame);
    skipActions = static_cast<uint8_t>(skipActions);
    void* def = SwfGetDefinition(this);
    uint16_t totalFrames = SwfGetTotalFrames(def);

    if (targetFrame >= totalFrames) return;

    uint16_t& currentFrame = SwfCurrentFrameRef(this);
    uint16_t curFrame = currentFrame;
    if (curFrame == targetFrame) return;

    while (curFrame != targetFrame) {
        uint16_t nextFrame = (currentFrame + 1) & 0xFFFF;
        uint16_t maxFrames = SwfGetTotalFrames(SwfGetDefinition(this));

        if (nextFrame >= maxFrames) {
            for (swfINSTANCE* child = SwfChildList(this); child; child = SwfNextSibling(child)) {
                SwfWrapResetFlagRef(child) = 0;
            }
            nextFrame = 0;
        }
        currentFrame = nextFrame;

        if (skipActions == 0) {
            void* curDef2 = SwfGetDefinition(this);
            uint16_t frameIdx = currentFrame;
            void* frameTable = SwfGetFrameTable(curDef2);
            void* cmdList = *(void**)((char*)frameTable + frameIdx * 8 + 4);
            while (cmdList) {
                typedef void (*ExecFunc)(void*, swfINSTANCE*);
                void** cmdVtable = *(void***)cmdList;
                ExecFunc exec = (ExecFunc)cmdVtable[2];
                exec(cmdList, this);
                cmdList = *(void**)((char*)cmdList + 12);
            }
        } else {
            void* curDef2 = SwfGetDefinition(this);
            typedef void (*DefExecFunc)(void*, swfINSTANCE*);
            void** defVtable = *(void***)curDef2;
            DefExecFunc defExec = (DefExecFunc)defVtable[2];
            defExec(curDef2, this);
        }

        curFrame = currentFrame;
    }
}

/**
 * swfINSTANCE::NextFrame @ 0x823FB8A0 | size: 0x80
 *
 * Advances to next frame with wrapping. Saves and restores the
 * m_bIsPlaying flag, calling GotoFrame with play=true.
 */
void swfINSTANCE::NextFrame(void* context) {
    uint16_t curFrame = SwfCurrentFrameRef(this);
    uint16_t nextFrame = (curFrame + 1) & 0xFFFF;
    uint16_t maxFrames = SwfGetTotalFrames(SwfGetDefinition(this));

    if (nextFrame >= maxFrames) {
        nextFrame = 0;
    }

    uint8_t& isPlaying = SwfIsPlayingRef(this);
    uint8_t savedPlaying = isPlaying;
    isPlaying = 1;

    // Retail dispatches slot 1 and forwards the full context register.
    using GotoFrameFn = void (*)(swfINSTANCE*, uint32_t, void*);
    void** vtable = *reinterpret_cast<void***>(this);
    reinterpret_cast<GotoFrameFn>(vtable[1])(this, nextFrame, context);

    isPlaying = savedPlaying;
}

/**
 * swfINSTANCE::PrevFrame @ 0x823FB920 | size: 0x50
 *
 * Goes to previous frame. If at frame 0, wraps to last frame.
 * Calls GotoFrame (vtable slot 1) with stop flag.
 */
void swfINSTANCE::PrevFrame() {
    uint16_t curFrame = SwfCurrentFrameRef(this);

    if (curFrame == 0) {
        uint16_t maxFrames = SwfGetTotalFrames(SwfGetDefinition(this));
        uint16_t lastFrame = (maxFrames + 0x10000 - 1) & 0xFFFF;
        this->GotoFrame(lastFrame, 0);
    } else {
        uint16_t prevFrame = (curFrame + 0x10000 - 1) & 0xFFFF;
        this->GotoFrame(prevFrame, 0);
    }
}

/**
 * swfINSTANCE::MarkDirty @ 0x823FB760 | size: 0x48
 *
 * Sets the dirty flag (+171) to 1. If the parent sprite at +176 exists
 * and its definition type byte is not 2 (shape), calls the sprite's
 * Advance method (vtable slot 4).
 */
void swfINSTANCE::MarkDirty() {
    *(uint8_t*)((char*)this + 171) = 1;  // m_bDirty = true

    // Parent is another display-list instance (swfINSTANCE).
    swfINSTANCE* parentSprite = *(swfINSTANCE**)((char*)this + 176);
    if (!parentSprite) return;

    void* memberTable = *(void**)((char*)this + 4);
    if (!memberTable) return;

    uint8_t defType = *(uint8_t*)((char*)memberTable + 4);
    if (defType == 2) return;  // shapes don't need advance

    // Call parent's MarkDirty (virtual slot 4) via virtual dispatch
    parentSprite->MarkDirty();
}

/**
 * swfINSTANCE::SetVisible @ 0x823FB150 | size: 0x8
 *
 * Sets the visibility flag at +172 to true.
 */
void swfINSTANCE::SetVisible() {
    *(uint8_t*)((char*)this + 172) = 1;
}

/**
 * swfINSTANCE::EnumerateMembers @ 0x823FED18 | size: 0xBC
 *
 * Recursively enumerates all members: calls EnumerateMembers (vtable
 * slot 6) on the next sibling (+184), child list (+180), and sprite
 * (+160). Also walks the action list at +72, setting bit 0 of each
 * node's flags (+12).
 */
void swfINSTANCE::EnumerateMembers() {
    // Enumerate next sibling (another swfINSTANCE on the display list)
    swfINSTANCE* sibling = *(swfINSTANCE**)((char*)this + 184);
    if (sibling) {
        sibling->EnumerateMembers();
    }

    // Enumerate child list (head of children, also a swfINSTANCE)
    swfINSTANCE* childList = *(swfINSTANCE**)((char*)this + 180);
    if (childList) {
        childList->EnumerateMembers();
    }

    // Enumerate attached sprite/definition at +160.
    // This is a swfSCRIPTOBJECT-derived resource (sprite definition).
    swfSCRIPTOBJECT* sprite = *(swfSCRIPTOBJECT**)((char*)this + 160);
    if (sprite) {
        sprite->EnumerateMembers();
    }

    // Walk action list and set the visited bit without clobbering the next link.
    void* actionNode = *(void**)((char*)this + 72);
    while (actionNode) {
        void* nextNode = *(void**)((char*)actionNode + 12);
        *(uint32_t*)((char*)actionNode + 12) = ((uint32_t)(uintptr_t)nextNode) | SWF_ACTION_NODE_VISITED_BIT;
        actionNode = nextNode;
    }
}

/**
 * swfINSTANCE::GetMemberCount @ 0x823FB160 | size: 0x28
 *
 * Returns member count by delegating to the sprite at +160.
 * If no sprite, returns 0.
 */
int swfINSTANCE::GetMemberCount() {
    swfSCRIPTOBJECT* sprite = *(swfSCRIPTOBJECT**)((char*)this + 160);
    if (!sprite) return 0;

    // Virtual GetMemberCount (slot 8) via virtual dispatch
    return sprite->GetMemberCount();
}

/**
 * swfINSTANCE::VisitMembers @ 0x823FBF98 | size: 0x28
 *
 * Delegates to sprite at +160's VisitMembers (vtable slot 9).
 * If no sprite, returns 0.
 */
int swfINSTANCE::VisitMembers() {
    swfSCRIPTOBJECT* sprite = *(swfSCRIPTOBJECT**)((char*)this + 160);
    if (!sprite) return 0;

    // Virtual VisitMembers (slot 9) via virtual dispatch
    return sprite->VisitMembers();
}

/**
 * swfACTIONFUNC::SetMember() @ 0x823FF4A0 | size: 0x14
 * 
 * Virtual function slot 11 - forwards to inner object's SetMember.
 * The inner object is stored at offset +7332.
 */
uint32_t swfACTIONFUNC::SetMember(const char* name, void* value) {
    swfINSTANCE* innerObj = *reinterpret_cast<swfINSTANCE**>(reinterpret_cast<char*>(this) + 0x1CA4);
    using Setter = uint32_t (*)(swfINSTANCE*, const char*, void*);
    void** vtable = *reinterpret_cast<void***>(innerObj);
    return reinterpret_cast<Setter>(vtable[11])(innerObj, name, value);
}

/**
 * swfACTIONFUNC::DeleteMember() @ 0x823FF4B8 | size: 0x14
 *
 * Virtual function slot 12 - forwards to inner object's DeleteMember.
 */
void swfACTIONFUNC::DeleteMember(const char* name) {
    // Forward to inner MovieClip's DeleteMember (virtual slot 12).
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) {
        innerObj->DeleteMember(name);
    }
}


// swfINSTANCE slot 10 @ 0x823FB970: display properties and script fallback.
// The shared declaration calls r4 a const char*, but the game passes an SWF
// {value, type} key. Convert it before comparing or forwarding the property name.
uint32_t swfINSTANCE::GetMember(const char* name, void* result) {
    extern void* g_swfStringBuffer;        // @ 0x82604850
    extern void* g_swfRootObject;          // @ 0x82602828
    extern void* g_swfGlobalScope;         // @ 0x8260282C
    extern void* g_swfScriptObjectPool;    // @ 0x82604C60
    extern void* g_vtable_swfSCRIPTOBJECT; // @ 0x82074D14

    const char* property = util_A768_1(name, &g_swfStringBuffer, SWF_INTERN_BUFFER_SIZE);
    char* instance = reinterpret_cast<char*>(this);
    uint32_t& type = *(reinterpret_cast<uint32_t*>(result) + 1);

    if (strcmp(property, "this") == 0) {
        *reinterpret_cast<void**>(result) = this;
        type = 5;
        return true;
    }
    if (strcmp(property, "_root") == 0) {
        *reinterpret_cast<void**>(result) = g_swfRootObject;
        type = 5;
        return true;
    }
    if (strcmp(property, "_global") == 0) {
        *reinterpret_cast<void**>(result) = g_swfGlobalScope;
        type = 5;
        return true;
    }
    if (strcmp(property, "textColor") == 0) {
        const uint8_t* color = reinterpret_cast<const uint8_t*>(instance + 0x4C);
        *reinterpret_cast<uint32_t*>(result) = (uint32_t(color[0]) << 16)
                                            | (uint32_t(color[1]) << 8) | color[2];
        type = 3;
        return true;
    }
    if (strcmp(property, "_parent") == 0) {
        void* parent = *reinterpret_cast<void**>(instance + 0xB0);
        *reinterpret_cast<void**>(result) = parent ? parent : this;
        type = 5;
        return true;
    }
    if (strcmp(property, "onEnterFrame") == 0) {
        *reinterpret_cast<void**>(result) = *reinterpret_cast<void**>(instance + 0xCC);
        type = 5;
        return true;
    }
    if (strcmp(property, "_name") == 0) {
        *reinterpret_cast<void**>(result) = *reinterpret_cast<void**>(instance + 0xBC);
        type = 1;
        return true;
    }

    // Tag 4 is a single-precision number here; set it even for delegated lookups.
    type = 4;
    if (strcmp(property, "_x") == 0) {
        *reinterpret_cast<float*>(result) = *reinterpret_cast<float*>(instance + 0x70);
        return true;
    }
    if (strcmp(property, "_y") == 0) {
        *reinterpret_cast<float*>(result) = *reinterpret_cast<float*>(instance + 0x74);
        return true;
    }
    if (strcmp(property, "_width") == 0) {
        *reinterpret_cast<float*>(result) = util_EF98(this, 0);
        return true;
    }
    if (strcmp(property, "_height") == 0) {
        *reinterpret_cast<float*>(result) = swfINSTANCE_F0D8_w(this, 0);
        return true;
    }
    if (strcmp(property, "_xscale") == 0) {
        *reinterpret_cast<float*>(result) = *reinterpret_cast<float*>(instance + 0x68);
        return true;
    }
    if (strcmp(property, "_yscale") == 0) {
        *reinterpret_cast<float*>(result) = *reinterpret_cast<float*>(instance + 0x6C);
        return true;
    }
    if (strcmp(property, "_alpha") == 0) {
        // Preserve both single-precision multiplies (100, then 1/255).
        float alpha = float(*reinterpret_cast<uint8_t*>(instance + 0x4F)) * 100.0f;
        *reinterpret_cast<float*>(result) = alpha * (1.0f / 255.0f);
        return true;
    }
    if (strcmp(property, "_rotation") == 0) {
        *reinterpret_cast<float*>(result) = *reinterpret_cast<float*>(instance + 0x54);
        return true;
    }

    // Use the game's slots: C++ virtual ordering in this header is different.
    using DefinitionLookup = uint32_t (*)(void*, const char*, void*);
    void* definition = SwfGetDefinition(this);
    void** definitionVtable = *reinterpret_cast<void***>(definition);
    if (uint8_t(reinterpret_cast<DefinitionLookup>(definitionVtable[4])(definition, property, result))) {
        return true;
    }

    using ScriptLookup = uint32_t (*)(void*, const swfValuePair*, void*);
    swfValuePair key = {uint32_t(reinterpret_cast<uintptr_t>(property)), 1};
    void*& script = *reinterpret_cast<void**>(instance + 0xA0);
    if (script) {
        void** vtable = *reinterpret_cast<void***>(script);
        if (uint8_t(reinterpret_cast<ScriptLookup>(vtable[10])(script, &key, result))) {
            return true;
        }
    }

    // A failed lookup replaces even an existing script object with a fresh one.
    // The pool must have a free node; the original dereferences its head unconditionally.
    char* pool = reinterpret_cast<char*>(g_swfScriptObjectPool);
    void* object = *reinterpret_cast<void**>(pool + 12);
    void* next = *reinterpret_cast<void**>(object);
    --*reinterpret_cast<uint16_t*>(pool + 6);
    *reinterpret_cast<void**>(pool + 12) = next;
    *reinterpret_cast<void**>(object) = &g_vtable_swfSCRIPTOBJECT;
    *reinterpret_cast<uint32_t*>(reinterpret_cast<char*>(object) + 8) = 0;
    *reinterpret_cast<uint32_t*>(reinterpret_cast<char*>(object) + 4) = 0;
    *reinterpret_cast<uint32_t*>(reinterpret_cast<char*>(object) + 12) = 0;
    script = object;
    void** vtable = *reinterpret_cast<void***>(script);
    return reinterpret_cast<ScriptLookup>(vtable[10])(script, &key, result);
}

// swfINSTANCE slot 11 @ 0x823FC1A8: display writes and script fallback.
// As in GetMember, name points to an 8-byte SWF value, not a C string.
uint32_t swfINSTANCE::SetMember(const char* name, void* value) {
    extern void* g_swfStringBuffer;        // @ 0x82604850
    extern void* g_swfScriptObjectPool;    // @ 0x82604C60
    extern void* g_vtable_swfSCRIPTOBJECT; // @ 0x82074D14
    extern void swfReleaseText(void* text, int freeStorage); // @ 0x823F8A38
    extern void* swfCopyText(const char* text); // @ 0x823FABC0
    extern void* swfFindTexture(void* dictionary, const char* name); // @ 0x82151990
    extern double swfRotationRemainder(double angle, double period); // @ 0x82431D78

    const char* property = util_A768_1(name, &g_swfStringBuffer, SWF_INTERN_BUFFER_SIZE);
    char* instance = reinterpret_cast<char*>(this);

    if (strcmp(property, "_x") == 0) {
        *reinterpret_cast<float*>(instance + 0x70) = swfValueToFloat(value);
        instance[0x95] = 1;
        return 1;
    }
    if (strcmp(property, "_y") == 0) {
        *reinterpret_cast<float*>(instance + 0x74) = swfValueToFloat(value);
        instance[0x95] = 1;
        return 1;
    }
    if (strcmp(property, "_xscale") == 0) {
        *reinterpret_cast<float*>(instance + 0x68) = swfValueToFloat(value);
        instance[0x95] = 1;
        return 1;
    }
    if (strcmp(property, "_yscale") == 0) {
        *reinterpret_cast<float*>(instance + 0x6C) = swfValueToFloat(value);
        instance[0x95] = 1;
        return 1;
    }
    if (strcmp(property, "text") == 0) {
        char buffer[256];
        const char* text = util_A768_1(value, buffer, sizeof(buffer));
        void*& oldText = *reinterpret_cast<void**>(instance + 0x48);
        if (oldText) swfReleaseText(oldText, 1);
        oldText = swfCopyText(text);
        return 1;
    }
    if (strcmp(property, "_alpha") == 0) {
        // Xenon wraps the integer product before signed division by 100;
        // the byte store wraps again, without clamping to [0, 255].
        uint32_t alpha = static_cast<uint32_t>(swfValueToInteger(value));
        int32_t scaled = static_cast<int32_t>((alpha << 8) - alpha);
        instance[0x4F] = static_cast<uint8_t>(scaled / 100);
        return 1;
    }
    if (strcmp(property, "textColor") == 0) {
        uint32_t color = static_cast<uint32_t>(swfValueToInteger(value));
        instance[0x4C] = static_cast<uint8_t>(color >> 16);
        instance[0x4D] = static_cast<uint8_t>(color >> 8);
        instance[0x4E] = static_cast<uint8_t>(color);
        return 1;
    }
    if (strcmp(property, "_rotation") == 0) {
        float angle = swfValueToFloat(value);
        *reinterpret_cast<float*>(instance + 0x54) =
            static_cast<float>(swfRotationRemainder(angle, 360.0));
        instance[0x95] = 1;
        return 1;
    }
    if (strcmp(property, "__texturename") == 0) {
        // This branch uses the payload directly, without converting the value.
        const swfValuePair* pair = static_cast<const swfValuePair*>(value);
        const char* texture = reinterpret_cast<const char*>(static_cast<uintptr_t>(pair->data));
        *reinterpret_cast<void**>(instance + 0x90) = swfFindTexture(g_sda_6404, texture);
        return 1;
    }
    if (strcmp(property, "__drawcallback") == 0) {
        *reinterpret_cast<int32_t*>(instance + 0x98) = swfValueToInteger(value);
        return 1;
    }
    if (strcmp(property, "_seamFix") == 0) {
        instance[0x9C] = swfValueToInteger(value) > 0;
        return 1;
    }
    if (strcmp(property, "onEnterFrame") == 0) {
        const swfValuePair* pair = static_cast<const swfValuePair*>(value);
        *reinterpret_cast<uint32_t*>(instance + 0xCC) = pair->type == 5 ? pair->data : 0;
        return 1;
    }
    if (strcmp(property, "onRelease") == 0) {
        const swfValuePair* pair = static_cast<const swfValuePair*>(value);
        *reinterpret_cast<uint32_t*>(instance + 0xD0) = pair->type == 5 ? pair->data : 0;
        return 1;
    }

    using DefinitionSetter = uint32_t (*)(void*, const char*, void*);
    void* definition = SwfGetDefinition(this);
    void** definitionVtable = *reinterpret_cast<void***>(definition);
    if (uint8_t(reinterpret_cast<DefinitionSetter>(definitionVtable[5])(definition, property, value))) {
        return 1;
    }

    void*& script = *reinterpret_cast<void**>(instance + 0xA0);
    if (!script) {
        // The original requires a nonempty pool and reads the next link first.
        char* pool = reinterpret_cast<char*>(g_swfScriptObjectPool);
        void* object = *reinterpret_cast<void**>(pool + 12);
        void* next = *reinterpret_cast<void**>(object);
        --*reinterpret_cast<uint16_t*>(pool + 6);
        *reinterpret_cast<void**>(pool + 12) = next;
        *reinterpret_cast<void**>(object) = &g_vtable_swfSCRIPTOBJECT;
        *reinterpret_cast<uint32_t*>(reinterpret_cast<char*>(object) + 8) = 0;
        *reinterpret_cast<uint32_t*>(reinterpret_cast<char*>(object) + 4) = 0;
        *reinterpret_cast<uint32_t*>(reinterpret_cast<char*>(object) + 12) = 0;
        script = object;
    }
    // Unlike GetMember's fallback, assignment forwards the original tagged key.
    using ScriptSetter = uint32_t (*)(void*, const char*, void*);
    void** vtable = *reinterpret_cast<void***>(script);
    return reinterpret_cast<ScriptSetter>(vtable[11])(script, name, value);
}

// slot 12 = DeleteMember (same as base — no special display property handling)
void swfINSTANCE::DeleteMember(const char* name) {
    swfSCRIPTOBJECT::DeleteMember(name);
}

// slot 13 = Invoke (dispatches gotoAndPlay, gotoAndStop, play, nextFrame, prevFrame,
//          getBytesLoaded, getBytesTotal, attachMovie + falls through to base)
void swfINSTANCE::Invoke(const char* methodName, void* args, int argCount, void* outResult) {
    // Full body @ 0x823FE500 dispatches gotoAndPlay, gotoAndStop, play,
    // nextFrame, prevFrame, getBytesLoaded, getBytesTotal, attachMovie,
    // then falls through to the script-object base. Pending dedicated
    // lift; base Invoke handles the non-display-list AS methods.
    swfSCRIPTOBJECT::Invoke(methodName, args, argCount, outResult);
}


// ===========================================================================
// ===========================================================================
// swfACTIONFUNC — ActionScript function object
//
// swfACTIONFUNC wraps an inner swfSCRIPTOBJECT (at +7332, m_pInnerObject)
// and extends it with a local variable table for ActionScript closures.
// The local table stores up to m_localCount (at +132) named bindings,
// each as a 128-byte name string at +136 + index*128, with corresponding
// 8-byte {value, type} pairs in m_pLocalValues (at +7328).
//
// Most vtable methods are simple forwarding thunks that delegate to the
// inner object's corresponding vtable slot.
// ===========================================================================

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::ScalarDtor  [vtable slot 1 @ 0x823FF4E8]
// Forwards to inner object's scalar destructor (vtable slot 1).
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::ScalarDtor(int flags) {
    // Forward to inner MovieClip's scalar destructor (vtable slot 1).
    // Slot 1 is compiler-synthesised (not a declared virtual), so retain
    // explicit vtable indirection through a typed function pointer.
    swfINSTANCE* innerObj = m_pInnerObject;
    typedef void (*ScalarDtorFn)(swfINSTANCE*, int);
    void** vtable = *(void***)innerObj;
    ((ScalarDtorFn)vtable[1])(innerObj, flags);
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::NextFrame  [vtable slot 2 @ 0x823FF500]
// Forwards to inner object's vtable slot 2.
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::NextFrame() {
    // Forward to inner MovieClip's NextFrame (virtual slot 2).
    // Original binary passes no context argument.
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) innerObj->NextFrame(nullptr);
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::PrevFrame  [vtable slot 3 @ 0x823FF518]
// Forwards to inner object's vtable slot 3.
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::PrevFrame() {
    // Forward to inner MovieClip's PrevFrame (virtual slot 3).
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) innerObj->PrevFrame();
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::MarkDirty  [vtable slot 4 @ 0x823FF530]
// Forwards to inner object's vtable slot 4.
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::MarkDirty() {
    // Forward to inner MovieClip's MarkDirty (virtual slot 4).
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) innerObj->MarkDirty();
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::SetVisible  [vtable slot 5 @ 0x823FF548]
// Forwards to inner object's vtable slot 5.
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::SetVisible() {
    // Forward to inner MovieClip's SetVisible (virtual slot 5).
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) innerObj->SetVisible();
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::EnumerateMembers  [vtable slot 6 @ 0x823FF560]
// Forwards to inner object's vtable slot 6.
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::EnumerateMembers() {
    // Forward to inner MovieClip's EnumerateMembers (virtual slot 6).
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) innerObj->EnumerateMembers();
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::VisitChildren  [vtable slot 7 @ 0x823FF578]
// Forwards to inner object's vtable slot 7.
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::VisitChildren() {
    // Forward to inner MovieClip's child lookup/create helper (virtual slot 7).
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) innerObj->FindOrCreateChildByDepth();
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::GetMemberCount  [vtable slot 8 @ 0x823FF2A8]
// Returns total member count: inner object's count + local variable count.
// ─────────────────────────────────────────────────────────────────────────────
int swfACTIONFUNC::GetMemberCount() {
    // Inner MovieClip's member count + this closure's local bindings.
    swfINSTANCE* innerObj = m_pInnerObject;  // +7332
    int innerCount = innerObj ? innerObj->GetMemberCount() : 0;
    return innerCount + m_localCount;  // +132
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::Invoke  [vtable slot 13 @ 0x823FF4D0]
// Forwards to inner object's Invoke (vtable slot 13).
// ─────────────────────────────────────────────────────────────────────────────
void swfACTIONFUNC::Invoke(const char* methodName, void* args, int argCount, void* outResult) {
    // Forward to inner MovieClip's Invoke (virtual slot 13).
    swfINSTANCE* innerObj = m_pInnerObject;
    if (innerObj) innerObj->Invoke(methodName, args, argCount, outResult);
}

// ─────────────────────────────────────────────────────────────────────────────
// swfACTIONFUNC::GetMember  [vtable slot 10 @ 0x823FF2F0]
//
// Searches local variable table first (name strings at +136, stride 128),
// then delegates to inner object's GetMember (vtable slot 10).
// Local entries store 8-byte {value, type} pairs in m_pLocalValues (+7328).
// ─────────────────────────────────────────────────────────────────────────────
uint32_t swfACTIONFUNC::GetMember(const char* name, void* result) {
    // Intern the name string
    char internBuffer[SWF_INTERN_BUFFER_SIZE];
    extern const char* swfInternString(const char* name, void* buffer, int maxLen);
    const char* interned = swfInternString(name, internBuffer, SWF_INTERN_BUFFER_SIZE);

    // Search local variable table
    int localCount = m_localCount;  // +132
    if (localCount > 0) {
        const char* localNames = (const char*)this + 136;  // local name table
        for (int i = 0; i < localCount; i++) {
            // Compare interned name against local name entry (byte-by-byte)
            const char* entryName = localNames + i * 128;
            const char* src = interned;
            const char* dst = entryName;
            int diff = 0;
            while (*src != '\0') {
                diff = (int)(uint8_t)*src - (int)(uint8_t)*dst;
                if (diff != 0) break;
                src++;
                dst++;
            }
            if (diff == 0) {
                // Found — copy 8-byte value pair from m_pLocalValues
                uint32_t* localValues = (uint32_t*)m_pLocalValues;  // +7328
                uint32_t* out = (uint32_t*)result;
                out[0] = localValues[i * 2];
                out[1] = localValues[i * 2 + 1];
                return true;
            }
        }
    }

    // Not found locally — delegate to inner MovieClip's GetMember (slot 10).
    swfINSTANCE* innerObj = m_pInnerObject;  // +7332
    if (!innerObj) return false;
    return innerObj->GetMember(name, result);
}

int swfACTIONFUNC::VisitMembers() {
    // Forwards to inner MovieClip's VisitMembers (virtual slot 9).
    swfINSTANCE* innerObj = m_pInnerObject;
    return innerObj ? innerObj->VisitMembers() : 0;
}


// ===========================================================================
// swfSCRIPTARRAY — ActionScript array object
// ===========================================================================

/**
 * swfSCRIPTARRAY::~swfSCRIPTARRAY @ 0x823FF218 | size: 0x80
 *
 * Destructor — sets vtable to swfSCRIPTARRAY, frees the element array
 * at +16 if capacity (+22) > 0, then calls swfSCRIPTOBJECT base
 * destructor. If the delete flag is set, adds this object back to
 * the SWF object pool's free list.
 */
swfSCRIPTARRAY::~swfSCRIPTARRAY() {
    // Free element array (at +16) if capacity (uint16 at +22) > 0
    uint16_t capacity = *(uint16_t*)((char*)this + 22);
    if (capacity > 0) {
        void* elements = *(void**)((char*)this + 16);
        rage_free(elements);
    }
    // swfSCRIPTOBJECT base destructor runs automatically via C++ chain
}



// @ 0x823FEB48
uint32_t swfSCRIPTARRAY::GetMember(const char* name, void* result) {
    // Like the other GetMember overrides, name points at an 8-byte VM value,
    // despite the historical const char* declaration. String keys are never
    // parsed as array indices; only "length" is handled here.
    const auto* key = reinterpret_cast<const uint32_t*>(name);
    const auto* array = reinterpret_cast<const uint8_t*>(this);
    auto* output = static_cast<uint32_t*>(result);
    if (key[1] != 0 && key[1] != 1) {
        int32_t index = swfValueToInteger(key);
        if (index >= 0 && index < *reinterpret_cast<const uint16_t*>(array + 20)) {
            const auto* elements = *reinterpret_cast<const uint32_t* const*>(array + 16);
            const uint32_t* element = elements + index * 2;
            output[0] = element[0];
            output[1] = element[1];
            return true;
        }
    } else {
        extern void* g_swfStringBuffer;  // @ 0x82604850
        const char* property = util_A768_1(key, &g_swfStringBuffer, SWF_INTERN_BUFFER_SIZE);
        if (strcmp(property, "length") == 0) {
            output[0] = *reinterpret_cast<const uint16_t*>(array + 20);
            output[1] = 3; // VM integer tag; the old swfValueType enum differs.
            return true;
        }
    }
    return swfSCRIPTOBJECT::GetMember(name, result);
}

// Slot 11 converts the key to a signed index; it does not fall back to named members.
uint32_t swfSCRIPTARRAY::SetMember(const char* name, void* value) {
    int32_t index = swfValueToInteger(name);
    char* array = reinterpret_cast<char*>(this);
    if (index >= *reinterpret_cast<uint16_t*>(array + 0x14)) return 0;
    // Retail only checks the upper bound. Callers must provide storage for the index.
    uintptr_t elements = *reinterpret_cast<uintptr_t*>(array + 0x10);
    uint32_t* destination = reinterpret_cast<uint32_t*>(elements + static_cast<uintptr_t>(index) * 8);
    const uint32_t* pair = static_cast<const uint32_t*>(value);
    destination[0] = pair[0];
    destination[1] = pair[1];
    return 1;
}


// ===========================================================================
// swfOBJECT and derived display object classes
// ===========================================================================

// swfOBJECT/swfSPRITE destructors @ 0x82403518 / 0x82403560 just reseat
// the vtable pointer and return; any owned heap buffers are released by
// derived destructors (swfFONT / swfSHAPE / swfBUTTON / swfEDITTEXT).
swfOBJECT::~swfOBJECT() {}
swfSPRITE::~swfSPRITE() {}

// ===========================================================================
// swfCONTEXT Additional Methods
// ===========================================================================

/**
 * swfContext_IsGlobalSlot13AltMode @ 0x823FB1F0 | size: 0x64
 * 
 * Checks if the global SWF object's slot 13 has mismatched sign bits
 * between byte[0] and byte[3], indicating an alternate execution mode.
 * Returns true if the XOR of two bytes exceeds 127 (sign bit differs).
 */
bool swfContext_IsGlobalSlot13AltMode() {
    // External declarations
    extern void* swfGlobalObject_GetSlotValuePtr(void* obj, int slotIndex);  // @ 0x823FB188
    extern void* g_swfSlotObject;  // @ 0x82604848 (SDA offset 18504)
    
    // Get slot 13 value from the global SWF object
    uint8_t* result = (uint8_t*)swfGlobalObject_GetSlotValuePtr(g_swfSlotObject, 13);
    
    // Load bytes at offsets +0 and +3
    uint8_t byte0 = result[0];
    uint8_t byte3 = result[3];
    
    // XOR the bytes and check if result > 127
    uint8_t xorResult = byte0 ^ byte3;
    return (xorResult > 127);
}

// @ 0x823FAE98 | size: 0x17C
// Four signed 2.6 multipliers followed by four byte offsets. Stores wrap,
// without saturation. Preserve offset-before-multiplier writes for aliasing.
void swfConcatColorTransform(uint8_t* out, const uint8_t* local, const uint8_t* parent,
                             uint32_t rgb, uint32_t alpha) {
    int32_t factors[4];
    for (unsigned channel = 0; channel < 4; ++channel) {
        const int32_t inherited = static_cast<int8_t>(parent[channel]);
        const int32_t offset = (static_cast<int8_t>(local[channel + 4]) * inherited) >> 6;
        factors[channel] = static_cast<int8_t>((static_cast<int8_t>(local[channel]) * inherited) >> 6);
        out[channel + 4] = static_cast<uint8_t>(offset + parent[channel + 4]);
    }
    out[0] = static_cast<uint8_t>((factors[0] * int32_t((rgb >> 16) & 255)) / 255);
    out[1] = static_cast<uint8_t>((factors[1] * int32_t((rgb >> 8) & 255)) / 255);
    out[2] = static_cast<uint8_t>((factors[2] * int32_t(rgb & 255)) / 255);
    out[3] = static_cast<uint8_t>((factors[3] * int32_t(alpha & 255)) / 255);
}

// The old hudFlashBase_D450_g label belongs to the SWF instance renderer.
// instance +8 and parentTransform use the embedded transform layout (local
// matrix +0, world matrix +24, local colour +48, world colour +56, flag +140).
// @ 0x823FD450
void swfRenderInstanceTree(void* instance, const void* parentTransform) {
    extern void swfConcatMatrix(float* out, const float* child, const float* parent);  // @ 0x823FA1E0
    extern void* g_currentSwfContext;  // @ 0x8260281C
    extern void* g_swfRenderCallbackOwner;  // @ 0x82602814
    extern uint16_t g_swfMaskEndDepth;  // @ 0x826066CC

    auto* node = static_cast<uint8_t*>(instance);
    const auto* parent = static_cast<const uint8_t*>(parentTransform);
    if (node[0xAF] == 0) return;

    float* world = reinterpret_cast<float*>(node + 0x20);
    const float oldX = world[4];
    const float oldY = world[5];
    if (node[0x95] != 0) swfRebuildTransform(node + 8);
    swfConcatMatrix(world, reinterpret_cast<const float*>(node + 8),
                    reinterpret_cast<const float*>(parent + 24));
    node[0x94] = parent[140];
    const uint32_t rgb = (uint32_t(parent[68]) << 16) | (uint32_t(parent[69]) << 8) | parent[70];
    swfConcatColorTransform(node + 0x40, node + 0x38, parent + 56, rgb, parent[71]);
    if (node[0x43] == 0) return;

    uint32_t flags;
    void* texture = *reinterpret_cast<void**>(node + 0x90);
    if (texture) {
        hudFlashBase_76F8_g(0, 0, texture);
        if (g_grmShaderFx_flushRequired != 0 || g_grmShaderFx_forceResetFlag != 0) {
            hudFlashBase_B138_g();
        }
        node[0x94] = 1;
    }
    flags = g_grmShaderFx_flushRequired;
    uint32_t appliedMode;
    if (*reinterpret_cast<uint16_t*>(node + 0xA8) != 0) {
        grcDevice_Present(0, 0, 1, 1.0f, false, 0);
        g_grmShaderFx_variantTable[9] = 0;
        flags = g_grmShaderFx_flushRequired;
        flags = g_swfAppliedRenderState[9] == 0 ? flags & ~0x200u : flags | 0x200u;
        appliedMode = g_swfAppliedRenderState[6];
        g_grmShaderFx_variantTable[6] = 3;
        flags = appliedMode == 3 ? flags & ~0x40u : flags | 0x40u;
        g_grmShaderFx_flushRequired = flags;

        // Depth is accumulated modulo 65536, including each ancestor.
        uint16_t depth = *reinterpret_cast<uint16_t*>(node + 0xA6);
        auto* ancestor = *reinterpret_cast<uint8_t**>(node + 0xB0);
        while (ancestor) {
            depth = static_cast<uint16_t>(depth + *reinterpret_cast<uint16_t*>(ancestor + 0xA6));
            ancestor = *reinterpret_cast<uint8_t**>(ancestor + 0xB0);
        }
        g_swfMaskEndDepth = static_cast<uint16_t>(depth + *reinterpret_cast<uint16_t*>(node + 0xA8));
    } else {
        appliedMode = g_swfAppliedRenderState[6];
    }

    if (*reinterpret_cast<int32_t*>(node + 0x98) >= 0) {
        auto* owner = static_cast<uint8_t*>(g_swfRenderCallbackOwner);
        if (*reinterpret_cast<int32_t*>(owner + 16) != 0) {
            sysCallback_Invoke(owner + 4, node + 0x98);
            flags = g_grmShaderFx_flushRequired;
            appliedMode = g_swfAppliedRenderState[6];
        }
    }

    const uint32_t savedMode = g_grmShaderFx_variantTable[6];
    if (node[0x9C] != 0) {
        g_grmShaderFx_variantTable[6] = 2;
        flags = appliedMode == 2 ? flags & ~0x40u : flags | 0x40u;
        g_grmShaderFx_flushRequired = flags;
    }

    auto* child = *reinterpret_cast<uint8_t**>(node + 0xB4);
    if (child) {
        do {
            swfRenderInstanceTree(child, node + 8);
            child = *reinterpret_cast<uint8_t**>(child + 0xB8);
        } while (child);
        flags = g_grmShaderFx_flushRequired;
    } else {
        if (g_swfMaskEndDepth != 0) {
            uint16_t depth = *reinterpret_cast<uint16_t*>(node + 0xA6);
            auto* ancestor = *reinterpret_cast<uint8_t**>(node + 0xB0);
            while (ancestor) {
                depth = static_cast<uint16_t>(depth + *reinterpret_cast<uint16_t*>(ancestor + 0xA6));
                ancestor = *reinterpret_cast<uint8_t**>(ancestor + 0xB0);
            }
            if (depth > g_swfMaskEndDepth) {
                g_grmShaderFx_variantTable[6] = 3;
                flags = appliedMode == 3 ? flags & ~0x40u : flags | 0x40u;
                g_grmShaderFx_flushRequired = flags;
                g_swfMaskEndDepth = 0;
            }
        }
        if (node[0x43] != 0) {
            const int mode = g_currentSwfContext == instance ? (swfContext_IsGlobalSlot13AltMode() ? 3 : 2) : 1;
            auto* definition = *reinterpret_cast<swfOBJECT**>(node + 4);
            definition->Render(node + 8, mode);
            flags = g_grmShaderFx_flushRequired;
        }
        // fcmpu/bne considers NaNs changed; signed zeros compare equal.
        const bool moved = oldX != world[4] || oldY != world[5];
        node[0xAD] = node[0x43] == 64 && !moved;
    }

    appliedMode = g_swfAppliedRenderState[6];
    if (node[0x9C] != 0) {
        g_grmShaderFx_variantTable[6] = savedMode;
        flags = savedMode == appliedMode ? flags & ~0x40u : flags | 0x40u;
        g_grmShaderFx_flushRequired = flags;
    }
    if (*reinterpret_cast<uint16_t*>(node + 0xA8) != 0) {
        g_grmShaderFx_variantTable[9] = 15;
        flags = g_swfAppliedRenderState[9] == 15 ? flags & ~0x200u : flags | 0x200u;
        g_grmShaderFx_variantTable[6] = 5;
        flags = appliedMode == 5 ? flags & ~0x40u : flags | 0x40u;
        g_grmShaderFx_flushRequired = flags;
    }
}


/**
 * swfCONTEXT_ProcessContextTree @ 0x823FCA50 | size: 0x118
 * Dispatch this node and then visit its children in sibling order.
 */
void swfCONTEXT_ProcessContextTree(swfCONTEXT* ctx) {
    extern void* g_currentSwfContext;          // @ 0x8260281C
    extern int32_t g_swfContextStackCount;     // @ 0x8260484C
    extern int32_t g_swfContextStackFocusIndex; // @ 0x82604C64
    extern void* g_swfContextStack[32];        // @ 0x82604C68

    char* node = reinterpret_cast<char*>(ctx);
    uint8_t result = 0;
    if (*reinterpret_cast<uint8_t*>(node + 173)) {
        void* nested = *reinterpret_cast<void**>(node + 176);
        if (!nested || !*(reinterpret_cast<uint8_t*>(nested) + 170)) {
            void* object = *reinterpret_cast<void**>(node + 4);
            void** vtable = *reinterpret_cast<void***>(object);
            // The caller tests only r3's low byte; the callee need not zero-extend it.
            using ProbeFn = uint32_t (*)(void*);
            result = static_cast<uint8_t>(reinterpret_cast<ProbeFn>(vtable[6])(object));
        }
    }

    if (result && g_swfContextStackCount < 32) {
        int32_t index = g_swfContextStackCount;
        if (g_currentSwfContext == ctx) {
            g_swfContextStackFocusIndex = index;
        }
        g_swfContextStack[index] = ctx;
        g_swfContextStackCount = index + 1;
    } else if (g_currentSwfContext == ctx) {
        void* object = *reinterpret_cast<void**>(node + 4);
        void** vtable = *reinterpret_cast<void***>(object);
        using TransitionFn = void (*)(void*, swfCONTEXT*, int, int);
        reinterpret_cast<TransitionFn>(vtable[3])(object, ctx, 2, 1);
        g_currentSwfContext = nullptr;
    }

    auto* child = *reinterpret_cast<swfCONTEXT**>(node + 180);
    while (child) {
        swfCONTEXT_ProcessContextTree(child);
        child = *reinterpret_cast<swfCONTEXT**>(reinterpret_cast<char*>(child) + 184);
    }
}

// ============================================================================
// SWF image globals. Native storage lives in rage_data.cpp.
// ============================================================================
extern void* g_currentSwfContext;  // @ 0x8260281C
extern void* g_swfSlotObject;      // @ 0x82604848
extern int32_t g_swfPointerX;      // @ 0x825F312C
extern int32_t g_swfPointerY;      // @ 0x825F3138
extern uint32_t g_swfCallDepth;    // @ 0x82604D1C
extern float g_swfFrameScale;      // @ 0x82079B90
extern void* g_swfGlobalObject;    // @ 0x82602818
extern void* g_swfGlobalScope;         // @ 0x8260282C
extern void* g_swfStringBuffer;        // @ 0x82604850 — address of the 1024-byte buffer
extern void* g_vtable_swfSCRIPTOBJECT; // @ 0x82074D14 — address of the table

// ── swfINSTANCE::FindOrCreateChildByDepth @ 0x823FC908 size:0x144 ──
swfINSTANCE* swfINSTANCE::FindOrCreateChildByDepth(uint32_t depth, uint32_t character, void* definition) {
    const uint16_t key = static_cast<uint16_t>(depth);
    char* parent = reinterpret_cast<char*>(this);
    char** link = reinterpret_cast<char**>(parent + 180);
    char* child = *link;
    while (child && *reinterpret_cast<uint16_t*>(child + 166) < key) {
        link = reinterpret_cast<char**>(child + 184);
        child = *link;
    }
    if (!child || *reinterpret_cast<uint16_t*>(child + 166) != key) {
        char* pool = static_cast<char*>(g_swfInstancePool);
        char* storage = *reinterpret_cast<char**>(pool + 12);
        char* next = *reinterpret_cast<char**>(storage);
        --*reinterpret_cast<uint16_t*>(pool + 6);
        *reinterpret_cast<char**>(pool + 12) = next;
        child = storage ? static_cast<char*>(swfInstanceConstruct(storage)) : nullptr;
        *reinterpret_cast<char**>(child + 176) = parent;
        *reinterpret_cast<uint16_t*>(child + 166) = key;
        *reinterpret_cast<uint16_t*>(child + 168) = static_cast<uint16_t>(character);
        *reinterpret_cast<char**>(child + 184) = *link;
        *link = child;
    }
    *reinterpret_cast<void**>(child + 4) = definition;
    if (definition) {
        char* def = static_cast<char*>(definition);
        const uint8_t type = *reinterpret_cast<uint8_t*>(def + 4);
        if (type == 0 || type == 2) {
            const uint16_t frames = *reinterpret_cast<uint16_t*>(def + 8);
            if (frames && *reinterpret_cast<uint16_t*>(child + 164) >= frames) {
                rage_DebugLog(reinterpret_cast<const char*>(0x82074DE8),
                              *reinterpret_cast<uint16_t*>(child + 164), frames);
                *reinterpret_cast<uint16_t*>(child + 164) = 0;
            }
        }
    }
    return reinterpret_cast<swfINSTANCE*>(child);
}

} // namespace rage

// @ 0x823FD078
extern "C" void pg_D078_g(void* instance) {
    // Guest swfINSTANCE layout: definition +4, affine matrix +8, children
    // +0xB4/+0xB8, frame callback +0xCC, pointer callback +0xD0.
    char* object = static_cast<char*>(instance);
    using CallbackFn = void (*)(void*, int, int, void*, int);
    void* callback = *reinterpret_cast<void**>(object + 0xCC);
    if (callback) {
        void** vtable = *static_cast<void***>(callback);
        reinterpret_cast<CallbackFn>(vtable[14])(callback, 0, 0, instance, 0);
    }

    void* definition = *reinterpret_cast<void**>(object + 4);
    void** vtable = *static_cast<void***>(definition);
    using UpdateFn = void (*)(void*, void*);
    reinterpret_cast<UpdateFn>(vtable[2])(definition, instance);

    if (rage::g_currentSwfContext == instance) {
        int fromState = 0;
        int toState = 0;
        if (CheckButtonPressed(util_B188(rage::g_swfSlotObject, 13))) {
            fromState = 2;
            toState = 3;
        } else if (util_0068(util_B188(rage::g_swfSlotObject, 13)) != 0) {
            fromState = 3;
            toState = 2;
        }
        if (fromState != 0) {
            definition = *reinterpret_cast<void**>(object + 4);
            vtable = *static_cast<void***>(definition);
            using TransitionFn = void (*)(void*, void*, int, int);
            reinterpret_cast<TransitionFn>(vtable[3])(definition, instance, fromState, toState);
        }
    }

    if (*reinterpret_cast<void**>(object + 0xD0) &&
        util_0068(util_B188(rage::g_swfSlotObject, 32)) != 0) {
        const int32_t pointerX = rage::g_swfPointerX;
        const int32_t pointerY = rage::g_swfPointerY;
        const float hitX = static_cast<float>(pointerX);
        const float hitY = static_cast<float>(pointerY);

        // The original reuses the high words of its signed int64 conversion
        // scratch as outMin. Preserve them when a bounds helper writes nothing:
        // positive coordinates leave +0, negative coordinates leave a NaN.
        const uint32_t minXBits = pointerY < 0 ? 0xFFFFFFFFu : 0;
        const uint32_t minYBits = pointerX < 0 ? 0xFFFFFFFFu : 0;
        float minX;
        float minY;
        std::memcpy(&minX, &minXBits, sizeof(minX));
        std::memcpy(&minY, &minYBits, sizeof(minY));
        const float width = util_EF98(instance, &minX);
        const float height = swfINSTANCE_F0D8_w(instance, &minY);
        const float maxX = minX + width;
        const float maxY = minY + height;

        float* matrix = reinterpret_cast<float*>(object + 8);
        rage::swfRebuildTransform(matrix);
        // Keep fmuls rounding before each fmadds, and the final translation
        // addition separate. Ordered comparisons also reject all NaN bounds.
        const float leftProduct = matrix[0] * minX;
        const float topProduct = matrix[3] * minY;
        const float left = std::fma(matrix[2], minY, leftProduct) + matrix[4];
        const float top = std::fma(matrix[1], minX, topProduct) + matrix[5];
        if (hitX >= left) {
            const float rightProduct = matrix[0] * maxX;
            const float right = std::fma(matrix[2], maxY, rightProduct) + matrix[4];
            if (hitX <= right && hitY >= top) {
                const float bottomProduct = matrix[1] * maxX;
                const float bottom = std::fma(matrix[3], maxY, bottomProduct) + matrix[5];
                if (hitY <= bottom) {
                    callback = *reinterpret_cast<void**>(object + 0xD0);
                    vtable = *static_cast<void***>(callback);
                    reinterpret_cast<CallbackFn>(vtable[14])(callback, 0, 0, instance, 0);
                }
            }
        }
    }

    void* child = *reinterpret_cast<void**>(object + 0xB4);
    while (child) {
        pg_D078_g(child);
        child = *reinterpret_cast<void**>(static_cast<char*>(child) + 0xB8);
    }
}

// ============================================================================
// Stubs pending full implementation — pg_/PageGroup/swf*/hudFlashBase/Dialog
// (moved from src/stubs.cpp and src/stubs_final.cpp). These bodies remain
// as no-ops until their callees (pg_5B10_fw, pg_5BC8_fw, pg_80D0, pg_C3B8_g,
// UpdatePageGroup, pg_6C80_g, pongCameraMgr_5CE8_2hr, etc.) are themselves lifted.
// ============================================================================

// Forward decls for typed params used below.
struct TransitionParams;
struct TransitionFlags;

// ── pg_* / PageGroup / Dialog / TextEntry / CreditsRoll ─────────────────────
bool PageGroup_DispatchEvent(void* group, void* event, int eventType, unsigned int* outResult, int flags) {
    (void)group; (void)event; (void)eventType; (void)outResult; (void)flags; return false;
}
void* PageGroupNames_ResolveByHandle(void* namesMgr) { (void)namesMgr; return nullptr; }
void* PageGroupNames_ResolveByHandle(void* namesMgr, int handle) { (void)namesMgr; (void)handle; return nullptr; }
uint8_t PageGroup_ApplyTransition(void* gameState, TransitionParams* params, int transitionType,
                                  TransitionFlags* flags, int enableFlag) {
    (void)gameState; (void)params; (void)transitionType; (void)flags; (void)enableFlag; return 0;
}
uint8_t pg_ApplyTransition(void* gameState, TransitionParams* params, int transitionType,
                           TransitionFlags* flags, int enableFlag) {
    return PageGroup_ApplyTransition(gameState, params, transitionType, flags, enableFlag);
}
void PostPageGroupMessage_Internal(int messageId, int param1, int param2, int param3) { (void)messageId; (void)param1; (void)param2; (void)param3; }
void GeneratePageGroupCommands(void) {}

extern "C" void UpdatePageGroup(void* group) { (void)group; }
extern "C" void pgBase_AcquireRef(void* a, int b) { (void)a; (void)b; }

void PageGroup_DispatchEventCompat(void* group, void* event, int eventType,
                                   unsigned int* outResult, int flags) {
    (void)group; (void)event; (void)eventType; (void)outResult; (void)flags;
}
void pgPageGroup_DispatchEvent(void* group, void* event, int eventType,
                               unsigned int* outResult, int flags) {
    PageGroup_DispatchEventCompat(group, event, eventType, outResult, flags);
}

extern "C" {
void _c_pgPageGroup_DispatchEvent(void* a, void* b, int c, unsigned* d, int e) __asm__("_pg_6F68");
void _c_pgPageGroup_DispatchEvent(void* a, void* b, int c, unsigned* d, int e) {
    PageGroup_DispatchEvent(a, b, c, d, e);
}
} // extern "C"

void* PageGroup_GetTextEntry(void* a, const char* b) { (void)a; (void)b; return nullptr; }
void* PageGroup_LookupText(uint32_t a, const char* b) { (void)a; (void)b; return nullptr; }
void PageGroup_Register(void* a) { (void)a; }
void* PageGroup_SetState(void* a) { (void)a; return nullptr; }

extern "C" {
void DestroyPageGroup(void* group) { (void)group; }
int GetPageGroupState(void* group) { (void)group; return 0; }
void ProcessPageGroupInput(void* group) { (void)group; }
void NotifyUIEvent(int event) { (void)event; }
void* GetStateContextName(void* a) { (void)a; return nullptr; }
void FadePageGroup(void* a, float b, uint32_t c, uint32_t d, uint32_t e) {
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
void FadePageGroupOut(void* a, float b, int c, int d, int e) {
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
} // extern "C"

// C++-linkage FadePageGroup overload (different signature).
void FadePageGroup(void* a, int b, int c, float d, float e) {
    (void)a; (void)b; (void)c; (void)d; (void)e;
}

// C++-linkage PostPageGroupMessage overloads.
void PostPageGroupMessage(int a, int b, int c, int d, int e) {
    (void)a; (void)b; (void)c; (void)d; (void)e;
}
void PostPageGroupMessage(uint32_t a, uint8_t b, uint32_t c, uint32_t d, uint32_t e, uint32_t f) {
    (void)a; (void)b; (void)c; (void)d; (void)e; (void)f;
}
void PostPageGroupMessage(void* a, int b, int c, int d, int e) {
    (void)a; (void)b; (void)c; (void)d; (void)e;
}

extern "C" void PostPageGroupMessage_C(int a, int b, int c, int d) __asm__("_PostPageGroupMessage");
extern "C" void PostPageGroupMessage_C(int a, int b, int c, int d) {
    (void)a; (void)b; (void)c; (void)d;
}

void DismissPageGroup(void* a) { (void)a; }
void InitializePageGroup(void* a) { (void)a; }
void SetPageGroupVisible(void* a) { (void)a; }

uint8_t Dialog_IsComplete(void* a) { (void)a; return 0; }
void* DialogPageGroup_Construct(void* a) { (void)a; return nullptr; }
void* LegalsPageGroup_Construct(void* a) { (void)a; return nullptr; }

int32_t TextEntry_GetValue(void* a) { (void)a; return 0; }

void CreditsRoll_Deactivate(void* a, int b, int c) { (void)a; (void)b; (void)c; }
void* CreditsRoll_NotifyEntry(void* a, uint32_t b) { (void)a; (void)b; return nullptr; }

// ── hudFlashBase_* ──────────────────────────────────────────────────────────
void hudFlashBase_RenderElement(void* hudObj, int modeIndex, float param1, float param2,
                                int flag1, int flag2, int flag3) {
    (void)hudObj; (void)modeIndex; (void)param1; (void)param2; (void)flag1; (void)flag2; (void)flag3;
}
void hudFlashBase_0F08_g(void* hudObj, int modeIndex, float param1, float param2,
                         int flag1, int flag2, int flag3) {
    hudFlashBase_RenderElement(hudObj, modeIndex, param1, param2, flag1, flag2, flag3);
}
void hudFlashBase_DrawFlashOverlay(void* a, void* b, void* c, float d, int e) {
    (void)a; (void)b; (void)c; (void)d; (void)e;
}

namespace rage {
void hudFlashBase_ExecuteFromContext(void* a, void* b, void* c) { (void)a; (void)b; (void)c; }
} // namespace rage

// ── swf* free functions ─────────────────────────────────────────────────────
extern "C" {
void swfContext_Cleanup(void* context) { (void)context; }
void swfFile_DestroyResources(void* file) { (void)file; }
void swfInstance_Cleanup(void* instance) { (void)instance; }
float swfComputeFramePosition(void* a, void* b, float* c, float* d) {
    (void)a; (void)b; if (c) *c = 0.0f; if (d) *d = 0.0f; return 0.0f;
}
const char* swfInternString(const char* a, void* b, int c) {
    (void)b; (void)c; return a;
}
// @ 0x82403270
void* swfPopResult(void* dst) {
    // Native storage is mapped to the retail addresses only by lift-check.
    // Empty pops produce integer zero.
    auto& depth = rage::g_swfCallDepth;
    auto* stack = rage::g_swfValueStack;
    if (depth == 0) {
        rage_DebugLog("Warning: Attempting to pop object from the stack but nothing is on the stack");
        stack[0] = 0;
        stack[1] = 3;
        depth = 1;
    }
    --depth;
    auto* out = static_cast<uint32_t*>(dst);
    out[0] = stack[depth * 2];
    out[1] = stack[depth * 2 + 1];
    return dst;
}
void swfSymtab_Delete(void* a, const char* b) { (void)a; (void)b; }
void swfSymtab_Enumerate(void* a) { (void)a; }
} // extern "C"
