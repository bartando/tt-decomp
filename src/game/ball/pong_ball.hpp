/**
 * pong_ball.hpp — Ball / paddle / robot declarations
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */
#pragma once

#include <stdint.h>

// ── gdBallFudgeData  [vtable @ 0x8203E8FC] ──────────────────────────
struct gdBallFudgeData {
    void** vtable;  // +0x00

    // ── virtual methods ──
    virtual void IsApplicable();    // [20] @ 0x821d9cc0
    virtual void LoadProperties();  // [21] @ 0x821d9d08
    virtual void GetNodeTypeName(); // [22] @ 0x821d9c10
};

// ── gdBallFudgeMgr  [vtable @ 0x8203E960] ──────────────────────────
struct gdBallFudgeMgr {
    void** vtable;  // +0x00
};

// ── gdBallPredictManager  [vtable @ 0x8203DF30] ─────────────────────
struct gdBallPredictManager {
    void** vtable;  // +0x00

    // ── virtual methods ──
    virtual ~gdBallPredictManager(); // [0] @ 0x821d31c8
};

// ── gmBallNode  [vtables @ 0x820571DC (+0x00), 0x82057288 (+0x60), 0x82057298 (+0x80)] ──
// The ball's scene-graph node, 0x150 bytes (ctor 0x822809B8). Its slots 26 and
// 31..40 are sgPhysicalObject's (vtable 0x8204F35C), and the sgTraverse* visitors
// (0x823D9F10..) name slots 23..29: Initialize, Terminate, Reset, Restart, Update,
// PostUpdate, Draw. +0x80 is a msgMsgSink base (its vtable 0x82027B34 is stored
// back there by the destructor); its slot 1 is gmBallNode_HandleMessage. Members are plain functions so no vtable is
// emitted here; each comment gives the slot it fills. Offsets are the game's 32-bit ones.
// Field names in quotes are the ones LoadProperties registers with the XML loader.
struct fxBallTrail;
struct fxBallShadow;
struct fxBallSpinTex;
struct fxBallSplash2D;
struct pongBallInstance;
struct gmBallDrawInst;  // what sgPhysicalObject builds at +0x7C (0x8227F810); see pong_ball.cpp

struct gmBallNode {
    struct Vec4 { float x, y, z, w; };
    struct Matrix34 { Vec4 a, b, c, d; };  // rows a, b, c and the translation d

