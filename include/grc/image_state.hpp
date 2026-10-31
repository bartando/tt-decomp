#pragma once
#include <cstdint>
#include "rage/shader_parameters.hpp"
struct pongLightState;
extern "C" {
extern uint32_t g_fxCountOnly; // @ 0x825eba84
extern uint32_t g_fxCurrentColor; // @ 0x825ca604
extern uint32_t g_fxVertexCount; // @ 0x825eba88
extern uint32_t g_grcTextureParameter; // @ 0x825eb980
extern uint32_t g_grcResolveDisableWait; // @ 0x82606640
extern uint32_t g_grcResolveForceShaderControl; // @ 0x82606644
extern uint32_t g_grcResolveExtraWaits; // @ 0x82606648
extern uint32_t g_grcResolveSubmit; // @ 0x8260664c
extern uint32_t g_grcResolveSkipShaderControl; // @ 0x82606650
extern uint32_t g_grmShaderInstance_activeEntry; // @ 0x825ebc48
extern uint32_t g_grmShaderInstance_previous; // @ 0x825ebc44
extern uint32_t g_grmUploadOverrideEnabled; // @ 0x825b1f70
extern uint32_t g_grmUploadOverrideLayout; // @ 0x825e784c
extern uint32_t lbl_825EBAAC; // @ 0x825ebaac
extern uint32_t lbl_825EBAB0; // @ 0x825ebab0
extern uint32_t lbl_825EBB18; // @ 0x825ebb18
extern uint32_t lbl_825EBC30; // @ 0x825ebc30
extern uint32_t lbl_825EBC34; // @ 0x825ebc34
extern uintptr_t g_fxVertexCursor; // @ 0x825eba74
extern float g_fxVertexNormalX; // @ 0x825eba6c
extern float g_fxVertexNormalY; // @ 0x825eba80
extern float g_fxVertexNormalZ; // @ 0x825eba8c
extern float g_fxVertexU; // @ 0x825eba78
extern float g_fxVertexV; // @ 0x825eba70
extern float g_swfPixelScaleX; // @ 0x82602824
extern float g_swfPixelScaleY; // @ 0x8260283c
extern const float g_grcLodBiasScale; // @ 0x82079af0
extern const float g_swfAtlasUVScale; // @ 0x820290ec
extern const float lbl_825C4890; // @ 0x825c4890
extern float lbl_825C8078; // @ 0x825c8078
extern uint8_t g_grcUsePendingTexture; // @ 0x825c89e5
extern uint8_t lbl_8260633D; // @ 0x8260633d
extern const uint32_t g_boxFaceIndices[24]; // @ 0x825d4a90
extern const uint32_t g_grcCullModeTable[3]; // @ 0x825d4cc4
extern const uint32_t g_grcColorWriteMaskTable[16]; // @ 0x825d4cd0
extern const uint32_t g_grcCompareFuncTable[8]; // @ 0x825d4d10
extern const uint32_t g_grcFillModeTable[3]; // @ 0x825d4d30
extern const uint32_t g_grcFormatCompareTable[8]; // @ 0x825d4d3c
extern const uint32_t g_grcResolveVertexProgram[15]; // @ 0x8202c12c
extern const uint32_t g_grcResolveViewport[6]; // @ 0x82065ce8
extern const uint32_t g_grcResolveScissor[4]; // @ 0x82065d00
extern uint32_t g_grcAppliedRenderState[22]; // @ 0x825ebb80
extern uint32_t g_grcPendingTextureState[24]; // @ 0x825ebb20
extern uint32_t g_grcAppliedTextureState[24]; // @ 0x825ebab8
extern const uint16_t g_grcResolveFormatInfo[64]; // @ 0x82065c68
extern const int32_t g_grcResolveOrigin[2]; // @ 0x82065e50
extern const float g_grcResolveConstants[2]; // @ 0x8202d10c
extern const float lbl_825CA420[4]; // @ 0x825ca420
extern const float lbl_825CA430[2]; // @ 0x825ca430
extern const float lbl_825D0930[4]; // @ 0x825d0930
extern const float lbl_82606740[4]; // @ 0x82606740
extern const float lbl_8262F650[4]; // @ 0x8262f650
extern float lbl_82619D20[16]; // @ 0x82619d20
extern float lbl_82619D60[16]; // @ 0x82619d60
extern void* g_grcDefaultTexture; // @ 0x825eba20
extern void* lbl_82606564; // @ 0x82606564
extern const ShaderVector lbl_825CA4A8[4];
extern ShaderVector lbl_82617DF0;
extern pongLightState lbl_825CA610;
extern void* lbl_825EBA20; // Alias of g_grcDefaultTexture @ 0x825EBA20
}
