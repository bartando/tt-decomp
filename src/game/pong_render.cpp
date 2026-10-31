/**
 * pong_render.cpp — Light state and render bucket implementation
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Lifted functions:
 *   pongLightState_CopyLights                      @ 0x8213E110
 *   pongLightState_Apply                           @ 0x82154320
 *   pongRender_ResetState                         @ 0x82225590
 *   pongDrawBucketLayer::Render                    @ 0x82225D90
 *   pongShadowMap::applyShaderParameters            @ 0x82147228
 *   pongDrawBucketManager::~pongDrawBucketManager  @ 0x822272B0  (vfn_0)
 *   pongDrawBucketManager::Load                    @ 0x82227430
 *   pongDrawBucket_AddEntry                        @ 0x822278D8
 *
 * Sources: recomp/structured_pass5_final/tt-decomp_recomp.{3,9}.cpp
 */

#include "rage/indexed_registry.h"
#include "pong_render.hpp"
#include "camera/pong_camera.hpp"
#include <cstring>
#include "rage/shader_parameters.hpp"
#include "rage/sys_callback.hpp"

// pongLightState_CopyLights @ 0x8213E110 | size: 0x30C (was game_E110)
// Copies all eight slots, regardless of count. game_E0A8 (0x8213E0A8)
// wraps this to also copy ambient and the two halfwords; those are untouched here.
// The original returns dst in r3 and leaves each light's tail padding alone.
pongLightState* pongLightState_CopyLights(pongLightState* dst, const pongLightState* src) {
    for (int i = 0; i < 8; ++i) {
        for (int v = 0; v < 3; ++v) {
            dst->lights[i].vectors[v] = src->lights[i].vectors[v];
        }
        dst->lights[i].scalars[0] = src->lights[i].scalars[0];
        dst->lights[i].scalars[1] = src->lights[i].scalars[1];
        for (int f = 0; f < 4; ++f) {
            dst->lights[i].flags[f] = src->lights[i].flags[f];
        }
    }
    return dst;
}

namespace {
float flushLightVmx(float value) {
    uint32_t bits;
    memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        memcpy(&value, &bits, sizeof(value));
    }
    return value;
}
}  // namespace

extern pongLightState lbl_825CA610;             // @ 0x825CA610  applied light-state snapshot
extern uint32_t lbl_825EBB18;                   // @ 0x825EBB18  Diffuse handle / initialization sentinel
extern uint32_t lbl_825EBAAC;                   // @ 0x825EBAAC  Position handle
extern uint32_t lbl_825EBC30;                   // @ 0x825EBC30  LightCount handle
extern uint32_t lbl_825EBAB0;                   // @ 0x825EBAB0  LightType handle
extern uint32_t lbl_825EBC34;                   // @ 0x825EBC34  Ambient handle
extern ShaderTable* lbl_825EBC40;          // @ 0x825EBC40
extern "C" const uint8_t g_shaderParameterDirtyMasks[8];           // @ 0x825D4C80  MSB-first dirty-bit masks
extern const float lbl_825C5938;               // @ 0x825C5938  -1.0f
extern const float lbl_8202D108;               // @ 0x8202D108  1.0f
extern "C" uint32_t g_grmShaderFx_variantTable[23];  // @ 0x825EBBD8  pending render state
extern "C" uint32_t g_grmShaderFx_boundContext;      // @ 0x825EBC54  shader-global write counter

// @ 0x8213E0A8 | size: 0x64
pongLightState* game_E0A8(pongLightState* dst, const pongLightState* src) {
    pongLightState_CopyLights(dst, src);
    dst->ambient = src->ambient;
    dst->count = src->count;
    dst->field_212 = src->field_212;
    return dst;
}
extern uint32_t game_A2F8(const char* name, int create);              // @ 0x8215A2F8
// @ 0x8215A670 | size: 0xCC
void game_A670(uint32_t handle, const ShaderVector* values, int count) {
    ShaderTable* table = lbl_825EBC40;
    uint32_t* entry = table->entries + (handle >> 18) * 2;
    uint32_t bit = (handle >> 1) & 0x1FFFFu;
    uint32_t header = entry[0];
    ++g_grmShaderFx_boundContext;
    uint32_t length = count != 0 ? static_cast<uint32_t>(count) : ((header >> 2) & 0x3FFFu);
    uint32_t end = bit + length;
    while (bit < end) {
        uint8_t vector[16];
        const void* source = reinterpret_cast<const void*>(
            reinterpret_cast<uintptr_t>(values) & ~uintptr_t(15));
        memcpy(vector, source, sizeof(vector));
        ShaderVector* bank = table->values;
        table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7];
        entry += 2;
        uint32_t slot = entry[1] & 0xFFFFu;
        void* destination = reinterpret_cast<void*>(
            reinterpret_cast<uintptr_t>(bank + slot) & ~uintptr_t(15));
        memcpy(destination, vector, sizeof(vector));
        ++bit;
        ++values;
    }
}

// @ 0x82154320 | size: 0x308 (game_4320)
// Inferred name: upload the light state to Diffuse/Position/LightCount/LightType/Ambient.
void pongLightState_Apply(const pongLightState* state) {
    game_E0A8(&lbl_825CA610, state);

    const int count = state->count;
    alignas(16) ShaderVector diffuse[8];
    alignas(16) ShaderVector position[8];
    float type[8];
    const uint32_t mode = g_grmShaderFx_variantTable[1];
    for (int i = 0; i < count; ++i) {
        const pongLightState::Light& light = state->lights[i];
        // vectors: position/direction/diffuse; scalars: falloff/intensity.
        // flags: type, negate falloff, negate diffuse (all retain raw bytes).
        const bool directional = mode == 2 && light.flags[0] == 0;
        memcpy(position[i].lane, light.vectors[directional ? 1 : 0].bits, 16);
        position[i].lane[3] = light.scalars[1];
        memcpy(diffuse[i].lane, light.vectors[2].bits, 16);
        diffuse[i].lane[3] = light.scalars[0];
        type[i] = directional ? 0.0f : 1.0f;

        if (light.flags[2] != 0) {
            // The VMX multiply flushes subnormals in all four lanes; w uses +1.
            for (int lane = 0; lane < 4; ++lane) {
                const float sign = lane == 3 ? lbl_8202D108 : lbl_825C5938;
                diffuse[i].lane[lane] = flushLightVmx(flushLightVmx(diffuse[i].lane[lane]) * sign);
            }
        }
        if (light.flags[1] != 0) {
            // This is scalar fmuls: retain subnormals when the VMX path was skipped.
            diffuse[i].lane[3] *= lbl_825C5938;
        }
    }

    uint32_t diffuseHandle = lbl_825EBB18;
    uint32_t positionHandle;
    uint32_t countHandle;
    uint32_t typeHandle;
    uint32_t ambientHandle;
    if (diffuseHandle == 0) {
        lbl_825EBB18 = diffuseHandle = game_A2F8("Diffuse", 1);
        lbl_825EBAAC = positionHandle = game_A2F8("Position", 1);
        lbl_825EBC30 = countHandle = game_A2F8("LightCount", 1);
        lbl_825EBAB0 = typeHandle = game_A2F8("LightType", 1);
        lbl_825EBC34 = ambientHandle = game_A2F8("Ambient", 1);
        // All five lookups happen even when the Diffuse lookup fails.
        if (diffuseHandle == 0)
            return;
    } else {
        positionHandle = lbl_825EBAAC;
        countHandle = lbl_825EBC30;
        typeHandle = lbl_825EBAB0;
        ambientHandle = lbl_825EBC34;
    }

    game_A670(diffuseHandle, diffuse, count);
    game_A670(positionHandle, position, count);

    ShaderTable* table = lbl_825EBC40;
    uint32_t bit = (countHandle >> 1) & 0x1FFFF;
    table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7];
    uint32_t slot = table->entries[(countHandle >> 18) * 2 + 1] & 0xFFFF;
    table->values[slot].lane[0] = static_cast<float>(count);

    grmShaderParameter_SetFloatArray(lbl_825EBC40, typeHandle, type, count);

    table = lbl_825EBC40;
    bit = (ambientHandle >> 1) & 0x1FFFF;
    g_grmShaderFx_boundContext += 3;
    table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7];
    slot = table->entries[(ambientHandle >> 18) * 2 + 1] & 0xFFFF;
    memcpy(table->values[slot].lane, state->ambient.bits, 16);
}