    void**             vtable;                 // +0x000
    uint8_t            _pad004[0x0C];
    Matrix34           transform;              // +0x010  sgRMDrawable's "Matrix"
    uint8_t            _pad050[0x10];
    void**             renderEntryVtable;      // +0x060
    uint8_t            _pad064[0x0C];
    uint8_t            fixed;                  // +0x070  "Fixed"
    uint8_t            flag71;                 // +0x071  written by sgPhysicalObject slot 35
    uint8_t            _pad072[2];
    pongBallInstance*  inst;                   // +0x074  the ball's phInst, made by CreateInst
    void*              archetype;              // +0x078  copy of inst's archetype
    gmBallDrawInst*    drawInst;               // +0x07C
    void**             sinkVtable;             // +0x080  msgMsgSink base
    float              popFlyMinHeight;        // +0x084  "PopFlyMinHeight"
    uint8_t            storeScale;             // +0x088  SetScale writes `scale` back only when set
    uint8_t            _pad089[3];
    float              scale;                  // +0x08C  "Scale"
    float              visualSpinScale;        // +0x090  "VisualSpinScale"
    // A scale the trail and splash draws multiply by (0x82381BB0, 0x82389490).
    // Message 0x29 fades it to a target over a duration; Update steps the fade.
    float              fxScale;                // +0x094
    float              fxScaleFrom;            // +0x098
    float              fxScaleTo;              // +0x09C
    float              fxFadeDuration;         // +0x0A0
    float              fxFadeTime;             // +0x0A4  seconds into the fade; -1 (0x825C5938) when idle
    uint8_t            effectsHeld;            // +0x0A8  while set, Update keeps the effects reset whenever the
                                               //         ball is active in the level (ctor: 1; messages 0x81E/0x81F
                                               //         set it, 0x821 clears it)
    uint8_t            _pad0A9[3];
    fxBallTrail*       trails[2];              // +0x0AC
    fxBallShadow*      shadow;                 // +0x0B4
    fxBallSpinTex*     spinTex;                // +0x0B8
    fxBallSplash2D*    splash;                 // +0x0BC
    float              gamePace;               // +0x0C0  "GamePace"
    float              gamePaceFactor;         // +0x0C4  "GamePaceFactor"
    float              gamePaceNormalBias;     // +0x0C8  "GamePaceNormalBias"
    float              gamePaceNetworkBias;    // +0x0CC  "GamePaceNetworkBias"
    int32_t            gamePaceStart;          // +0x0D0  "GamePaceStart" (registered as an int)
    float              minGamePaceDelta;       // +0x0D4  "MinGamePaceDelta"
    float              maxGamePaceDelta;       // +0x0D8  "MaxGamePaceDelta"
    float              serveTimeout;           // +0x0DC  "ServeTimeout"
    float              networkFastestBallTravelTime;  // +0x0E0  "NetworkFastestBallTravelTime"
    uint8_t            flagsE4[3];             // +0x0E4  ctor clears them
    uint8_t            _pad0E7[9];
    Matrix34           lastMatrix;             // +0x0F0  the ball's matrix as of the last Update (ctor: identity)
    Vec4               velocity;               // +0x130  (position - last position) / frame time (ctor: 0)
    uint32_t           ballColorVar;           // +0x140  handle of the "Ball_Color" shader global
    uint8_t            _pad144[0x0C];

    gmBallNode*       ScalarDtor(int flags);           // [0]  @ 0x82280B18
    const char*       GetTypeName();                   // [19] @ 0x82280940
    bool              IsEventHandled(uint32_t eventHash); // [20] @ 0x822808E8
    void              LoadProperties();                // [21] @ 0x82280B98
    void              Initialize();                    // [23] @ 0x82280D48
    void              Terminate();                     // [24] @ 0x82281368
    void              Reset();                         // [25] @ 0x82281408
    void              Update();                        // [27] @ 0x82281630
    void              Draw();                          // [29] @ 0x82281C10
    pongBallInstance* CreateInst();                    // [37] @ 0x82282430
    void              SetScale(float newScale);        // @ 0x82282318
};

// ── gmBallRobot  [2 vtables — template/MI] ──────────────────────────
class gmBallRobot {
public:
    virtual ~gmBallRobot();                   // [0] @ 0x821120a8
    virtual void HandleEvent(uint16_t eventType); // [1] @ 0x82112160
    static void DestructorThunk(gmBallRobot* ptr); // @ 0x821129c8

private:
    void* m_vtable1;              // +0x000 primary vtable @ 0x82032338
    void* m_vtable2;              // +0x004 secondary vtable @ 0x82032344
    uint8_t m_padding08[8];       // +0x008
    uint8_t m_singletonData[368]; // +0x010 atSingleton base storage
    uint8_t m_audControl3d[176];  // +0x180 audControl3d storage
    void* m_pOwnedObject;         // +0x230
    uint8_t m_isActive;           // +0x21c
    uint8_t m_padding21D[3];      // +0x21d
    void* m_pCharacter;           // +0x220
    void* m_pAnimationData;       // +0x224
    void* m_pMotionClip;          // +0x228
    void* m_pAllocatedObject;     // +0x22c
    void* m_pAnimBuffer1;         // +0x238
    void* m_pAnimBuffer2;         // +0x23c
};

// ── pongBallAudio  [vtable @ 0x82057CDC] ────────────────────────────
struct pongBallAudio {
    void** vtable;  // +0x00

    // ── virtual methods ──
    // Vtable slot 0 is the MSVC scalar-deleting destructor:
    //   takes an extra `flags` arg; low bit triggers operator delete.
    // We expose it as a named method (matches pongPaddle::ScalarDtor).
    virtual void ScalarDtor(int flags);  // [0] @ 0x8228abe0

