#pragma once
#include <cstddef>
#include <cstdint>

// 16-byte vector as the camera code stores it (xyz + w).
struct CamVec4 {
    float x, y, z, w;
};

// Four 16-byte rows: a = right, b = up, c = forward, d = position (row names from
// the camera machine's value names, see CMtoCSAdapter::PublishCameraMatrix).
// Used both as rage's Matrix34 (w ignored) and as a full 4x4.
struct CamMatrix44 {
    CamVec4 a, b, c, d;
};

// ── grcViewport (no vtable, 0x390 bytes) ──────────────────────────
// Name inferred from RAGE: it holds the camera and view matrices, the
// FOV/aspect/clip block at +0x338 (written by camViewCS::Update) and a
// "current viewport" global (0x825EBAA0) that 0x82153070 re-uploads when this
// viewport is current. pongCameraMgr owns three of them.
struct grcViewport {
    CamMatrix44 m_transformMtx;     // +0x000 - first matrix, copied verbatim
    CamMatrix44 m_cameraMtx;        // +0x040 - camera (world) matrix, copied verbatim
    CamMatrix44 m_transformMtx44;   // +0x080 - first matrix with homogeneous w
    CamMatrix44 m_secondMtx44;      // +0x0C0 - second matrix with homogeneous w
    CamMatrix44 m_modelViewMtx;     // +0x100 - transform * view
    CamMatrix44 m_modelViewProjectionMtx; // +0x140 - model-view * projection
    CamMatrix44 m_cameraMtx44;      // +0x180 - camera matrix with w forced to (0, 0, 0, 1)
    CamMatrix44 m_viewMtx;          // +0x1C0 - inverse of the camera matrix, w forced to (0, 0, 0, 1)
    CamMatrix44 m_viewMtxFlipZ;     // +0x200 - m_viewMtx with its z column negated
    CamMatrix44 m_projectionMtx;    // +0x240
    CamMatrix44 m_modelScreenMtx;   // +0x280 - model-view-projection * screen
    CamMatrix44 m_screenMtx;       // +0x2C0 - pixel scale/translation (third row untouched)
    float       m_normalizedRect[4]; // +0x300 - x, y, width, height
    float       m_screenDepth;     // +0x310
    uint8_t     _pad_0x314[0x0C];
    float       m_viewportScaleX;  // +0x320 - aspect calculation scale
    float       m_viewportScaleY;  // +0x324 - zero selects default aspect
    uint8_t     _pad_0x328[8];
    int32_t     m_windowWidth;     // +0x330 - cached window dimensions
    int32_t     m_windowHeight;    // +0x334
    // Perspective inputs. Writers set all four and m_isPerspective, then call
    // 0x82153598, which builds the projection from them; 0x82153318 calls
    // 0x82153598 again while m_isPerspective is set.
    float       m_fov;              // +0x338
    float       m_aspect;           // +0x33C - 0 = from the window size (0x82143E98)
    float       m_zClipNear;        // +0x340
    float       m_zClipFar;         // +0x344 - z scale = far / (near - far)
    uint8_t     _pad_0x348[0x18];   // +0x348..+0x35F (outputs of 0x82153598)
    uint8_t     m_isPerspective;    // +0x360
    uint8_t     _pad_0x361[0x2F];   // +0x361..+0x38F

    float GetAspectRatio() const;                 // @ 0x82143E98
    void RebuildCompositeMatrices();              // @ 0x82153070
    void UpdateScreenMatrix();                    // @ 0x82152EE0
    void SetTransformMatrices(const CamMatrix44& first, const CamMatrix44& second); // @ 0x821538C0
    void SetCameraMtx(const CamMatrix44& cameraMtx);  // @ 0x821539F0
};
static_assert(sizeof(grcViewport) == 0x390, "grcViewport is 912 bytes");
static_assert(offsetof(grcViewport, m_modelViewMtx) == 0x100, "");
static_assert(offsetof(grcViewport, m_modelViewProjectionMtx) == 0x140, "");
static_assert(offsetof(grcViewport, m_projectionMtx) == 0x240, "");
static_assert(offsetof(grcViewport, m_modelScreenMtx) == 0x280, "");

extern "C" void* g_pCurrentViewport; // @ 0x825EBAA0