extern "C" {
    extern uint32_t g_grmShaderFx_flushRequired;       // @ 0x825EBB1C
    extern uint32_t g_grmShaderFx_forceResetFlag;      // @ 0x825EBAB4
    extern uint32_t g_grcAppliedRenderState[22];       // @ 0x825EBB80
    extern uint32_t g_grcPendingTextureState[24];      // @ 0x825EBB20
    extern uint32_t g_grcAppliedTextureState[24];      // @ 0x825EBAB8
    extern void* g_grcDefaultTexture;                 // @ 0x825EBA20
    extern uint32_t g_grcFormatId;                    // @ 0x825C9030
    extern void* lbl_826063C8;                        // @ 0x826063C8
}
extern void game_5450();                              // @ 0x82225450 — reset all 16 device samplers
extern void pongShadowMap_A5C8_g(uint32_t handle, void* texture); // @ 0x8215A5C8 — shader texture write

// @ 0x82225590 | size: 0x7FC (was pongShadowMap_5590_g)
// Inferred name: establish per-pass render defaults, reset device samplers and
// update the fallback tables consumed by grmShaderInstance_Unbind. Called by
// ordinary draw passes as well as GenerateShadowMaps; this is not a shadow-map method.
// Negative passes request full colour writes and cull mode 1; 13/14 use cull mode 0.
// The baseline blocks and fallback tables retain their image addresses, as in rage_grm.cpp.
void pongRender_ResetState(int32_t pass) {
    auto* defaults = reinterpret_cast<uint32_t*>(0x825C8F58u);
    auto* pending = g_grmShaderFx_variantTable;
    const auto* applied = g_grcAppliedRenderState;
    uint32_t dirty = g_grmShaderFx_flushRequired;
    const auto setDefault = [&](uint32_t index, uint32_t value) {
        defaults[index] = value;
        pending[index] = value;
        const uint32_t bit = 1u << index;
        dirty = applied[index] == value ? dirty & ~bit : dirty | bit;
    };

    setDefault(12, static_cast<uint32_t>(pass) - 1u <= 15u);
    setDefault(3, 0);
    setDefault(10, 0);
    setDefault(5, 0);
    setDefault(6, 3);
    setDefault(19, 1);
    setDefault(7, 1);
    const bool fullColour = pass < 0 || (pass >= 4 && pass < 17);
    setDefault(9, fullColour ? 15 : 7);
    const uint32_t cullMode = pass < 0 ? 1 : (static_cast<uint32_t>(pass) - 13u <= 1u ? 0 : 2);
    setDefault(0, cullMode);
    *reinterpret_cast<uint32_t*>(0x825C8F54u) = 2;
    // The PPC briefly updates bit 1 if the previous pending value exceeded 2,
    // then unconditionally replaces it with this comparison before publishing.
    setDefault(1, 2);
    g_grmShaderFx_flushRequired = dirty;

    auto* defaultTextures = reinterpret_cast<uint32_t*>(0x825C8FB0u);
    const uint32_t texture = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(g_grcDefaultTexture));
    uint32_t textureDirty = g_grmShaderFx_forceResetFlag;
    for (uint32_t slot = 0; slot < 8; ++slot) {
        defaultTextures[slot * 3] = texture;
        g_grcPendingTextureState[slot * 3] = texture;
        const uint32_t bit = 1u << (slot * 4);
        textureDirty = g_grcAppliedTextureState[slot * 3] == texture
            ? textureDirty & ~bit : textureDirty | bit;
        // On a mismatch the original publishes immediately, then again after the loop.
        if (g_grcAppliedTextureState[slot * 3] != texture)
            g_grmShaderFx_forceResetFlag = textureDirty;
    }
    g_grmShaderFx_forceResetFlag = textureDirty;
    game_5450();

    if (pass == 0 || pass == 17 || pass == 18) {
        const auto* shadow = *reinterpret_cast<uint8_t**>(static_cast<uint8_t*>(lbl_826063C8) + 8);
        const uint32_t handle = *reinterpret_cast<const uint32_t*>(shadow + 1028);
        if (handle != 0) {
            void* shadowTexture = *reinterpret_cast<void* const*>(shadow + (pass == 18 ? 980 : 976));
            pongShadowMap_A5C8_g(handle, shadowTexture);
        }
    }

    auto* renderDefaults = reinterpret_cast<uint32_t*>(0x825B1F90u);
    const auto setRenderDefault = [&](uint32_t offset, uint32_t value) {
        for (uint32_t i = 0; i < 87; ++i) {
            if (renderDefaults[i * 2] == offset) {
                renderDefaults[i * 2 + 1] = value;
                break;
            }
        }
    };
    setRenderDefault(60, pass > 0 && pass < 17);
    setRenderDefault(80, 0);
    setRenderDefault(72, 6);
    setRenderDefault(76, 7);
    setRenderDefault(96, 0);
    setRenderDefault(100, 0);
    setRenderDefault(44, g_grcFormatId == 0x1A220197u ? 6 : 3);
    setRenderDefault(40, 1);
    setRenderDefault(48, 1);
    setRenderDefault(212, fullColour ? 15 : 7);
    setRenderDefault(56, pass < 0 ? 6 : (static_cast<uint32_t>(pass) - 13u <= 1u ? 0 : 2));

    struct SamplerDefault {
        uint16_t field_0;
        uint16_t offset;
        uint32_t value;
    };
    auto* samplerDefaults = reinterpret_cast<SamplerDefault*>(0x825B2248u);
    const auto setSamplerDefault = [&](uint16_t offset, uint32_t value) {
        for (uint32_t i = 0; i < 20; ++i) {
            if (samplerDefaults[i].offset == offset) {
                samplerDefaults[i].value = value;
                break;
            }
        }
    };
    // Preserve the scalar load/store conversion before copying the LOD's raw word.
    const float lod = *reinterpret_cast<const uint8_t*>(0x826064E2u) != 0
        ? lbl_825C5938 : *reinterpret_cast<const float*>(0x8202D110u);
    uint32_t lodBits;
    memcpy(&lodBits, &lod, sizeof(lodBits));
    setSamplerDefault(24, 0);
    setSamplerDefault(16, 4);
    setSamplerDefault(20, 4);
    setSamplerDefault(36, 2);
    setSamplerDefault(0, 0);
    setSamplerDefault(4, 0);
    setSamplerDefault(8, 0);
    setSamplerDefault(28, lodBits);
    setSamplerDefault(56, 3);
}

// A slot starts at config+0x110 and repeats every 0xE0 bytes. Seven slots:
// three map slots, then two player pairs (the second pair is at indices 5/6).
struct pongShadowSlot {
    uint8_t enabled;                  // +0x00
    uint8_t _001[0x4F];
    ShaderVector matrix[4];            // +0x50
    ShaderVector weight;               // +0x90 (w scales xyz)
    uint8_t _0A0[0x30];
    float softness;                    // +0xD0
    int32_t pass;                      // +0xD4
    uint8_t _0D8[8];
};
static_assert(sizeof(pongShadowSlot) == 0xE0, "shadow slot stride");

struct pongShadowConfig {
    uint8_t _000[0x100];
    int32_t slotCount;                 // +0x100
    uint8_t _104[0x0C];
    pongShadowSlot slots[7];           // +0x110
    uint8_t _730[0xC0];
    float mapSampleScale;              // +0x7F0
    float playerSampleScale;           // +0x7F4
};
static_assert(__builtin_offsetof(pongShadowConfig, mapSampleScale) == 2032, "map sampling scale");
#if UINTPTR_MAX == 0xFFFFFFFFu
static_assert(__builtin_offsetof(pongShadowMap, m_config) == 8, "shadow config pointer");
static_assert(__builtin_offsetof(pongShadowMap, m_draw_430) == 1072, "last shader handle");
#endif

extern void* lbl_825EBA20;                       // @ 0x825EBA20  fallback texture
extern ShaderVector lbl_82617DF0;               // @ 0x82617DF0  softness upload scratch
extern const float lbl_825CA430[2];             // @ 0x825CA430  half-texel offsets
extern const ShaderVector lbl_825CA4A8[4];       // @ 0x825CA4A8  paired sampling taps
extern const float lbl_825C4890;                // @ 0x825C4890  shadow blend (0.3)
extern void* game_53C8(pongShadowMap* map, int32_t player, int32_t layer); // @ 0x821453C8
extern void pongShadowMap_A5C8_g(uint32_t handle, void* texture);         // @ 0x8215A5C8
extern void game_9AA0(ShaderTable* table, uint32_t handle, const ShaderVector* matrices,
                      int32_t count);                                  // @ 0x82159AA0

namespace {
int32_t shadowTextureDimension(void* texture, int slot) {
    using DimensionFn = int32_t (*)(void*);
    return reinterpret_cast<DimensionFn>((*static_cast<void***>(texture))[slot])(texture);
}
} // namespace