    // Actual instance destructor body (invoked internally by ScalarDtor).
    ~pongBallAudio();
};

// ── pongBallHit  [vtable @ 0x820573A8] ──────────────────────────────
struct pongBallHit {
    void** vtable;  // +0x00
};

// ── pongBallHitData  [vtable @ 0x8203E59C] ──────────────────────────
struct pongBallHitData {
    void** vtable;              // +0x00
    uint8_t m_payloadLo[194];   // +0x04..0xC5  (serialized fields registered by LoadProperties)
    uint16_t m_flags;           // +0xC6  (W:PostLoadProperties, R:LoadProperties — bit 0x1000 = 'enabled')
    uint8_t m_payloadHi[148];   // +0xC8..0x15B (remaining serialized fields)

    // ── virtual methods ──
    virtual void PostLoadProperties();                     // [2] @ 0x821d6900
    virtual bool IsApplicable(uint32_t contextHash);       // [20] @ 0x821d65c0
    virtual void LoadProperties();                         // [21] @ 0x821d6608
    virtual const char* GetNodeTypeName();                 // [22] @ 0x821d65b0

    void Initialize();
    bool ValidateAttribute(uint32_t attributeHash);
    const char* GetEventName();

    // ── nested helper nodes ──
    struct xmlNodeStructHitZone {
        void** vtable;  // +0x00

        // ── virtual methods ──
        virtual void vfn_5(); // [5] @ 0x821d6930
        virtual void vfn_6(); // [6] @ 0x821d6940
    };

    struct xmlNodeStructSwingType {
        void** vtable;  // +0x00

        // ── virtual methods ──
        virtual void vfn_5(); // [5] @ 0x821d6948
    };
};

// ── pongBallInstance  [2 vtables — template/MI] ─────────────────────
// Confirmed methods: ActivateBall
struct pongBallInstance {
    void** vtable;                 // +0x0000  primary vtable @ 0x8205700C

    // ── named members (derived from access pattern analysis) ──
    uint32_t m_flags;              // +0x0004  (R:22) — general flag word
    uint8_t  m_isActive;           // +0x0005  R:1 W:4 — activation byte read by vfn_24 @ +85
    uint8_t  _pad0x06[2];          // +0x0006
    uint16_t m_slotIndex;          // +0x0008  R:2
    uint8_t  _pad0x0a[2];          // +0x000a
    uint32_t m_typeId;             // +0x000c  R:1
    uint32_t field_0x0010;         // +0x0010
    uint32_t m_ownerIndex;         // +0x0014  R:3 W:1
    uint32_t m_assocHandle;        // +0x0018  R:1
    uint32_t m_assocSecondary;     // +0x001c  R:1
    uint32_t field_0x0020;         // +0x0020
    uint32_t m_linkHandleA;        // +0x0024  R:1
    uint32_t m_linkHandleB;        // +0x0028  R:1
    uint16_t m_stateCode;          // +0x002c  R:1
    uint8_t  _pad0x2e[2];          // +0x002e
    uint32_t m_physicsBlockPtr;    // +0x0030  R:4 W:2
    uint32_t m_physicsSlotIndex;   // +0x0034  R:2
    float    m_speedSquared;       // +0x0038  R:6 W:2 — read @ +56 as float
    uint32_t m_lastHitContext;     // +0x003c  R:2
    uint8_t  _pad0x40[16];         // +0x0040
    uint32_t m_collisionCounter;   // +0x0050  W:2
    uint8_t  _pad0x54;             // +0x0054
    uint8_t  m_hitPolicyFlag;      // +0x0055  R:2 — read by vfn_24 as 'can activate' gate
    uint8_t  _pad0x56[2];          // +0x0056
    uint32_t m_lastImpactPtr;      // +0x0058  R:3
    uint8_t  _pad0x5c[20];         // +0x005c
    uint32_t m_pendingEventA;      // +0x0070  W:1
    uint32_t m_pendingEventB;      // +0x0074  W:1
    uint32_t m_pendingEventC;      // +0x0078  W:1
    uint8_t  _pad0x7c[68];         // +0x007c
    uint32_t m_primaryLinkPtr;     // +0x00c0  R:1 W:1
    uint32_t m_secondaryLinkPtr;   // +0x00c4  R:1 W:1
    uint8_t  _pad0xc8[16712];      // +0x00c8
    uint32_t m_runtimeStateA;      // +0x4210  W:2
    uint32_t m_runtimeStateB;      // +0x4214  W:1
    uint8_t  _pad0x4218[136];      // +0x4218
    uint32_t m_spawnOwnerPtr;      // +0x42a0  W:2 — written by ActivateBall as owner handle (vfn_24 reads as m_primaryLinkPtr at +17072)
    uint32_t m_spawnOwnerAlt;      // +0x42a4  W:1
    uint32_t m_spawnTargetPtr;     // +0x42a8  W:2 — vfn_24 reads at +17076 as m_secondaryLinkPtr
    uint32_t m_spawnTargetAlt;     // +0x42ac  W:2
    uint32_t m_spawnExtraA;        // +0x42b0  W:2
    uint32_t m_spawnExtraB;        // +0x42b4  W:2

    // ── nested POD types used by vtable methods ──
    struct Vec4 { float x, y, z, w; };               // 16-byte vector (XYZ + pad / W)
    struct Mat44 { Vec4 row0, row1, row2, row3; };   // 64-byte matrix stored @ this+0x60

    // ── virtual methods ──
    virtual ~pongBallInstance();                                        // [0] @ 0x8227f990
    virtual Mat44* GetMatrixAt60();                                      // [2] @ 0x82280028 — returns &this->m_matrix
    virtual void SetMatrixAt60(const Mat44* src);                        // [3] @ 0x82280030 — copies src into m_matrix
    virtual void GetCurrentPosition(Vec4* outPos);                       // [4] @ 0x8227ff38 — pulls position from history slot
    virtual void GetCurrentVelocity(Vec4* outVel);                       // [5] @ 0x8227ffb0 — pulls velocity from history slot
    virtual void OnEnter();                                              // [11] @ 0x822c90d0
    virtual void ProcessCollisionAndActivate(pongBallInstance* other);   // [24] @ 0x8227fa48
    virtual int  ValidateCollisionParams3(uint32_t a, uint32_t b, uint32_t c);  // [30] @ 0x8227fa28

    // ── non-virtual methods ──
    void* GetMatrix();                     // [3] @ 0x82280028
    void SetMatrix(const void* sourceData);  // [3] @ 0x82280030
    void GetPosition(void* outPosition);   // [4] @ 0x8227FF38
    void GetVelocity(void* outVelocity);   // [5] @ 0x8227FFB0
    void ProcessCollision(void* gameState);  // @ 0x8227FA48
    int ValidateCollisionParams(int param1, int param2, int param3);  // @ 0x8227FA28
    void* FindObjectByID(uint16_t searchID);  // @ 0x822C1C60
    void UpdatePhysicsState();             // @ 0x8227FDB0
    void ActivateBall(void* activationContext);  // @ 0x822801B8
    void* InitializeFromData(void* initData);  // @ 0x8227F810
    static void SnapshotMatrixToGlobalSlot0(pongBallInstance* ball);  // @ 0x822CD5F0
    static void SnapshotMatrixToGlobalSlot1(pongBallInstance* ball);  // @ 0x822CD690
    void* HandlePlayerHitEvent(void* eventData, void* hitContext);  // @ 0x822C3B80
    bool HandleRemotePlayerHit(void* hitContext);  // @ 0x822D5400
};

// ── pongPaddle  [vtable @ 0x82071678] ───────────────────────────────
struct pongPaddle {
    void** vtable; // +0x00

    // ── virtual methods ──
    virtual ~pongPaddle();          // [0] @ 0x823d4208
    virtual void vfn_1();           // [1] @ 0x823d4488
    virtual void ScalarDtor(int flags); // [2] @ 0x823d4140
};