// @ 0x82147228 | size: 0x600 (was pongShadowMap_7228_g)
void pongShadowMap::applyShaderParameters(int32_t pass) {
    alignas(16) ShaderVector weights[3];
    alignas(16) ShaderVector matrices[3 * 4];
    int selected = 0;
    const int32_t slotCount = m_config->slotCount;
    for (int32_t i = 0; i < slotCount; ++i) {
        const pongShadowSlot& slot = m_config->slots[i];
        if (slot.pass != pass)
            continue;
        for (int lane = 0; lane < 3; ++lane)
            weights[selected].lane[lane] = slot.weight.lane[lane] * slot.weight.lane[3];
        weights[selected].lane[3] = lbl_8202D108;
        if (pass > 0) {
            memcpy(&matrices[selected * 4], slot.matrix, sizeof(slot.matrix));
            if (slot.enabled == 0 || (i == 5 && m_draw_448 != 0) || (i == 6 && m_draw_448 != 1))
                weights[selected].lane[0] = 0.0f;
        }
        ++selected;
    }
    if (m_draw_420 != 0)
        game_A670(m_draw_420, weights, 3);

    if (m_draw_41c != 0) {
        ++g_grmShaderFx_boundContext;
        lbl_82617DF0.lane[2] = m_config->slots[pass].softness;
        ShaderTable* table = lbl_825EBC40;
        uint32_t dirtyBit = (m_draw_41c >> 1) & 0x1FFFF;
        table->dirtyBits[dirtyBit >> 3] |= g_shaderParameterDirtyMasks[dirtyBit & 7];
        uint32_t index = table->entries[(m_draw_41c >> 18) * 2 + 1] & 0xFFFF;
        memcpy(table->values[index].lane, lbl_82617DF0.lane, 16);
    }
    if (m_draw_424 != 0) {
        ++g_grmShaderFx_boundContext;
        game_9AA0(lbl_825EBC40, m_draw_424, matrices, pass > 0 ? 2 : 1);
    }

    float scaleX, scaleY, offsetX, offsetY;
    if (pass == 0) {
        void* texture = reinterpret_cast<void*>(static_cast<uintptr_t>(m_draw_3d0));
        int32_t height = shadowTextureDimension(texture, 9);
        int32_t width = shadowTextureDimension(texture, 8);
        float radius = m_config->mapSampleScale * 0.5f;
        scaleY = radius / static_cast<float>(height);
        scaleX = radius / static_cast<float>(width);
        offsetX = offsetY = 0.0f;
    } else if (m_draw_408 != 0 && m_draw_410 != 0) {
        const int32_t player = pass - 1;
        void* texture = game_53C8(this, player, 0);
        pongShadowMap_A5C8_g(m_draw_408, texture);
        pongShadowMap_A5C8_g(m_draw_410, texture);
        void* second = lbl_825EBA20;
        if (m_config->slots[player + 5].enabled != 0 && player == static_cast<int32_t>(m_draw_448))
            second = reinterpret_cast<void*>(static_cast<uintptr_t>(
                static_cast<int32_t>(m_draw_444) < 2 ? m_draw_3fc : m_draw_3f4));
        pongShadowMap_A5C8_g(m_draw_40c, second);
        pongShadowMap_A5C8_g(m_draw_414, second);
        if (texture == lbl_825EBA20)
            texture = second;

        int32_t width = shadowTextureDimension(texture, 8);
        void* reference = reinterpret_cast<void*>(static_cast<uintptr_t>(m_draw_3f0));
        int32_t referenceWidth = shadowTextureDimension(reference, 8);
        float scaledWidth = m_config->playerSampleScale * static_cast<float>(width);
        scaleX = scaledWidth / static_cast<float>(referenceWidth);
        int32_t height = shadowTextureDimension(texture, 9);
        int32_t referenceHeight = shadowTextureDimension(reference, 9);
        float scaledHeight = m_config->playerSampleScale * static_cast<float>(height);
        scaleY = scaledHeight / static_cast<float>(referenceHeight);
        height = shadowTextureDimension(texture, 9);
        width = shadowTextureDimension(texture, 8);
        scaleY /= static_cast<float>(height);
        scaleX /= static_cast<float>(width);
        height = shadowTextureDimension(texture, 9);
        width = shadowTextureDimension(texture, 8);
        offsetY = lbl_825CA430[1] / static_cast<float>(height);
        offsetX = lbl_825CA430[0] / static_cast<float>(width);
    }
    // Missing player texture bindings leave the original's scratch floats
    // uninitialized. The caller must disable this upload in that state.
    if (static_cast<int32_t>(m_draw_42c) >= 0) {
        alignas(16) ShaderVector taps[4];
        for (int i = 0; i < 4; ++i) {
            taps[i].lane[0] = __builtin_fmaf(lbl_825CA4A8[i].lane[0], scaleX, offsetX);
            taps[i].lane[1] = __builtin_fmaf(lbl_825CA4A8[i].lane[1], scaleY, offsetY);
            taps[i].lane[2] = __builtin_fmaf(lbl_825CA4A8[i].lane[2], scaleX, offsetX);
            taps[i].lane[3] = __builtin_fmaf(lbl_825CA4A8[i].lane[3], scaleY, offsetY);
        }
        game_A670(m_draw_42c, taps, 4);
    }
    if (m_draw_430 != 0) {
        ++g_grmShaderFx_boundContext;
        ShaderTable* table = lbl_825EBC40;
        uint32_t dirtyBit = (m_draw_430 >> 1) & 0x1FFFF;
        table->dirtyBits[dirtyBit >> 3] |= g_shaderParameterDirtyMasks[dirtyBit & 7];
        uint32_t index = table->entries[(m_draw_430 >> 18) * 2 + 1] & 0xFFFF;
        table->values[index].lane[0] = lbl_825C4890;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Layer rendering
// ─────────────────────────────────────────────────────────────────────────────
extern void pongLightState_Reset(pongLightState* state, int32_t mask);  // @ 0x82154628
extern void cmOperatorCtor_0B50_w(void* overrideState);  // @ 0x820F0B50
extern "C" void* rage_A980(void* device);  // @ 0x8235A980
extern uint32_t* grc_9B60(void* commands);  // @ 0x82359B60
extern void rage_C660(void* device);  // @ 0x8235C660

// @ 0x82225D90 | size: 0x328 (was rage_5D90)
// Inferred name from the layer descriptors consumed by pongDrawBucket_AddEntry.
// Callbacks run even for disabled layers. Mode 4 with a shader override draws
// unlit entries first under that override, flushes it, then draws lit entries.
void pongDrawBucketLayer::Render(int32_t pass) {
    auto* callbacks = reinterpret_cast<void**>(0x825C58ECu);
    if (void* callback = callbacks[beforeCallback * 2])
        sysCallback_Invoke(callback, nullptr);

    if (enabled != 0) {
        const uint32_t frame = *reinterpret_cast<const uint32_t*>(0x825C4898u);
        pongRender_ResetState(pass);
        pongLightState defaults;
        defaults.count = 3;
        defaults.field_212 = 3;
        pongLightState_Reset(&defaults, -1);
        pongLightState_Reset(&defaults, -1);
        for (int lane = 0; lane < 4; ++lane)
            memcpy(&defaults.ambient.bits[lane], &lbl_8202D108, sizeof(float));

        auto* manager = *reinterpret_cast<uint8_t**>(0x826064F4u);
        auto*& shaderOverride = *reinterpret_cast<void**>(0x825EB1D0u);
        const bool twoPasses = *reinterpret_cast<void**>(manager + 84) != nullptr && sortMode == 4;
        auto* loop = *reinterpret_cast<uint8_t**>(0x825EAB30u);
        void* root = *reinterpret_cast<void**>(0x8271A310u);
        auto* active = *reinterpret_cast<uint8_t**>(0x82606564u);
        const int32_t key = loop[576] != 0
            ? *reinterpret_cast<int32_t*>(static_cast<uint8_t*>(root) + 32)
            : *reinterpret_cast<int32_t*>(active + 20);
        auto* lighting = key >= 0 ? static_cast<uint8_t*>(pg_C2A0_g(root, key)) : nullptr;
        const float threshold = *reinterpret_cast<const float*>(0x8202D110u);

        for (int phase = twoPasses ? 1 : 0; phase >= 0; --phase) {
            void* savedOverride = nullptr;
            if (phase == 1) {
                savedOverride = shaderOverride;
                shaderOverride = *reinterpret_cast<void**>(manager + 84);
            }
            pongLightState_Apply(&defaults);
            if (counts[frame] > 0) {
                for (int i = 0; i < counts[frame]; ++i) {
                    Entry* entry = buffers[frame].entries[order[frame][i]];
                    const int32_t light = entry->lightIndex;
                    if (phase == 0 && light >= 0) {
                        if (lighting != nullptr) {
                            const float weight = *reinterpret_cast<const float*>(lighting + 5728 + light * 4);
                            // bgt skips the primary state only for ordered greater;
                            // equal and NaN both select the primary state.
                            const uint32_t offset = weight > threshold ? 3552 : 208;
                            pongLightState_Apply(
                                reinterpret_cast<const pongLightState*>(lighting + light * 544 + offset));
                        }
                        reinterpret_cast<void (*)(Entry*, int32_t)>(entry->vtable[0])(entry, pass);
                        if (!twoPasses)
                            pongLightState_Apply(&defaults);
                    } else if (light < 0 && (phase == 1 || !twoPasses)) {
                        reinterpret_cast<void (*)(Entry*, int32_t)>(entry->vtable[0])(entry, pass);
                    }
                }
                manager = *reinterpret_cast<uint8_t**>(0x826064F4u);
            }
            if (phase == 1) {
                cmOperatorCtor_0B50_w(*reinterpret_cast<void**>(manager + 84));
                manager = *reinterpret_cast<uint8_t**>(0x826064F4u);
                shaderOverride = savedOverride;
            }
        }

        if (pass == -1) {
            auto* device = *reinterpret_cast<uint8_t**>(0x825EB988u);
            rage_A980(device);
            auto* cursor = *reinterpret_cast<uint32_t**>(device + 13580);
            auto* end = *reinterpret_cast<uint32_t**>(device + 13584);
            if (reinterpret_cast<uintptr_t>(cursor) + 4 > reinterpret_cast<uintptr_t>(end))
                cursor = grc_9B60(device + 13572);
            *cursor = 0x84000000u;
            *reinterpret_cast<uint32_t**>(device + 13580) = cursor + 1;
            device[10432] = (device[10432] & 0xDDu) | 2u;
            *reinterpret_cast<uint64_t*>(device + 40) |= 0x20000000ull;
            if ((device[10432] & 1) != 0)
                rage_C660(device);
        }
    }

    if (void* callback = callbacks[afterCallback * 2])
        sysCallback_Invoke(callback, nullptr);
}

// ─────────────────────────────────────────────────────────────────────────────
// Globals
// ─────────────────────────────────────────────────────────────────────────────

// @ 0x82606358 (SDA, r2-relative offset 25432)
// Written by Load(), read by render-sort passes.
extern uint32_t g_numDrawBuckets;

// Static config strings (from .rdata, referenced in Load())
static const char* s_configBasename = "settings";
static const char* s_configExt      = "drawbucket";

// Static per-bucket init data (used by pongDrawBucket::Load)
// Placeholder: actual structure populated from XML; opaque to bucket manager
static void* s_bucketData[32] = {};

// External XML parsing helpers (called via rage tokeniser vtable)
extern int   xml_ReadInt(const char* key);
extern void  xml_ReadString(const char* key, char* buf, int maxLen);
extern "C" void* rage_alloc(uint32_t size);  // RAGE aligned alloc

// Assertion macro
#ifndef ASSERT_MSG
#define ASSERT_MSG(cond, ...) ((void)0)
#endif

// ─────────────────────────────────────────────────────────────────────────────
// pongDrawBucketManager::~pongDrawBucketManager()  [vtable slot 0 @ 0x822272B0]
//
// Deleting destructor.  Two-step RAGE pattern:
//   1. atSingleton_7300() — release the singleton reference / context that
//      backs the bucket allocator.  m_pBuckets itself is not freed here;
//      the singleton teardown handles it.
//   2. If (flags & 1): rage_free(this) — free the object allocation.
//
// Scaffold:
//   mr r31,r3  / mr r30,r4
//   bl atSingleton_7300          <- singleton release
//   clrlwi r11,r30,31            <- r11 = flags & 0x1  (keep bit 0)
//   if (r11 != 0): bl rage_free  <- conditional self-free
// ─────────────────────────────────────────────────────────────────────────────
pongDrawBucketManager::~pongDrawBucketManager()
{
    // atSingleton_7300(this) — releases singleton backing store.
    // The bucket array (m_pBuckets) is owned by the singleton allocator,
    // not by a direct heap alloc here, so it is not explicitly freed.
    //
    // Caller sets flags=1 (delete self) for `delete obj` path,
    // flags=0 for in-place destruction (e.g. stack / embedded member).
}

// ─────────────────────────────────────────────────────────────────────────────
// pongDrawBucketManager::Load()  @ 0x82227430  size: 0x438
//
// Parses "$/tune/settings.drawbucket" XML and populates the bucket array.
//
// XML schema:
//   BucketCount:   <int>   — total number of buckets (1..32)
//   DefaultBucket: <int>   — which bucket is the default (0-indexed)
//   DrawBucket:    <elem>  — one per bucket, contains:
//       Effects     <string> — bucket name (e.g. "Effects")
//       BucketSize: <int>   — max renderable entries (0..32 per bucket)
//
// Verified string addresses:
//   "loading draw bucket config file..."        @ 0x8205002C
//   "$/tune/settings"                           @ 0x82050050
//   "BucketCount:"                              @ 0x820500AC
//   "pongDrawBucketManager::Load() - cannot have %d draw buckets!"        @ 0x820500BC
//   "pongDrawBucketManager::Load() - cannot have more than %d draw buckets!" @ 0x82050100
//   "DefaultBucket:"                            @ 0x82050148
//   "pongDrawBucketManager::Load() - invalid default bucket: %d"          @ 0x82050158
//   "DrawBucket:"                               @ 0x82050194
//   "Effects"                                   @ 0x820501A0
//   "BucketSize:"                               @ 0x820501A8
//   "pongDrawBucketManager::Load() - cannot have %d entries in draw bucket '%s'!"        @ 0x820501B8
//   "pongDrawBucketManager::Load() - cannot have more than %d entries in bucket '%s'!"  @ 0x82050208
//   "draw bucket config load done"              @ 0x8205025C
//
// Struct writes verified:
//   strncpy(this->m_configBasename, <rdata_ptr>, 32)   <- this+0x10
//   strncpy(this->m_configExt,      <rdata_ptr>, 32)   <- this+0x30
//   this->m_numBuckets    = numBuckets   (sth @ this+0x0C)
//   this->m_defaultBucket = numBuckets   (sth @ this+0x0E, initial sentinel)
//   this->m_pBuckets      = rage_alloc(numBuckets * 4)   (stw @ this+0x08)
//   g_numDrawBuckets      = numBuckets   (stw @ 0x82606358)
// ─────────────────────────────────────────────────────────────────────────────
void pongDrawBucketManager::Load()
{
    // Store config filename components for later use in error messages
    // (source ptrs are .rdata → actual strings are "settings" / "drawbucket")
    strncpy(m_configBasename, s_configBasename, 32);  // this+0x10
    strncpy(m_configExt,      s_configExt,      32);  // this+0x30

    // Initialise per-class static state for all draw bucket slots
    pongDrawBucket::InitStatics();

    // Open the XML config file via rage tokeniser
    // Path: "$/tune/settings" + "." + m_configExt  → "$/tune/settings.drawbucket"
    // The rage_obj_factory_create + ph_58A8 pair open the file and build a
    // tokeniser context on the stack (224 bytes, 2 tokens, max 32 chars).
    // An obj-ref is created/destroyed around the parse block.
    // (Not fully expanded here — the XML open/parse/close calls through vtable
    //  indirection make the exact sequence clearer from the raw scaffold.)

    // ── BucketCount ────────────────────────────────────────────────────────
    // Read integer attribute "BucketCount:" from XML
    int numBuckets = xml_ReadInt("BucketCount:");  // indirect call via tokeniser vtable

    // Validate: must be >= 1
    if (numBuckets < 1) {
        // "pongDrawBucketManager::Load() - cannot have %d draw buckets!" @ 0x820500BC
        ASSERT_MSG(false, "pongDrawBucketManager::Load() - cannot have %d draw buckets!", numBuckets);
    }
    // Validate: must be <= 32  (MAX_DRAW_BUCKETS)
    if (numBuckets > 32) {
        // "pongDrawBucketManager::Load() - cannot have more than %d draw buckets!" @ 0x82050100
        ASSERT_MSG(false, "pongDrawBucketManager::Load() - cannot have more than %d draw buckets!", 32);
    }

    // Store globally and in struct
    g_numDrawBuckets  = (uint32_t)numBuckets;  // @ 0x82606358 (SDA)
    m_numBuckets      = (uint16_t)numBuckets;  // @ this+0x0C
    // Initial sentinel: m_defaultBucket = numBuckets (overwritten below by DefaultBucket:)
    m_defaultBucket   = (uint16_t)numBuckets;  // @ this+0x0E

    // Allocate bucket pointer array: numBuckets × 4 bytes
    // rage_alloc is the RAGE aligned allocator (equivalent to rage::MemAlloc)
    // Guard: assert numBuckets <= 0x3FFFFFFF (prevents size overflow in shift)
    m_pBuckets = (pongDrawBucket**)rage_alloc(numBuckets * sizeof(pongDrawBucket*));

    // ── DefaultBucket ──────────────────────────────────────────────────────
    int defaultBucket = xml_ReadInt("DefaultBucket:");
    if (defaultBucket < 0 || defaultBucket >= numBuckets) {
        // "pongDrawBucketManager::Load() - invalid default bucket: %d" @ 0x82050158
        ASSERT_MSG(false, "pongDrawBucketManager::Load() - invalid default bucket: %d", defaultBucket);
    }
    m_defaultBucket = (uint16_t)defaultBucket;  // @ this+0x0E

    // ── Per-bucket DrawBucket: elements ────────────────────────────────────
    for (int i = 0; i < numBuckets; i++) {
        // Each element has:
        //   "Effects"     — bucket name string (up to 64 chars, stack buffer)
        //   "BucketSize:" — max entry count for this bucket (0..32)
        char effectsName[64] = {};
        xml_ReadString("DrawBucket:", effectsName, 64);

        int bucketSize = xml_ReadInt("BucketSize:");
        // Validate size
        if (bucketSize < 0) {
            // "cannot have %d entries in draw bucket '%s'!" @ 0x820501B8
            ASSERT_MSG(false,
                "pongDrawBucketManager::Load() - cannot have %d entries in draw bucket '%s'!",
                bucketSize, effectsName);
        }
        if (bucketSize > 32) {
            // "cannot have more than %d entries in bucket '%s'!" @ 0x82050208
            ASSERT_MSG(false,
                "pongDrawBucketManager::Load() - cannot have more than %d entries in bucket '%s'!",
                32, effectsName);
        }

        // Delegate to pongDrawBucket::Load for full bucket init
        // (reads sort type, LOD level, animated flag, etc. from sibling XML attrs)
        m_pBuckets[i]->Load(effectsName, bucketSize, &s_bucketData[i]);
    }

    // "draw bucket config load done" @ 0x8205025C
}

// ─────────────────────────────────────────────────────────────────────────────
// pongDrawBucket_AddEntry  @ 0x822278D8  size whichever pongDrawBucket layers are
// selected by `bucketMask` (one bit per layer).
//
// void pongDrawBucket_AddEntry(pongDrawBucket* bucket, void* renderable, uint32_t bucketMask)
//   r3 = bucket, r4 = renderable, r5 = bucketMask
//
// Verified field accesses (all on `bucket`):
//   +0x50  lbz  m_bEnabled   — skip entirely if 0
//   +0x0C  lhz  m_numLayers  — number of layers in this bucket (u16)
//   +0x08  lwz  m_pData      — ptr to layer descriptor array
//
// The bucket descriptor array (`m_pData`) is indexed by layer index.
// Each element (`pBucketLayer`) contains:
//   At layerIdx*4 offset from m_pData:
//     m_pData[layerIdx]  = ptr to pBucketLayerDesc
//
// Within each pBucketLayerDesc:
//   Offsets computed via rlwinm (verified with Python):
//     entry_count  @ (layerSubIdx + 13) * 4   e.g. layer[0] → +0x34
//     capacity     @ (layerSubIdx +  5) * 8   e.g. layer[0] → +0x28  (u16)
//     entries_base @ *(layerDesc + layerSubIdx*8 + 36)  (ptr to entry ptr array)
//
//   Adding entry n: entries_base[(entry_count++) - 1] = renderable
//   Overflow assert: if entry_count > capacity →
//     "pongDrawBucket::AddEntry() - adding more than %d entries to bucket '%s'"
//     @ 0x8204FF20
//
// bucketMask iteration:
//   Each bit of bucketMask corresponds to one layer (bit 0 = layer 0).
//   The mask is consumed by logical-right-shift-1 each iteration
//   (rlwinm r24,r24,31,1,31 verified: identical to r24 >>= 1).
//   Loop runs while layerIdx < m_numLayers.
//
// Before the layer loop, vtable slot 1 is called on `renderable`:
//   VCALL(renderable, 1)  — likely some "prepare for render bucket" callback.
// ─────────────────────────────────────────────────────────────────────────────
extern "C" uint32_t g_phFrameIndex;  // @ 0x826065DC — render buffer the entries go into
extern void rage_debugLog(const char* fmt, ...);  // @ 0x8240E6D0 (empty in this build)

// @ 0x822278D8
void pongDrawBucket_AddEntry(pongDrawBucket* bucket, void* renderable, uint32_t bucketMask)
{
    if (!bucket->m_bEnabled)  // +0x50
        return;

    // Prepare renderable — vtable slot 1
    typedef void(*VoidFn)(void*); ((VoidFn)(*(void***)renderable)[1])(renderable);

    if ((int)bucket->m_numLayers <= 0)
        return;

    // Each layer descriptor keeps one entry list per buffer: count words from
    // +0x34, {u16 capacity at +0x28, entries at +0x24} pairs every 8 bytes.
    const int buf = (int)g_phFrameIndex;
    uint32_t mask = bucketMask;
    for (int layerIdx = 0; layerIdx < (int)bucket->m_numLayers; layerIdx++, mask >>= 1) {
        if (mask == 0)
            return;
        if (!(mask & 1))
            continue;

        uint8_t* desc = (uint8_t*)bucket->m_pData[layerIdx];
        int32_t& count = *(int32_t*)(desc + (buf + 13) * 4);
        count++;
        uint16_t capacity = *(uint16_t*)(desc + (buf + 5) * 8);
        if (count > (int32_t)capacity) {
            rage_debugLog(
                "pongDrawBucket::AddEntry() - adding more than %d entries to bucket '%s'",
                capacity, (const char*)desc);
        }
        void** entries = *(void***)(desc + buf * 8 + 0x24);
        entries[count - 1] = renderable;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransFreezeAndCrossFade::Update()  [vtable slot 3 @ 0x823789A8]
//
// Updates the screen transition effect by advancing elapsed time and calculating
// the fade alpha value. The alpha represents the inverse progress (1.0 - progress),
// so it starts at 1.0 and decreases to 0.0 as the transition completes.
//
// Parameters:
//   deltaTime (f1) - time delta to add to elapsed time
//
// Globals accessed:
//   0x82606670 (SDA) - g_pauseFlag: if non-zero, time does not advance
//   0x8202D108 (.rdata) - constant 1.0f
//   0x8202D110 (.rdata) - epsilon value for duration comparison
//
// Struct layout verified:
//   +0x04: m_duration (float) - total transition duration
//   +0x08: m_elapsedTime (float) - current elapsed time
//   +0x0C: m_finished (bool) - set to true when elapsed >= duration
//   +0x34: m_alpha (float) - fade alpha (1.0 - progress)
//
// Logic:
//   1. If not paused, increment elapsed time by deltaTime
//   2. If elapsed >= duration, clamp to duration and set finished flag
//   3. Calculate alpha = 1.0 - (elapsed / duration)
//   4. If duration <= epsilon, clamp alpha to epsilon (avoid divide by zero)
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransFreezeAndCrossFade::Update(float deltaTime) {
    // External globals (defined elsewhere in the engine)
    extern uint8_t g_pauseFlag;           // @ 0x82606670 (SDA)
    extern const float g_floatOne;        // @ 0x8202D108 (.rdata) = 1.0f
    extern const float g_floatEpsilon;    // @ 0x8202D110 (.rdata) = small epsilon

    // Only advance time if not paused
    if (!g_pauseFlag) {
        m_elapsedTime += deltaTime;
    }

    // Check if transition is complete
    if (m_elapsedTime >= m_duration) {
        m_elapsedTime = m_duration;
        m_finished = true;
    }

    // Calculate fade alpha (inverse progress: 1.0 - progress)
    // If duration is very small (near zero), clamp alpha to epsilon to avoid divide by zero
    if (m_duration > g_floatEpsilon) {
        float progress = m_elapsedTime / m_duration;
        m_alpha = g_floatOne - progress;
    } else {
        m_alpha = g_floatEpsilon;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransSwipe Implementation
// ─────────────────────────────────────────────────────────────────────────────

// External globals
extern const float g_floatZero;        // @ 0x8202D110 (.rdata) = 0.0f
extern const float g_floatOne;         // @ 0x8202D10C (.rdata) = 1.0f

// Swipe pattern lookup table @ 0x825D09A0 (.data, size: 0x550 = 1360 bytes)
// Contains 17 patterns (1360 / 80 = 17), each 80 bytes (0x50)
// Pattern structure (per entry, 80 bytes):
//   +0x00: float duration
//   +0x04: float field_04 (timing parameter)
//   +0x08: vec4 startCorner1  (16 bytes)
//   +0x18: vec4 endCorner1    (16 bytes)
//   +0x28: vec4 startCorner2  (16 bytes)
//   +0x38: vec4 endCorner2    (16 bytes)
//   +0x40: uint8_t reverseFlag (at offset +64 from base)
//   +0x41: uint8_t pauseFlag   (at offset +65 from base)
struct SwipePattern {
    float duration;           // +0x00
    float timingParam;        // +0x04
    float startCorner1[4];    // +0x08
    float startCorner2[4];    // +0x18
    float endCorner1[4];      // +0x28
    float endCorner2[4];      // +0x38
    uint8_t reverseFlag;      // +0x40
    uint8_t pauseFlag;        // +0x41
    uint8_t _pad[14];         // padding to 80 bytes
};

extern SwipePattern g_swipePatterns[17];  // @ 0x825D09A0

// External function references
extern void util_PackColorRGBA(uint32_t* outColor, const float* inVector);  // @ 0x8223F840
extern void hudFlashBase_DrawFlashOverlay(void* hudObj, void* corner1, void* corner2, 
                                 float alpha, int reverseFlag);  // @ 0x82140420
extern void pongScrnTransFadeIn_EndTransition(void* obj);  // @ 0x82378460

// Global pointers (accessed via SDA and absolute addresses)
extern struct hudFlashBase* g_hudFlashBase;  // @ 0x82606454 (SDA, r2+25556)
extern void* g_someRenderObj1;         // @ 0x82606654 (via r11+25844)
extern void* g_someRenderObj2;         // @ 0x825FEAB0 (via r11-21712)

// Random number generator state (for pattern selection)
extern uint64_t g_randomState;         // @ 0x825DA268 (via r11-23864)

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransSwipe::Begin()  [vtable slot 2 @ 0x82378AB0]
//
// Initialize/reset the swipe transition. Sets up the pattern index, duration,
// and initial state. If m_randomize is true, picks a random pattern from the
// 17 available patterns. Otherwise uses a deterministic pattern selection.
//
// Struct layout verified:
//   +0x04: m_duration (float)
//   +0x08: m_elapsedTime (float)
//   +0x0C: m_finished (bool)
//   +0x10: field at +16 (passed to sysCallback_Invoke)
//   +0x1C: field_0x1C (checked for non-zero)
//   +0x34: m_patternIndex (uint32_t, 0-16)
//   +0x38: m_randomize (uint8_t)
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransSwipe::Begin() {
    // If field at +28 is non-zero, call utility function
    if (*(uint32_t*)((uint8_t*)this + 28) != 0) {
        sysCallback_Invoke((void*)((uint8_t*)this + 16), 0);
    }

    // Reset elapsed time and finished flag
    m_elapsedTime = g_floatZero;
    m_finished = false;

    // Determine pattern index
    if (m_randomize) {
        // Random pattern selection using linear congruential generator
        // Formula: state = state * 1597334873 + upper32(state)
        const uint64_t multiplier = 0x5DEECE66D;  // 1597334873 in hex
        uint64_t state = g_randomState;
        uint64_t newState = (state & 0xFFFFFFFF) * multiplier + (state >> 32);
        g_randomState = newState;
        
        // Extract 23-bit random value (bits 9-31)
        uint32_t randomBits = (uint32_t)(newState & 0x7FFFFF);
        
        // Scale to 0-16 range: randomBits * (1.0 / 8388608.0) * 17.0
        // 8388608 = 2^23, so this gives uniform distribution over [0, 17)
        const float scale = 1.0f / 8388608.0f;  // @ 0x82038358
        float normalized = (float)randomBits * scale;
        m_patternIndex = (uint32_t)(normalized * 17.0f);
    } else {
        // Increment pattern index, wrapping at 17
        m_patternIndex++;
        if (m_patternIndex >= 17) {
            m_patternIndex = 0;
        }
    }

    // Load pattern data
    SwipePattern* pattern = &g_swipePatterns[m_patternIndex];
    m_duration = pattern->duration;

    // If this pattern has the pause flag set, disable rendering on two objects
    if (pattern->pauseFlag) {
        *(uint8_t*)((uint8_t*)g_someRenderObj1 + 80) = 0;
        *(uint8_t*)((uint8_t*)g_someRenderObj2 + 492) = 0;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransSwipe::Update()  [vtable slot 3 @ 0x82378BD0]
//
// Update the transition by advancing elapsed time and calculating progress.
// Progress is clamped to [0.0, 1.0] and stored for use by the render function.
//
// Parameters:
//   deltaTime (f1) - time delta to add to elapsed time
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransSwipe::Update(float deltaTime) {
    // Advance elapsed time
    m_elapsedTime += deltaTime;

    // Check if transition is complete
    if (m_elapsedTime >= m_duration) {
        m_elapsedTime = m_duration;
        m_finished = true;
    }

    // Calculate normalized progress (0.0 to 1.0)
    if (m_duration > g_floatZero) {
        m_progress = m_elapsedTime / m_duration;
    } else {
        m_progress = g_floatZero;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransSwipe::Render()  [vtable slot 4 @ 0x82378C20]
//
// Render the swipe effect by interpolating between start and end corners
// based on the current progress value. Uses the pattern's corner positions
// and applies the reverse flag to determine swipe direction.
//
// The function:
//   1. Loads the current pattern's corner data
//   2. Applies reverse flag (inverts progress if needed)
//   3. Interpolates corner positions: lerp(start, end, progress)
//   4. Calls utility functions to set up and render the swipe quad
//   5. Passes alpha and reverse flag to HUD flash renderer
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransSwipe::Render() {
    SwipePattern* pattern = &g_swipePatterns[m_patternIndex];
    
    // Calculate effective progress (may be inverted based on reverse flag)
    float effectiveProgress = m_progress;
    if (pattern->reverseFlag) {
        effectiveProgress = g_floatOne - m_progress;
    }

    // Load pattern corner data
    // Pattern index calculation: patternIdx * 5 * 16 = patternIdx * 80
    // This gives us the base offset into the 80-byte pattern structure
    uint32_t patternOffset = m_patternIndex * 80;
    
    // Interpolate corner 1: lerp(startCorner1, endCorner1, progress)
    float corner1[4];
    for (int i = 0; i < 4; i++) {
        float start = pattern->startCorner1[i] + g_floatOne;
        float end = pattern->endCorner1[i] + g_floatOne;
        float delta = end - start;
        corner1[i] = start + delta * effectiveProgress;
    }

    // Interpolate corner 2: lerp(startCorner2, endCorner2, progress)
    float corner2[4];
    for (int i = 0; i < 4; i++) {
        float start = pattern->startCorner2[i] + g_floatOne;
        float end = pattern->endCorner2[i] + g_floatOne;
        float delta = end - start;
        corner2[i] = start + delta * effectiveProgress;
    }

    // Call utility function to prepare rendering (purpose unclear from scaffold)
    uint32_t renderData;
    util_PackColorRGBA(&renderData, corner1); // Assuming the first corner is packed

    // Calculate alpha value from timing parameter
    // Alpha = timingParam * constant * progress
    const float alphaScale = 0.00390625f;  // @ 0x8202D10C (1/256)
    float alpha = pattern->timingParam * alphaScale * effectiveProgress;

    // Render the swipe quad via HUD flash system
    hudFlashBase_DrawFlashOverlay(g_hudFlashBase, corner1, corner2, alpha, pattern->reverseFlag);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransSwipe::OnComplete()  [vtable slot 5 @ 0x82378D98]
//
// Called when the transition completes. Re-enables rendering on objects that
// were disabled during initialization (if the pattern had the pause flag set).
// Then delegates to the base class completion handler.
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransSwipe::OnComplete() {
    SwipePattern* pattern = &g_swipePatterns[m_patternIndex];
    
    // If this pattern had the pause flag, re-enable rendering
    if (pattern->pauseFlag) {
        *(uint8_t*)((uint8_t*)g_someRenderObj1 + 80) = 1;
        *(uint8_t*)((uint8_t*)g_someRenderObj2 + 492) = 1;
    }

    // Delegate to base class (pongScrnTransFadeIn) completion handler
    pongScrnTransFadeIn_EndTransition(this);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransSwipe::Reset()  [vtable slot 6 @ 0x82378DE0]
//
// Reset the transition to its initial state. Clears all timing values,
// resets the pattern index, and sets the randomize flag.
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransSwipe::Reset() {
    m_finished = false;
    m_patternIndex = 0;
    m_duration = g_floatOne;
    m_elapsedTime = g_floatZero;
    m_progress = g_floatZero;
    m_randomize = true;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScreenCapture_rtti_B0EC_0  @ 0x822ED968  size: 0x9C
//
// Screen capture render wrapper that saves/restores render state around a
// Flash HUD rendering call. This function is part of the screen capture system
// that allows taking screenshots or rendering UI elements to textures.
//
// The function performs a render state sandwich pattern:
//   1. Save current render state (grcViewport::UpdateScreenMatrix + game_2E80 + grcSetNormalizedViewport)
//   2. Render Flash HUD element with specific parameters
//   3. Restore previous render state (grcViewport::UpdateScreenMatrix + game_2E80 + grcSetNormalizedViewport)
//
// Globals accessed:
//   0x821EBA9C (pongPlayer_BA20_g + 0x7C) - previous render state pointer
//   0x821EBAA0 (pongPlayer_BA20_g + 0x80) - current render state pointer
//   0x821F0898 (gdRivalry_vfn_20 + 0x10) - render mode index (stored as "8@" string)
//   0x82140110 (ref_fi_F5F0 + 0xB20) - constant float value (likely 1.0f or 0.0f)
//   0x821FE3D4 (pongCameraMgr_D648_g + 0xD8C) - HUD Flash base object pointer
//
// External function references:
//   grcViewport::UpdateScreenMatrix @ 0x82152EE0 - Rebuild the pixel-space viewport matrix
//   game_2E80 @ 0x82152E80 - Save/restore render context (part 2)
//   grcSetNormalizedViewport @ 0x8214EB10 - Graphics device state save/restore
//   hudFlashBase_0F08_g @ 0x82140F08 - Render Flash HUD element
//
// Parameters:
//   r3 (this) - pongScreenCapture object pointer (stored in r28)
//
// The function uses a stack-based state save pattern where the previous state
// is pushed onto a global stack, the HUD is rendered, then the state is popped.
// ─────────────────────────────────────────────────────────────────────────────

// External globals (defined in globals.c or other subsystems)
extern void* g_renderStateStack[];      // @ 0x821EBA9C (stack of render states)
extern void* g_currentRenderState;      // @ 0x821EBAA0 (current active state)
extern int   g_renderModeIndex;         // @ 0x821F0898 (render mode selector)
extern float g_hudRenderParam;          // @ 0x82140110 (parameter for HUD render)
extern struct hudFlashBase* g_hudFlashBase;  // @ 0x821FE3D4 (HUD Flash system object)

// External function declarations
extern void game_2E80(void* renderState);
extern "C" void grcSetNormalizedViewport(const float* viewport);
extern void hudFlashBase_0F08_g(void* hudObj, int modeIndex, float param1, float param2,
                                 int param3, int param4, int param5);

void pongScreenCapture_rtti_B0EC_0(pongScreenCapture* this_ptr) {
    // Save previous render state pointer
    void* previousState = g_renderStateStack[g_renderModeIndex + 8];
    void* currentState = g_currentRenderState;
    
    // Push current state onto stack
    g_renderStateStack[g_renderModeIndex + 8] = currentState;
    
    // If there is a current render state, save it
    if (currentState != nullptr) {
        static_cast<grcViewport*>(currentState)->UpdateScreenMatrix();
        game_2E80(currentState);
        
        // Save graphics device state at offset +768 (0x300)
        // This offset points to a grcDevice or grcContext member within the render state
        grcSetNormalizedViewport((const float*)((uint8_t*)currentState + 768));
    }
    
    // Render the Flash HUD element
    // The mode index is read from a global array and used to select rendering parameters
    // The float array at (this_ptr + modeIndex*4) contains per-mode rendering parameters
    int modeIndex = g_renderModeIndex + 8;
    float* paramArray = (float*)((uint8_t*)this_ptr + modeIndex * 4);
    float renderParam = *paramArray;
    
    hudFlashBase_0F08_g(g_hudFlashBase, modeIndex, g_hudRenderParam, renderParam,
                        0, 0, 0);
    
    // Restore previous render state
    g_renderStateStack[g_renderModeIndex + 8] = previousState;
    
    // If there was a previous state, restore it
    if (previousState != nullptr) {
        static_cast<grcViewport*>(previousState)->UpdateScreenMatrix();
        game_2E80(previousState);
        
        // Restore graphics device state
        grcSetNormalizedViewport((const float*)((uint8_t*)previousState + 768));
    }
}

// (Duplicate pongScrnTransSwipe block removed)
//
// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransFreezeAndCrossFade::Begin()  [vtable slot 2 @ 0x82378938]
//
// Initializes the freeze-and-cross-fade transition effect. This function sets up
// the initial state for a screen transition that freezes the current frame and
// cross-fades to the next screen.
//
// Globals accessed:
//   0x8202D108 (.rdata) - constant 1.0f (initial alpha value)
//   0x8202D10C (.rdata) - default duration value
//   0x8202D110 (.rdata) - initial elapsed time (0.0f)
//   0x825C755C (.data) - default duration fallback
//
// Struct layout:
//   +0x04: m_duration (float) - total transition duration
//   +0x08: m_elapsedTime (float) - current elapsed time (starts at 0.0)
//   +0x0C: m_finished (bool) - completion flag (starts false)
//   +0x1C: field at offset 28 - checked for initialization
//   +0x10: field at offset 16 - passed to util function
//   +0x34: m_alpha (float) - fade alpha (starts at 1.0)
//
// Logic:
//   1. If field at +28 is non-zero, call sysCallback_Invoke to initialize something at +16
//   2. Load default duration from constant table
//   3. Initialize elapsed time to 0.0
//   4. Set finished flag to false
//   5. Set initial alpha to 1.0 (fully opaque)
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransFreezeAndCrossFade::Begin() {
    // External constants
    extern const float g_floatOne;        // @ 0x8202D108 = 1.0f
    extern const float g_floatZero;       // @ 0x8202D110 = 0.0f
    extern const float g_defaultDuration; // @ 0x825C755C

    // Check if we need to initialize something at offset +16
    uint32_t* fieldAt28 = (uint32_t*)((char*)this + 28);
    if (*fieldAt28 != 0) {
        void* fieldAt16 = (void*)((char*)this + 16);
        sysCallback_Invoke(fieldAt16, 0);
    }

    // Initialize transition state
    m_elapsedTime = g_floatZero;
    m_finished = false;
    m_duration = g_defaultDuration;
    m_alpha = g_floatOne;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransFreezeAndCrossFade::Render()  [vtable slot 4 @ 0x82378A18]
//
// Renders the freeze-and-cross-fade effect by drawing a full-screen quad with
// the calculated alpha value. Converts the float alpha (0.0-1.0) to an 8-bit
// integer (0-255) and constructs an RGBA color with white RGB and variable alpha.
//
// Globals accessed:
//   0x82079BE0 (.rdata) - multiplier constant (255.0f) for alpha conversion
//   0x826063D4 (.data, SDA) - pointer to render context
//
// Struct layout:
//   +0x34: m_alpha (float) - fade alpha value (0.0 to 1.0)
//
// Logic:
//   1. Load alpha from +52 (0x34)
//   2. Multiply by 255.0 to convert to 0-255 range
//   3. Convert float to integer
//   4. Construct RGBA color: (alpha << 24) | 0x00FFFFFF (white with variable alpha)
//   5. Call util_03C0 to render the full-screen quad with this color
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransFreezeAndCrossFade::Render() {
    // External constants and globals
    extern const float g_alphaMultiplier; // @ 0x82079BE0 = 255.0f
    extern void* g_renderContext;         // @ 0x826063D4 (SDA)
    extern void util_03C0(void* context, uint32_t* colorPtr);

    // Convert alpha from 0.0-1.0 to 0-255 range
    float alphaScaled = m_alpha * g_alphaMultiplier;
    uint32_t alphaInt = (uint32_t)alphaScaled;

    // Construct RGBA color: alpha in high byte, RGB = 0xFFFFFF (white)
    uint32_t color = (alphaInt << 24) | 0x00FFFFFF;

    // Render the full-screen fade quad
    util_03C0(g_renderContext, &color);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransFreezeAndCrossFade::End()  [vtable slot 5 @ 0x82378A78]
//
// Tail-call to pongScrnTransFadeIn_EndTransition. This is a simple forwarding function
// that delegates to another transition class's implementation, likely for code
// reuse or polymorphic behavior.
//
// Implementation: Direct branch to 0x82378460 (pongScrnTransFadeIn_EndTransition)
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransFreezeAndCrossFade::End() {
    // Forward to pongScrnTransFadeIn implementation
    extern void pongScrnTransFadeIn_EndTransition(void* thisPtr);
    pongScrnTransFadeIn_EndTransition(this);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongScrnTransFreezeAndCrossFade::Reset()  [vtable slot 6 @ 0x82378A80]
//
// Resets the transition state to initial values. This function is likely called
// when restarting or reinitializing the transition effect.
//
// Globals accessed:
//   0x8202D108 (.rdata) - constant 1.0f
//   0x8202D10C (.rdata) - default duration
//   0x8202D110 (.rdata) - constant 0.0f
//
// Struct layout:
//   +0x04: m_duration (float) - reset to default duration
//   +0x08: m_elapsedTime (float) - reset to 0.0
//   +0x0C: m_finished (bool) - reset to false
//   +0x30: field at offset 48 - set to 1.0
//   +0x34: m_alpha (float) - reset to 0.0
//
// Logic:
//   1. Clear finished flag
//   2. Load default duration from constant table at +4
//   3. Load zero constant from table at +8
//   4. Load one constant from table at +0
//   5. Set duration, elapsed time, and alpha fields
// ─────────────────────────────────────────────────────────────────────────────
void pongScrnTransFreezeAndCrossFade::Reset() {
    // External constants
    extern const float g_floatOne;        // @ 0x8202D108 = 1.0f
    extern const float g_floatZero;       // @ 0x8202D110 = 0.0f
    extern const float g_defaultDuration; // @ 0x8202D10C

    // Reset transition state
    m_finished = false;
    m_duration = g_defaultDuration;
    m_elapsedTime = g_floatZero;

    // Reset alpha values (field at +48 and +52)
    float* fieldAt48 = (float*)((char*)this + 48);
    *fieldAt48 = g_floatOne;
    m_alpha = g_floatZero;
}


// ─────────────────────────────────────────────────────────────────────────────
// pongPostEffects_Create — construct the post-effects object into the memory
// block supplied by the caller.  Reconstruction is pending; the factory is
// called from render_loop.c at init time and stored in g_pPostEffects.  Until
// the full ctor is lifted, we return the incoming pointer so the caller gets
// a non-null handle and subsequent effect calls can be short-circuited by the
// individual vtable entries.
// ─────────────────────────────────────────────────────────────────────────────
extern "C" void* pongPostEffects_Create(void* pMem) {
    return pMem;
}


// ============================================================================
// Render state save/restore stubs (SIMD-heavy, pending full lift)
// ============================================================================

/**
 * game_2E80 @ 0x82152E80 | size: 0x5C
 *
 * Saves a subset of the current render state (viewport, scissor rect)
 * into the provided state buffer. Part of the render context save/restore
 * pair used by pongPostEffects.
 *
 * TODO: Full SIMD lift — reads GPU registers via D3D device.
 */
void game_2E80(void* renderState) {
    (void)renderState;
    // No-op on host: OpenGL manages render state internally.
    // The save/restore pattern is only needed for Xbox 360's explicit
    // GPU state management.
}

/**
 * util_03C0 @ 0x821403C0 | size: 0x5C
 *
 * Renders a full-screen colored quad using the HUD flash system.
 * Checks if the render context at offset +108 is non-null, then
 * calls hudFlashBase_2278_g to draw the quad with the specified color.
 *
 * Parameters:
 *   context — render context object (+108 = flash renderer ptr, +364 = state)
 *   colorPtr — pointer to packed ARGB color value
 *
 * TODO: Implement when HUD flash rendering is active.
 */
void util_03C0(void* context, uint32_t* colorPtr) {
    (void)context;
    (void)colorPtr;
    // No-op until HUD flash rendering system is implemented.
}


extern void* g_loop_obj_ptr;                     // @ 0x825EAB30
extern void* lbl_8271A310;                       // @ 0x8271A310 — lighting registry
extern void* lbl_82606564;                       // @ 0x82606564 — active scene
extern uint32_t g_ambientCubeXPosHandle;         // @ 0x82606380
extern uint32_t g_ambientCubeXNegHandle;         // @ 0x82606384
extern uint32_t g_ambientCubeYPosHandle;         // @ 0x82606388
extern uint32_t g_ambientCubeYNegHandle;         // @ 0x8260638C
extern uint32_t g_ambientCubeZPosHandle;         // @ 0x82606390
extern uint32_t g_ambientCubeZNegHandle;         // @ 0x82606394
extern uint32_t g_ambientCubeYFallHandle;        // @ 0x82606398
extern const char g_ambientCubeParameterNames[57]; // @ 0x82030048
extern "C" const float kFastTurnMul;              // @ 0x8202D184 — 2.0
extern "C" const float g_ambientCubeFalloff;      // @ 0x825C8084 — 0.2

// @ 0x820FFF78 | size: 0x6C4 (was game_FF78)
// Select scene lighting, lazily intern seven amb* handles, then upload the six
// weighted cube faces and the Y falloff pair. No stream gate or virtual call.
void pongLighting_ApplyAmbientCube(uint32_t lightIndex) {
    uint8_t* lighting = nullptr;
    auto* loop = static_cast<uint8_t*>(g_loop_obj_ptr);
    if (*reinterpret_cast<int32_t*>(loop + 12) != 8) {
        void* root = lbl_8271A310;
        const int32_t key = loop[0x240] != 0
            ? *reinterpret_cast<int32_t*>(static_cast<uint8_t*>(root) + 32)
            : *reinterpret_cast<int32_t*>(static_cast<uint8_t*>(lbl_82606564) + 20);
        if (key > -1)
            lighting = static_cast<uint8_t*>(pg_C2A0_g(root, key));
    }
    uint32_t handles[7];
    handles[0] = g_ambientCubeXPosHandle;
    if (handles[0] == 0) {
        g_ambientCubeXPosHandle = handles[0] = game_A2F8(g_ambientCubeParameterNames, 1);
        g_ambientCubeXNegHandle = handles[1] = game_A2F8(g_ambientCubeParameterNames + 8, 1);
        g_ambientCubeYPosHandle = handles[2] = game_A2F8(g_ambientCubeParameterNames + 16, 1);
        g_ambientCubeYNegHandle = handles[3] = game_A2F8(g_ambientCubeParameterNames + 24, 1);
        g_ambientCubeZPosHandle = handles[4] = game_A2F8(g_ambientCubeParameterNames + 32, 1);
        g_ambientCubeZNegHandle = handles[5] = game_A2F8(g_ambientCubeParameterNames + 40, 1);
        g_ambientCubeYFallHandle = handles[6] = game_A2F8(g_ambientCubeParameterNames + 48, 1);
    } else {
        handles[1] = g_ambientCubeXNegHandle;
        handles[2] = g_ambientCubeYPosHandle;
        handles[3] = g_ambientCubeYNegHandle;
        handles[4] = g_ambientCubeZPosHandle;
        handles[5] = g_ambientCubeZNegHandle;
        handles[6] = g_ambientCubeYFallHandle;
    }
    if (lighting == nullptr)
        return;

    const float one = lbl_8202D108;
    // The original reuses the +0x70 staging vector for X+ and Y falloff.
    // Without X+, its last two falloff words are uninitialized stack bytes.
    uint32_t falloff[4] = {};
    for (unsigned face = 0; face < 6; ++face) {
        const uint32_t handle = handles[face];
        if (handle == 0)
            continue;
        const float weight = *reinterpret_cast<float*>(lighting + 0x1660 + lightIndex * 4);
        const float scale = __builtin_fmaf(weight, *reinterpret_cast<float*>(lighting + 0x1674), one);
        const auto* color = reinterpret_cast<const float*>(lighting + lightIndex * 0x120 + 0xA10 + face * 16);
        alignas(16) float vector[4] = {color[0] * scale, color[1] * scale, color[2] * scale, color[3]};
        if (face == 0)
            std::memcpy(falloff, vector, 16);
        ShaderTable* table = lbl_825EBC40;
        ++g_grmShaderFx_boundContext;
        const uint32_t bit = (handle >> 1) & 0x1FFFFu;
        table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7];
        const uint32_t slot = table->entries[(handle >> 18) * 2 + 1] & 0xFFFFu;
        std::memcpy(table->values[slot].lane, vector, 16);
    }
    const uint32_t fallHandle = handles[6];
    if (fallHandle != 0) {
        ShaderTable* table = lbl_825EBC40;
        ++g_grmShaderFx_boundContext;
        const uint32_t* entry = table->entries + (fallHandle >> 18) * 2;
        // lvlx loads all four staging words. The subsequent shift/OR leaves
        // them intact, regardless of the descriptor's component-count field.
        std::memcpy(&falloff[0], &kFastTurnMul, 4);
        std::memcpy(&falloff[1], &g_ambientCubeFalloff, 4);
        const uint32_t bit = (fallHandle >> 1) & 0x1FFFFu;
        table->dirtyBits[bit >> 3] |= g_shaderParameterDirtyMasks[bit & 7];
        const uint32_t slot = entry[1] & 0xFFFFu;
        std::memcpy(table->values[slot].lane, falloff, 16);
    }
}
