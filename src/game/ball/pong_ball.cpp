// pong_ball.cpp — Ball / robot classes | Rockstar Presents Table Tennis (Xbox 360, 2006)

/**
 * gm_ball_robot.cpp — Ball-serving robot implementation
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */

#include "pong_ball.hpp"
#include <cstring>   // memcpy, memset
#include <cmath>     // fabs

// External function declarations
extern void audControl_Destructor(void* obj);  // @ 0x82161568
extern "C" void* rage_alloc(uint32_t size);

namespace rage {
    void  ReleaseSingleton(void* singleton);         // @ 0x821A9420
    void  BindObject(void* obj1, void* obj2, uint32_t param3, uint32_t param4);
}
extern void* mfMotionClipRAGE_B8D8_g(void* clip, uint32_t param2, uint32_t param3, uint32_t param4);

// Global pointers
extern void* g_render_obj_ptr;

namespace {

constexpr uint16_t kEventRobotInit = 2071;
constexpr uint16_t kEventRobotDeactivate = 37;

constexpr uintptr_t kRobotVtablePrimary = 0x82032338u;
constexpr uintptr_t kRobotVtableSecondary = 0x82032344u;
constexpr uintptr_t kSingletonVtablePrimary = 0x820176C4u;
constexpr uintptr_t kSingletonVtableSecondary = 0x82017B34u;
constexpr uintptr_t kAudControlVtable = 0x82035594u;
constexpr uint32_t kCrAnimFrameVtable = 0x8204FCBCu;

constexpr uintptr_t kCharacterLookupKey = 0x8206A770u;
constexpr uintptr_t kAttachmentLookupKey = 0x82032318u;
constexpr uintptr_t kMotionClipLookupKey = 0x82032328u;

struct CrAnimFrameStub {
    uint32_t vtable;
    uint32_t field_0x04;
    uint32_t field_0x08;
    uint16_t field_0x0C;
    uint16_t field_0x0E;
};

int StringCompare(const char* lhs, const char* rhs) {
    if (lhs == rhs) {
        return 0;
    }
    if (lhs == nullptr || rhs == nullptr) {
        return 1;
    }

    while (*lhs != 0 && *lhs == *rhs) {
        ++lhs;
        ++rhs;
    }

    return static_cast<int>(static_cast<unsigned char>(*lhs)) -
           static_cast<int>(static_cast<unsigned char>(*rhs));
}

uint8_t* FindCharacterNode(uint8_t* node, const char* lookupName) {
    while (node != nullptr) {
        const char* candidate = *reinterpret_cast<const char**>(node + 20u);
        if (StringCompare(lookupName, candidate) == 0) {
            return node;
        }
        node = *reinterpret_cast<uint8_t**>(node + 184u);
    }
    return nullptr;
}

void* FindAttachmentObject(uint8_t* node, const char* lookupName) {
    while (node != nullptr) {
        uint8_t* attachment = *reinterpret_cast<uint8_t**>(node + 0u);
        if (attachment != nullptr) {
            const char* candidate = *reinterpret_cast<const char**>(attachment + 32u);
            if (StringCompare(lookupName, candidate) == 0) {
                return attachment;
            }
        }
        node = *reinterpret_cast<uint8_t**>(node + 128u);
    }
    return nullptr;
}

} // namespace

/**
 * gmBallRobot::~gmBallRobot() @ 0x821120A8 | size: 0xB8
 *
 * Destructor for ball robot.
 * Cleans up owned object, member audio control, and singleton registration.
 */
gmBallRobot::~gmBallRobot() {
    if (m_pOwnedObject != nullptr) {
        void** vtable = *(void***)m_pOwnedObject;
        void (*destructor)(void*, int) = reinterpret_cast<void (*)(void*, int)>(vtable[0]);
        destructor(m_pOwnedObject, 1);
    }

    m_vtable1 = reinterpret_cast<void*>(kRobotVtablePrimary);
    m_vtable2 = reinterpret_cast<void*>(kRobotVtableSecondary);

    *reinterpret_cast<void**>(&m_audControl3d[0]) = reinterpret_cast<void*>(kAudControlVtable);
    audControl_Destructor(&m_audControl3d[0]);
    rage::ReleaseSingleton(&m_singletonData[0]);

    m_vtable2 = reinterpret_cast<void*>(kSingletonVtableSecondary);
    m_vtable1 = reinterpret_cast<void*>(kSingletonVtablePrimary);
}

/**
 * gmBallRobot::HandleEvent() @ 0x82112160 | size: 0x20C
 *
 * Event handler for ball robot state changes.
 *
 * Event types:
 *   2071 (0x817): Initialize/activate robot
 *   37 (0x25): Deactivate robot
 */
void gmBallRobot::HandleEvent(uint16_t eventType) {
    if (eventType == kEventRobotInit) {
        auto* renderObj = reinterpret_cast<uint8_t*>(g_render_obj_ptr);
        if (renderObj == nullptr || m_pCharacter != nullptr) {
            return;
        }

        const char* characterLookupName =
            reinterpret_cast<const char*>(static_cast<uintptr_t>(kCharacterLookupKey));
        auto* characterNode = *reinterpret_cast<uint8_t**>(renderObj + 20u);
        characterNode = FindCharacterNode(characterNode, characterLookupName);
        m_pCharacter = characterNode;
        if (m_pCharacter == nullptr) {
            return;
        }

        m_pAnimationData = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(m_pCharacter) + 28u);

        const char* attachmentLookupName =
            reinterpret_cast<const char*>(static_cast<uintptr_t>(kAttachmentLookupKey));
        auto* attachmentNode = *reinterpret_cast<uint8_t**>(reinterpret_cast<uint8_t*>(m_pCharacter) + 148u);
        m_pMotionClip = FindAttachmentObject(attachmentNode, attachmentLookupName);

        m_pAllocatedObject = rage_alloc(16u);
        if (m_pAllocatedObject != nullptr) {
            auto* frame = reinterpret_cast<CrAnimFrameStub*>(m_pAllocatedObject);
            frame->vtable = kCrAnimFrameVtable;
            frame->field_0x04 = 0u;
            frame->field_0x08 = 0u;
            frame->field_0x0C = 0u;
            frame->field_0x0E = 0u;
        }

        rage::BindObject(m_pMotionClip, m_pAllocatedObject, 0u, 1u);

        void* motionClip = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(m_pAnimationData) + 4u);
        void* motionClipData = mfMotionClipRAGE_B8D8_g(
            motionClip,
            static_cast<uint32_t>(kMotionClipLookupKey),
            0u,
            0u);

        const uint32_t boneCount = static_cast<uint32_t>(
            *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(motionClipData) + 20u));
        const uint32_t animBufferBase1 =
            *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(m_pAnimationData) + 12u);
        const uint32_t animBufferBase2 =
            *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(m_pAnimationData) + 20u);

        const uint32_t offset1 = boneCount * 80u;
        const uint32_t offset2 = boneCount * 64u;

        m_pAnimBuffer1 = reinterpret_cast<void*>(static_cast<uintptr_t>(animBufferBase1 + offset1));
        m_pAnimBuffer2 = reinterpret_cast<void*>(static_cast<uintptr_t>(animBufferBase2 + offset2));
        return;
    }

    if (eventType == kEventRobotDeactivate) {
        m_isActive = 0;
    }
}

/**
 * gmBallRobot::DestructorThunk() @ 0x821129C8 | size: 0x8
 *
 * Thunk for secondary base class destructor.
 * Adjusts this pointer by -4 bytes for multiple inheritance.
 */
void gmBallRobot::DestructorThunk(gmBallRobot* ptr) {
    gmBallRobot* adjusted = reinterpret_cast<gmBallRobot*>(reinterpret_cast<uint8_t*>(ptr) - 4u);
    adjusted->~gmBallRobot();
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance vtable implementations
// ─────────────────────────────────────────────────────────────────────────────

/**
 * pongBallInstance::~pongBallInstance() @ 0x8227F990 | size: 0x98
 *
 * Destructor for ball instance.
 * Cleans up owned audio object and releases singleton resources.
 */
pongBallInstance::~pongBallInstance() {
    // Set primary and secondary vtable pointers
    constexpr uintptr_t kBallInstanceVtable1 = 0x8205700Cu;
    constexpr uintptr_t kBallInstanceVtable2 = 0x82057094u;
    
    vtable = reinterpret_cast<void**>(kBallInstanceVtable1);
    
    // Clean up audio object at offset +88
    void* audioObj = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(this) + 88);
    if (audioObj != nullptr) {
        void** audioVtable = *reinterpret_cast<void***>(audioObj);
        void (*destructor)(void*, int) = reinterpret_cast<void (*)(void*, int)>(audioVtable[0]);
        destructor(audioObj, 1);
    }
    
    // Set secondary vtable pointer at offset +80
    constexpr uintptr_t kUtilVtable = 0x82027B34u;
    *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(this) + 80) = reinterpret_cast<void*>(kUtilVtable);
    
    // Call utility cleanup function
    extern void util_8FD0(void* obj);
    util_8FD0(this);
}

/**
 * pongBallInstance::GetMatrix @ 0x82280028 | size: 0x8
 *
 * Returns pointer to the 4x4 transform matrix at offset +96.
 */
void* pongBallInstance::GetMatrix() {
    return reinterpret_cast<uint8_t*>(this) + 96;
}

/**
 * pongBallInstance::SetMatrix @ 0x82280030 | size: 0x40
 *
 * Copies a 4x4 transform matrix (64 bytes) from source into +96.
 */
void pongBallInstance::SetMatrix(const void* sourceData) {
    uint8_t* dest = reinterpret_cast<uint8_t*>(this) + 96;
    const uint8_t* src = reinterpret_cast<const uint8_t*>(sourceData);
    
    // Copy 4 x 16-byte vectors (64 bytes total)
    for (int i = 0; i < 4; ++i) {
        memcpy(dest + (i * 16), src + (i * 16), 16);
    }
}

/**
 * pongBallInstance::GetPosition @ 0x8227FF38 | size: 0x78
 *
 * Gets ball position vector from game state circular buffer.
 */
void pongBallInstance::GetPosition(void* outPosition) {
    extern void* g_game_state_ptr;  // @ 0x8271A2F8
    
    auto* gameState = reinterpret_cast<uint8_t*>(g_game_state_ptr);
    if (gameState == nullptr) {
        // Zero out the output position
        memset(outPosition, 0, 16);
        return;
    }
    
    auto* coreState = *reinterpret_cast<uint8_t**>(gameState + 20);
    int32_t frameCount = *reinterpret_cast<int32_t*>(coreState + 9640);
    
    if (frameCount <= 0) {
        memset(outPosition, 0, 16);
        return;
    }
    
    // Calculate circular buffer index: (frameCount + 1) % 120
    // Using fast modulo: (frameCount + 1) - ((frameCount + 1) / 120) * 120
    int32_t index = (frameCount + 1) % 120;
    int32_t offset = index * 80;  // 80 bytes per entry
    
    uint8_t* bufferBase = coreState + 32;
    uint8_t* entry = bufferBase + offset + 32;  // +32 for position offset within entry
    
    memcpy(outPosition, entry, 16);
}

/**
 * pongBallInstance::GetVelocity @ 0x8227FFB0 | size: 0x78
 *
 * Gets ball velocity vector from game state circular buffer.
 */
void pongBallInstance::GetVelocity(void* outVelocity) {
    extern void* g_game_state_ptr;  // @ 0x8271A2F8
    
    auto* gameState = reinterpret_cast<uint8_t*>(g_game_state_ptr);
    if (gameState == nullptr) {
        memset(outVelocity, 0, 16);
        return;
    }
    
    auto* coreState = *reinterpret_cast<uint8_t**>(gameState + 20);
    int32_t frameCount = *reinterpret_cast<int32_t*>(coreState + 9640);
    
    if (frameCount <= 0) {
        memset(outVelocity, 0, 16);
        return;
    }
    
    // Calculate circular buffer index
    int32_t index = (frameCount + 1) % 120;
    int32_t offset = index * 80;
    
    uint8_t* bufferBase = coreState + 32;
    uint8_t* entry = bufferBase + offset + 48;  // +48 for velocity offset within entry
    
    memcpy(outVelocity, entry, 16);
}

/**
 * pongBallInstance::OnEnter() @ 0x822C90D0 | size: 0x10
 *
 * State machine entry callback.
 * Calls virtual function at slot 16 (likely OnEnterState).
 */
void pongBallInstance::OnEnter() {
    void** vtable = *reinterpret_cast<void***>(this);
    void (*callback)(pongBallInstance*) = reinterpret_cast<void (*)(pongBallInstance*)>(vtable[16]);
    callback(this);
}

/**
 * pongBallInstance::ProcessCollision @ 0x8227FA48 | size: 0x364
 *
 * Complex ball collision/interaction handler.
 * Handles ball-player collisions, activation, and event triggering.
 *
 * KNOWN LIMITATION: 0x364-byte body not lifted in this pass. Dependencies include
 *  - ball collision-detection entry (ph_* query on gameState)
 *  - swing-event dispatcher (see ProcessCollisionAndActivate below)
 *  - physics history-system gate read at +9640
 * Keep as a pass-through stub until the dependencies land.
 */
void pongBallInstance::ProcessCollision(void* gameState) {
    (void)gameState;
}

/**
 * pongBallInstance::ValidateCollisionParams @ 0x8227FA28 | size: 0x20
 *
 * Validates parameters for ball collision operation.
 * Returns 0 if any required parameter is missing.
 */
int pongBallInstance::ValidateCollisionParams(int param1, int param2, int param3) {
    // Check if param1 is zero
    if (param1 == 0) {
        // If param2 is non-zero, return 0
        if (param2 != 0) {
            return 0;
        }
        // If param3 is zero, return early
        if (param3 == 0) {
            return 0;
        }
    }
    
    return 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance additional implementations
// ─────────────────────────────────────────────────────────────────────────────

/**
 * pongBallInstance::FindObjectByID() @ 0x822C1C60 | size: 0x50
 *
 * Searches internal array for object matching given ID.
 * Returns pointer to matching object, or nullptr if not found.
 */
void* pongBallInstance::FindObjectByID(uint16_t searchID) {
    uint16_t arrayCount = *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(this) + 44);
    
    if (arrayCount <= 0) {
        return nullptr;
    }
    
    void** arrayBase = *reinterpret_cast<void***>(reinterpret_cast<uint8_t*>(this) + 40);
    
    for (int i = 0; i < arrayCount; ++i) {
        void* entry = arrayBase[i];
        void* subObject = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(entry) + 4);
        uint16_t objectID = *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(subObject) + 8);
        
        if (objectID == searchID) {
            return arrayBase[i];
        }
    }
    
    return nullptr;
}

/**
 * pongBallInstance::UpdatePhysicsState() @ 0x8227FDB0 | size: 0x184
 *
 * Updates ball physics state based on player interaction and game mode.
 * Handles position interpolation, velocity calculations, and slow-motion effects.
 */
void pongBallInstance::UpdatePhysicsState() {
    extern void* g_game_state_ptr;  // @ 0x8271A2F8
    extern float g_floatZero;       // Common zero constant
    extern float g_physicsScale;    // Physics time scale
    
    auto* gameState = reinterpret_cast<uint8_t*>(g_game_state_ptr);
    uint16_t ballIndex = *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(this) + 8);
    
    // Initialize position vector to zero
    float positionBuffer[4] = { 0.0f, 0.0f, 0.0f, 0.0f };
    
    // Get player state and check if player is active
    auto* playerData = *reinterpret_cast<uint8_t**>(gameState + 4);
    auto* playerState = *reinterpret_cast<uint8_t**>(playerData + 28);
    uint8_t playerFlags = playerState[ballIndex];
    
    bool isPlayerActive = (playerFlags & 0x7) != 0;
    
    if (isPlayerActive) {
        // Get player object via vtable call
        void** vtable = *reinterpret_cast<void***>(playerData);
        void* (*getPlayer)(void*) = reinterpret_cast<void* (*)(void*)>(vtable[4]);
        void* player = getPlayer(playerData);
        
        if (player != nullptr) {
            // Copy player position (16 bytes at offset +224)
            memcpy(positionBuffer, reinterpret_cast<uint8_t*>(player) + 224, 16);
        }
    } else {
        // Use ball's own position via vtable call
        void** vtable = *reinterpret_cast<void***>(this);
        void* (*getPosition)(pongBallInstance*) = reinterpret_cast<void* (*)(pongBallInstance*)>(vtable[2]);
        void* ballPos = getPosition(this);
        memcpy(positionBuffer, ballPos, 16);
    }
    
    // Get ball physics data via vtable call
    void** vtable = *reinterpret_cast<void***>(this);
    void* (*getPhysics)(pongBallInstance*) = reinterpret_cast<void* (*)(pongBallInstance*)>(vtable[2]);
    void* physicsData = getPhysics(this);
    
    // Calculate height difference
    float ballHeight = *reinterpret_cast<float*>(reinterpret_cast<uint8_t*>(physicsData) + 56);
    float targetHeight = positionBuffer[2];  // Z component
    float heightDelta = ballHeight + targetHeight;
    
    // Check if height difference is significant (threshold check)
    constexpr float kHeightThreshold = 0.001f;
    if (fabs(heightDelta) > kHeightThreshold) {
        // Recalculate physics data
        void* physicsData2 = getPhysics(this);
        float currentHeight = *reinterpret_cast<float*>(reinterpret_cast<uint8_t*>(physicsData2) + 56);
        float scaleFactor = currentHeight / heightDelta;
        
        // Check slow-motion state
        extern void* g_slowmo_manager_ptr;  // @ 0x825C6540
        auto* slowmoMgr = reinterpret_cast<uint8_t*>(g_slowmo_manager_ptr);
        bool isSlowMotion = slowmoMgr[576] != 0;
        
        if (!isSlowMotion) {
            // Apply physics scale in normal mode
            float absScale = fabs(scaleFactor);
            float adjustedScale = absScale * g_physicsScale;
            
            // Check if player controller exists
            extern void* g_player_controller_ptr;  // @ 0x825C6564
            auto* controller = reinterpret_cast<uint8_t*>(g_player_controller_ptr);
            void* activePlayer = *reinterpret_cast<void**>(controller + 68);
            
            if (activePlayer != nullptr) {
                // Apply scaled velocity adjustment
                float velocityScale = 1.0f;
                float scaledVelocity[4];
                
                // Scale the position buffer
                for (int i = 0; i < 3; ++i) {
                    scaledVelocity[i] = positionBuffer[i] * velocityScale;
                }
                scaledVelocity[3] = 0.0f;
                
                // Apply to ball physics at offset +64
                extern void game_36E8(void* ball, const float* velocity);
                game_36E8(reinterpret_cast<uint8_t*>(this) + 64, scaledVelocity);
            }
        }
    }
}

/**
 * pongBallInstance::ActivateBall() @ 0x822801B8 | size: 0x1A0
 *
 * Activates the ball for gameplay.
 * Initializes ball state, position, velocity, and triggers activation events.
 */
void pongBallInstance::ActivateBall(void* activationContext) {
    extern void* g_game_state_ptr;  // @ 0x8271A2F8
    extern void rage_DebugLog();
    extern void pongBallInstance_4980_g(void*, int, int, int, int);
    extern void game_AA88(void*);
    extern void game_D500(void*, void*, void*);
    extern void game_DA60();
    extern void game_3860(void*, int, const char*);
    extern void pg_E6E0(int, int, int, int);
    
    // Check if ball is already active
    bool isActive = *reinterpret_cast<uint8_t*>(reinterpret_cast<uint8_t*>(this) + 85) != 0;
    
    if (!isActive) {
        // Debug message: "pongBallInstance::ActivateBall() - ball already active"
        constexpr uintptr_t kDebugString = 0x8203EFF8u;
        rage_DebugLog();  // Debug output function
    }
    
    auto* gameState = reinterpret_cast<uint8_t*>(g_game_state_ptr);
    auto* coreState = *reinterpret_cast<uint8_t**>(gameState + 20);
    int32_t frameCount = *reinterpret_cast<int32_t*>(coreState + 9640);
    
    if (frameCount <= 0) {
        return;
    }
    
    // Get ball index and check player state
    uint16_t ballIndex = *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(this) + 8);
    
    extern void* g_player_manager_ptr;  // @ 0x8271A2D0
    auto* playerMgr = reinterpret_cast<uint8_t*>(g_player_manager_ptr);
    auto* playerState = *reinterpret_cast<uint8_t**>(playerMgr + 28);
    uint8_t stateFlags = playerState[ballIndex];
    
    bool needsInit = (stateFlags & 0x7) == 0;
    
    if (needsInit) {
        // Initialize ball state
        pongBallInstance_4980_g(g_player_manager_ptr, 0, 0, 0, 0);
    }
    
    // Get player object
    void* player = nullptr;
    auto* playerData = *reinterpret_cast<uint8_t**>(playerMgr + 4);
    auto* stateData = *reinterpret_cast<uint8_t**>(playerData + 28);
    uint8_t flags = stateData[ballIndex];
    
    bool hasPlayer = (flags & 0x7) != 0;
    
    if (hasPlayer) {
        void** vtable = *reinterpret_cast<void***>(playerData);
        void* (*getPlayer)(void*) = reinterpret_cast<void* (*)(void*)>(vtable[4]);
        player = getPlayer(playerData);
    }
    
    // Prepare ball for activation
    game_AA88(player);
    
    // Get ball position via vtable
    void** vtable = *reinterpret_cast<void***>(this);
    void* (*getPosition)(pongBallInstance*) = reinterpret_cast<void* (*)(pongBallInstance*)>(vtable[2]);
    void* ballPos = getPosition(this);
    
    // Copy ball position to stack buffer
    float posBuffer[4];
    memcpy(posBuffer, reinterpret_cast<uint8_t*>(this) + 64, 16);
    memcpy(ballPos, posBuffer, 16);
    
    // Calculate velocity vector
    constexpr float kVelocityScale = 0.5f;  // From offset in .rdata
    float velocityBuffer[4];
    
    if (player != nullptr) {
        float* playerPos = reinterpret_cast<float*>(reinterpret_cast<uint8_t*>(player) + 48);
        
        // Calculate direction vector: (ballPos - playerPos) * scale
        for (int i = 0; i < 3; ++i) {
            velocityBuffer[i] = (posBuffer[i] - playerPos[i]) * kVelocityScale;
        }
        velocityBuffer[3] = 0.0f;
        
        // Apply velocity via vtable call
        void** playerVtable = *reinterpret_cast<void***>(player);
        void (*setVelocity)(void*, const float*) = 
            reinterpret_cast<void (*)(void*, const float*)>(playerVtable[40]);
        setVelocity(player, velocityBuffer);
    }
    
    // Handle activation context
    if (activationContext != nullptr) {
        game_D500(activationContext, player, this);
        game_DA60();
    }
    
    // Trigger activation event
    constexpr const char* kActivationEvent = "ball_activated";
    game_3860(gameState, 1, kActivationEvent);
    
    // Send deactivation event (event ID 37, type 64)
    pg_E6E0(37, 64, 0, 0);
}

/**
 * pongBallInstance::InitializeFromData() @ 0x8227F810 | size: 0x60
 *
 * Initializes ball instance from serialized data.
 * Sets up ball state and configuration from data structure.
 */
void* pongBallInstance::InitializeFromData(void* initData) {
    extern void* xe_GetLoadContext();
    extern void util_D150(void*, void*);
    
    // Allocate ball instance
    void* ballInstance = xe_GetLoadContext();
    
    // Initialize from data (copy 16-byte header)
    util_D150(initData, reinterpret_cast<uint8_t*>(initData) + 16);
    
    // Get configuration object
    void* configObj = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(this) + 20);
    void* configData = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(configObj) + 4);
    
    // Get ball data from init structure
    void* ballData = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(ballInstance) + 20);
    
    // Call configuration setup via vtable
    void** vtable = *reinterpret_cast<void***>(configData);
    void (*configure)(void*, void*) = reinterpret_cast<void (*)(void*, void*)>(vtable[6]);
    configure(configData, ballData);
    
    // Set ball state flags
    *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(ballInstance) + 16) = 4;
    *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(ballInstance) + 96) = 0;
    
    return ballInstance;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallHitData vtable implementations
// ─────────────────────────────────────────────────────────────────────────────

/**
 * pongBallHitData::Initialize() @ 0x821D6900 | size: 0x30
 *
 * Initializes hit data structure with default flags.
 * Sets up debug mode flags if enabled.
 */
void pongBallHitData::Initialize() {
    extern uint8_t g_debugMode;  // @ 0x825C64AD
    extern void xmlNodeStruct_Initialize(void*);
    
    // Clear flags at offset +198
    *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(this) + 198) = 0;
    
    uint16_t flags = 0;
    
    // Check if debug mode is enabled
    if (g_debugMode != 0) {
        flags = 4096;  // 0x1000 - debug flag
    }
    
    // Set base flags
    *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(this) + 198) = flags;
    
    // Add additional flags: 0x6000 (24576)
    flags |= 24576;
    *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(this) + 198) = flags;
    
    // Call parent initialization
    xmlNodeStruct_Initialize(this);
}

/**
 * pongBallHitData::ValidateAttribute() @ 0x821D65C0 | size: 0x48
 *
 * Validates XML attribute hash against known attribute types.
 * Returns true if attribute is recognized, false otherwise.
 */
bool pongBallHitData::ValidateAttribute(uint32_t attributeHash) {
    extern uint32_t g_attrHash_HitZone;      // @ 0x825C761C
    extern uint32_t g_attrHash_SwingType1;   // @ 0x825C8038
    extern uint32_t g_attrHash_SwingType2;   // @ 0x825C803C
    
    // Check against known attribute hashes
    if (attributeHash == g_attrHash_HitZone) {
        return true;
    }
    
    if (attributeHash == g_attrHash_SwingType2) {
        return true;
    }
    
    if (attributeHash == g_attrHash_SwingType1) {
        return true;
    }
    
    return false;
}

/**
 * pongBallHitData::GetEventName() @ 0x821D65B0 | size: 0xC
 *
 * Returns the event name string for slow-motion entry.
 * Used for HUD event triggering.
 */
const char* pongBallHitData::GetEventName() {
    return "HUD:SLOMO_ENTER_GENERIC";  // @ 0x8203E464
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallAudio::~pongBallAudio()
//
// Inline destructor body. The binary only ships the MSVC scalar-deleting
// wrapper at vtable slot 0 (@ 0x8228ABE0); that wrapper inlines this body.
// We keep a matching ~pongBallAudio() so both stack-scoped destruction and
// the ScalarDtor thunk share the same teardown logic.
// ─────────────────────────────────────────────────────────────────────────────
pongBallAudio::~pongBallAudio() {
    extern void audControl3d_Destructor(pongBallAudio* obj);  // @ 0x8228AC30 — base dtor
    audControl3d_Destructor(this);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallHit destructor thunk  [rtti_73A8_0 @ 0x822824A8]
// Destructor for pongBallHit — releases singleton data, sets vtable, frees.
// ─────────────────────────────────────────────────────────────────────────────
void pongBallHit_Destructor(pongBallHit* self, int flags) {
    extern void atSingleton_Release(void* obj);  // @ 0x821A9420
    extern void rage_free(void* ptr);            // @ 0x820C00C0

    constexpr uintptr_t kPongBallHitVtable = 0x820573A8u;

    // Release singleton resources at offset +48
    atSingleton_Release(reinterpret_cast<uint8_t*>(self) + 48);

    // Set vtable pointer
    self->vtable = reinterpret_cast<void**>(kPongBallHitVtable);

    // Free memory if flag bit 0 is set
    if (flags & 1) {
        rage_free(self);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance secondary vtable destructor thunk  [rtti_7094_0 @ 0x82280890]
// Adjusts 'this' by -80 to reach primary base, then calls primary destructor.
// ─────────────────────────────────────────────────────────────────────────────
void pongBallInstance_SecondaryDtorThunk(pongBallInstance* secondaryBase) {
    pongBallInstance* primary = reinterpret_cast<pongBallInstance*>(
        reinterpret_cast<uint8_t*>(secondaryBase) - 80);
    primary->~pongBallInstance();
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance::SnapshotMatrixToGlobalSlot0()  [@ 0x822CD5F0]
// Copies ball transform matrix into global ball state array (slot 0 / player 1).
// ─────────────────────────────────────────────────────────────────────────────
void pongBallInstance::SnapshotMatrixToGlobalSlot0(pongBallInstance* ball) {
    // Shared physics collision-pair broadphase scratch at 0x825CBCF0.
    // (See ball collision-pair broadphase seeders section lower in this file
    // for the layout map — same block, same name.)
    extern uint8_t g_pairBroadphaseScratch[];  // @ 0x825CBCF0 (17152 bytes)

    // Get ball's transform matrix via vtable slot 2 (GetMatrix)
    void* matrixPtr = ball->GetMatrix();

    // Read ball's flags to get physics sub-object reference
    uint32_t flagsObj = *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(ball) + 4);
    uint32_t physicsRef = *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(flagsObj) + 12);

    // Store metadata into global state (slot 0)
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 17064) = 0;               // clear status
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 17072) = reinterpret_cast<uintptr_t>(ball); // ball ptr
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 16912) = reinterpret_cast<uintptr_t>(
        reinterpret_cast<uint8_t*>(ball) + 16);                                       // ball data ptr
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 17056) = physicsRef;       // physics reference

    // Copy 4x4 transform matrix (4 x 16-byte rows = 64 bytes)
    const uint8_t* src = reinterpret_cast<const uint8_t*>(matrixPtr);
    memcpy(g_pairBroadphaseScratch + 16928, src,      16);  // row 0
    memcpy(g_pairBroadphaseScratch + 16944, src + 16, 16);  // row 1
    memcpy(g_pairBroadphaseScratch + 16960, src + 32, 16);  // row 2
    memcpy(g_pairBroadphaseScratch + 16976, src + 48, 16);  // row 3
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance::SnapshotMatrixToGlobalSlot1()  [@ 0x822CD690]
// Copies ball transform matrix into global ball state array (slot 1 / player 2).
// ─────────────────────────────────────────────────────────────────────────────
void pongBallInstance::SnapshotMatrixToGlobalSlot1(pongBallInstance* ball) {
    extern uint8_t g_pairBroadphaseScratch[];  // @ 0x825CBCF0

    void* matrixPtr = ball->GetMatrix();

    uint32_t flagsObj = *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(ball) + 4);
    uint32_t physicsRef = *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(flagsObj) + 12);

    // Store metadata into global state (slot 1 — offsets shifted by +4/+64 from slot 0)
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 17068) = 0;
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 17076) = reinterpret_cast<uintptr_t>(ball);
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 16916) = reinterpret_cast<uintptr_t>(
        reinterpret_cast<uint8_t*>(ball) + 16);
    *reinterpret_cast<uint32_t*>(g_pairBroadphaseScratch + 17060) = physicsRef;

    const uint8_t* src = reinterpret_cast<const uint8_t*>(matrixPtr);
    memcpy(g_pairBroadphaseScratch + 16992, src,      16);  // row 0
    memcpy(g_pairBroadphaseScratch + 17008, src + 16, 16);  // row 1
    memcpy(g_pairBroadphaseScratch + 17024, src + 32, 16);  // row 2
    memcpy(g_pairBroadphaseScratch + 17040, src + 48, 16);  // row 3
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance::HandlePlayerHitEvent()  [@ 0x822C3B80]
// Processes a player hit event on the ball — checks player state, resolves
// the ball object, and either dispatches a hit or returns the player object.
// ─────────────────────────────────────────────────────────────────────────────
void* pongBallInstance::HandlePlayerHitEvent(void* eventData, void* hitContext) {
    extern void pongBallInstance_DispatchHit(
        pongBallInstance*, uint16_t, void*, void*, void*, void*, void*);  // @ 0x822C4980

    // Get flags/player-state lookup table
    uint32_t flagsObj = *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(this) + 4);
    uint16_t playerIndex = *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(hitContext) + 8);
    uint8_t* playerStateTable = reinterpret_cast<uint8_t*>(
        *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(flagsObj) + 28));
    uint8_t stateFlags = playerStateTable[playerIndex];

    // Check if player state is exactly 1 (active single player)
    bool isActivePlayer = (stateFlags & 0x7) == 1;

    if (isActivePlayer) {
        // Try to find the ball object by ID
        void* ballObj = FindObjectByID(playerIndex);
        if (ballObj != nullptr) {
            // Check if ball is valid via vtable slot 7
            void** objVtable = *reinterpret_cast<void***>(ballObj);
            bool (*isValid)(void*) = reinterpret_cast<bool (*)(void*)>(objVtable[7]);
            if (!isValid(ballObj)) {
                return nullptr;
            }
        }

        // Dispatch the hit event
        pongBallInstance_DispatchHit(this, playerIndex, nullptr, eventData, nullptr, nullptr, nullptr);
        return nullptr;
    }

    // Player state is not active — check if state is zero (no player)
    uint8_t rawState = playerStateTable[playerIndex];
    bool noPlayer = (rawState & 0x7) == 0;

    if (noPlayer) {
        // Get player object via flags vtable slot 4
        uint32_t flagsObj2 = *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(this) + 4);
        void** fVtable = *reinterpret_cast<void***>(reinterpret_cast<void*>(flagsObj2));
        void* (*getPlayer)(void*) = reinterpret_cast<void* (*)(void*)>(fVtable[4]);
        return getPlayer(reinterpret_cast<void*>(flagsObj2));
    }

    return nullptr;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance::HandleRemotePlayerHit()  [@ 0x822D5400]
// Similar to HandlePlayerHitEvent but for remote/networked player hits.
// Loads ball instance from a global pointer instead of using 'this'.
// ─────────────────────────────────────────────────────────────────────────────
bool pongBallInstance::HandleRemotePlayerHit(void* hitContext) {
    extern uint32_t g_playerManagerPtr;  // @ 0x826065E4 (SDA global)
    extern uint32_t g_ballInstancePtr;   // @ 0x825F5BD0

    extern void pongBallInstance_DispatchHit(
        pongBallInstance*, uint16_t, void*, void*, void*, void*, void*);  // @ 0x822C4980

    // Look up player state from global player manager
    uint32_t playerMgr = *reinterpret_cast<uint32_t*>(&g_playerManagerPtr);
    uint16_t playerIndex = *reinterpret_cast<uint16_t*>(reinterpret_cast<uint8_t*>(hitContext) + 8);
    uint8_t* playerStateTable = reinterpret_cast<uint8_t*>(
        *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(playerMgr) + 28));
    uint8_t stateFlags = playerStateTable[playerIndex];

    bool isActivePlayer = (stateFlags & 0x7) == 1;

    if (!isActivePlayer) {
        // No active player — return true (handled)
        return true;
    }

    // Load ball instance from global
    auto* ballInstance = reinterpret_cast<pongBallInstance*>(
        *reinterpret_cast<uint32_t*>(&g_ballInstancePtr));

    // Try to find ball object by player index
    void* ballObj = ballInstance->FindObjectByID(playerIndex);
    if (ballObj != nullptr) {
        // Check validity via vtable slot 7
        void** objVtable = *reinterpret_cast<void***>(ballObj);
        bool (*isValid)(void*) = reinterpret_cast<bool (*)(void*)>(objVtable[7]);
        if (!isValid(ballObj)) {
            return false;
        }
        // Reload ball instance (may have changed)
        ballInstance = reinterpret_cast<pongBallInstance*>(
            *reinterpret_cast<uint32_t*>(&g_ballInstancePtr));
    }

    // Dispatch hit with caller context
    pongBallInstance_DispatchHit(ballInstance, playerIndex, nullptr, nullptr, nullptr, this, nullptr);

    return (ballInstance != nullptr);  // returns dispatch result
}

// ─────────────────────────────────────────────────────────────────────────────
// gmBallNode::IsEventHandled()  [vtable slot 20 @ 0x822808E8]
// Checks if a given event hash matches any of the 4 known ball event types.
// ─────────────────────────────────────────────────────────────────────────────
bool gmBallNode::IsEventHandled(uint32_t eventHash) {
    extern uint32_t g_eventHash_BallHit;       // @ 0x825C4954
    extern uint32_t g_eventHash_BallBounce;    // @ 0x825C2D74
    extern uint32_t g_eventHash_BallSpin;      // @ 0x825C2D78
    extern uint32_t g_eventHash_BallCollision; // @ 0x825C93D0

    if (eventHash == g_eventHash_BallHit) {
        return true;
    }
    if (eventHash == g_eventHash_BallBounce) {
        return true;
    }
    if (eventHash == g_eventHash_BallSpin) {
        return true;
    }
    if (eventHash == g_eventHash_BallCollision) {
        return true;
    }

    return false;
}

// ─────────────────────────────────────────────────────────────────────────────
// gmBallNode::GetTypeName()  [vtable slot 19 @ 0x82280940]
// Returns the RTTI type name string for this node class.
// ─────────────────────────────────────────────────────────────────────────────
const char* gmBallNode::GetTypeName() {
    // Points to the RTTI type info name at 0x820570A0 (in .rdata)
    return reinterpret_cast<const char*>(0x820570A0u);
}

// ═════════════════════════════════════════════════════════════════════════════
// gmBallNode — the ball's scene-graph node
// ═════════════════════════════════════════════════════════════════════════════
//
// gmBallNode owns the ball's physics instance (the pongBallInstance at +0x74,
// made by CreateInst), its effects (two trails, a shadow, the spin texture and
// a 2D splash) and the game-pace tuning it loads from XML. Initialize builds the
// effects, gives the ball the mass properties of a thin shell and publishes the
// node and its pace settings; Reset puts everything back for a new rally; Draw
// queues the effects; Terminate frees them.
//
// Objects it doesn't own are read through the views in namespace gmball, which
// hold only offsets these functions' asm proves (the game's 32-bit offsets are
// in the comments). Method names on the views say what a call does here; they
// are not proven RAGE names.

namespace gmball {

using Vec4 = gmBallNode::Vec4;

inline Vec4 Splat(float v) { return Vec4{v, v, v, v}; }

// Calls slot `slot` of the object's vtable with the object as `this`.
template <typename R, typename... A>
inline R CallSlot(void* object, int slot, A... args) {
    void** vtable = *static_cast<void***>(object);
    return reinterpret_cast<R (*)(void*, A...)>(vtable[slot])(object, args...);
}

inline void** GameVtable(uintptr_t address) { return reinterpret_cast<void**>(address); }

constexpr uintptr_t kVtable_gmBallNode            = 0x820571DCu;
constexpr uintptr_t kVtable_gmBallNode_renderEnt  = 0x82057288u;  // +0x60
constexpr uintptr_t kVtable_gmBallNode_sink       = 0x82057298u;  // +0x80
constexpr uintptr_t kVtable_msgMsgSink            = 0x82027B34u;
constexpr uintptr_t kVtable_pongRenderable        = 0x82032404u;
constexpr uintptr_t kVtable_fxBallShadow          = 0x82057188u;
constexpr uintptr_t kVtable_fxBallSpin            = 0x8206B3B0u;
constexpr uintptr_t kVtable_fxBallSpin_sink       = 0x8206B3D0u;
constexpr uintptr_t kVtable_fxBallSpinTex         = 0x820572A8u;
constexpr uintptr_t kVtable_fxBallSpinTex_sink    = 0x820572CCu;
constexpr uintptr_t kVtable_fxBallSplash2D        = 0x82057198u;
constexpr uintptr_t kVtable_fxBallSplash2D_render = 0x820571A8u;

// ── Memory ──────────────────────────────────────────────────────────────────
// `new` is inlined everywhere: make sure the thread has an allocator
// (0x820C0038), then call slot 1 of the allocator in TLS word 1.
struct AllocatorView {
    void** vtable;
    void* Allocate(uint32_t size, uint32_t align) { return CallSlot<void*>(this, 1, size, align); }
};

// ── Physics ─────────────────────────────────────────────────────────────────
struct BoundView {                 // rage::phBound
    void**  vtable;                // +0x00
    uint32_t _04;
    float   radius;                // +0x08  Initialize's inertia reads it; SetScale writes it
    uint8_t _pad0C[0x64];
    Vec4    radiusSplat;           // +0x70  phBoundSphere only: the radius in all four lanes

    // Slot 37, called after SetScale changes the radius (presumably refits the bound).
    void RadiusChanged() { CallSlot<void>(this, 37); }
};

struct ArchetypeView {             // rage::phArchetype
    void**     vtable;             // +0x00
    uint8_t    _pad04[8];
    BoundView* bound;              // +0x0C
    uint32_t   typeFlags;          // +0x10
    uint32_t   includeFlags;       // +0x14

    // Slot 7: inferred to be the mass (Initialize multiplies it by r² · 2/3).
    float GetMass() { return CallSlot<float>(this, 7); }
    // Slot 14: takes the three diagonal inertia terms.
    void SetAngInertia(const float* inertia) { CallSlot<void>(this, 14, inertia); }
};

struct BallAudioView {             // pongBallAudio (0x340 bytes, made by 0x8228A7D8)
    uint8_t  _pad000[0x32C];
    uint32_t word32C;              // +0x32C  Reset clears it
};

struct BallInstView {              // pongBallInstance (ctor 0x8227F870), a rage::phInst
    void**          vtable;        // +0x00
    ArchetypeView*  archetype;     // +0x04
    uint16_t        levelIndex;    // +0x08
    uint8_t         _pad0A[0x4B];
    uint8_t         flag55;        // +0x55  ctor and Reset set it to 1
    uint8_t         _pad56[2];
    BallAudioView*  audio;         // +0x58
};

inline BallInstView* View(pongBallInstance* inst) { return reinterpret_cast<BallInstView*>(inst); }

struct ColliderView {              // what the level hands back for an active object
    uint8_t _pad00[0x94];
    float   maxAngularSpeed;       // +0x94  inferred: Initialize stores 40π here
};

struct LevelView {                 // rage::phLevelNew
    void**   vtable;               // +0x00
    uint8_t  _pad04[0x18];
    uint8_t* objectStates;         // +0x1C  one byte per level index; low 3 bits 0 = active

    bool IsActive(uint16_t index) const { return (objectStates[index] & 7) == 0; }
    ColliderView* GetActiveCollider(uint16_t index) { return CallSlot<ColliderView*>(this, 4, index); }
};

struct SimulatorView {             // rage::phSimulator
    void**     vtable;             // +0x00
    LevelView* level;              // +0x04
};

// ── Effects ─────────────────────────────────────────────────────────────────
// pongRenderable (vtable 0x82032404): each effect's constructor starts with
// these three stores.
struct RenderableView {
    void**  vtable;                // +0x00
    float   sortValue;             // +0x04  inferred: Draw sets it right before queuing
    int32_t field08;               // +0x08  ctor: 0
    int32_t field0C;               // +0x0C  ctor: -1
};

inline void ConstructRenderable(RenderableView* r) {
    r->sortValue = 0.0f;
    r->field08 = 0;
    r->field0C = -1;
}

// fxBallTrail (vtable 0x820571B8, 0xB4D0 bytes)
inline void Trail_Draw(fxBallTrail* t)  { CallSlot<void>(t, 1); }  // 0x82382230
inline void Trail_Reset(fxBallTrail* t) { CallSlot<void>(t, 2); }  // 0x82381150; its ctor calls it too
// 0x82381208: stores intensity at +0xB470, data at +0x3C2C and entry type+1 of
// the table at *0x8271A394 at +0x3C28.
inline void Trail_Setup(fxBallTrail* t, int32_t type, int32_t intensity, void* data) {
    CallSlot<void>(t, 3, type, intensity, data);
}

// fxBallSpinTex : fxBallSpin : pongRenderable, with a msgMsgSink base at +0x10 (0x1A0 bytes)
struct SpinTexView {
    RenderableView renderable;     // +0x00
    void**         sinkVtable;     // +0x10
    void*          texture;        // +0x14  slot 4 stores its argument here
    uint8_t        flag18;         // +0x18  ctor: 1
    uint8_t        flag19;         // +0x19  ctor: 1
    uint8_t        _pad1A[2];
    float          f1C;            // +0x1C  ctor: 1
    float          f20;            // +0x20  ctor: 1
    float          f24;            // +0x24  ctor: 1
    uint8_t        _pad28[0x88];
    Vec4           vecB0[6];       // +0xB0  ctor: 0
};

inline void SpinTex_Draw(fxBallSpinTex* s)     { CallSlot<void>(s, 1); }  // 0x82388B70
inline void SpinTex_Register(fxBallSpinTex* s) { CallSlot<void>(s, 2); }  // 0x82388978
inline void SpinTex_Reset(fxBallSpinTex* s)    { CallSlot<void>(s, 3); }  // 0x82388C58
inline void SpinTex_SetTexture(fxBallSpinTex* s, void* texture) { CallSlot<void>(s, 4, texture); }  // 0x82280898

// fxBallSplash2D: msgMsgSink at +0 (slot 1, 0x82389C50, handles the messages),
// pongRenderable at +4 (0x240 bytes)
struct Splash2DView {
    void**         vtable;         // +0x00
    RenderableView renderable;     // +0x04
    uint8_t        _pad14[0xAC];
    struct Mark { uint8_t active; uint8_t _pad[0x4F]; };
    Mark           marks[4];       // +0xC0  0x50 apart
};

inline RenderableView* AsRenderable(fxBallSplash2D* splash) {
    return splash ? &reinterpret_cast<Splash2DView*>(splash)->renderable : nullptr;
}

// ── Other objects ───────────────────────────────────────────────────────────
// The object sgPhysicalObject builds next to the instance (0x8227F810 sets its
// +0x10 to 4 and +0x60 to 0).
struct DrawInstView {
    void**   vtable;               // +0x00
    uint8_t  _pad04[8];
    uint32_t mode0C;               // +0x0C  Initialize sets 2
    uint8_t  _pad10[0x50];
    void*    drawable60;           // +0x60  Draw draws it only when set
    uint8_t  _pad64[0x0C];
    Vec4     scale;                // +0x70  SetScale splats the scale here

    void Draw() { CallSlot<void>(this, 1); }
};

inline DrawInstView* View(gmBallDrawInst* d) { return reinterpret_cast<DrawInstView*>(d); }

// The object at 0x825EAB28 (g_input_obj_ptr): Initialize hands it the pace settings.
struct GameContextView {
    uint8_t  _pad000[0x28];
    uint32_t lookupKey28;          // +0x028  key for pg_C2A0_g (pong_misc.cpp: m_registryLookupKey)
    uint8_t  _pad02C[0x70];
    float    gamePace;             // +0x09C
    float    gamePaceA0;           // +0x0A0  gets the same value
    uint8_t  _pad0A4[0x60];
    float    gamePaceFactor;       // +0x104
    float    gamePaceNormalBias;   // +0x108
    float    gamePaceNetworkBias;  // +0x10C
    int32_t  gamePaceStart;        // +0x110
    float    minGamePaceDelta;     // +0x114
    float    maxGamePaceDelta;     // +0x118
    float    networkFastestBallTravelTime;  // +0x11C
};

// What pg_C2A0_g returns for that key; Reset reads the ball colour from it.
struct LookupRecordView {
    uint8_t _pad0000[0x1710];
    Vec4    ballColor;             // +0x1710
};

// The table at *0x8271A7F8: 12-byte records, the current one picked by +0x2C.
struct SpinTextureSetView {
    struct Record { uint32_t _00, _04; void* texture; };
    Record  records[3];            // +0x00
    uint8_t _pad24[8];
    int32_t current;               // +0x2C
};

struct Lookup826063C8View {        // *(0x826063C8)->+0x08
    uint8_t     _pad000[0x460];
    gmBallNode* ballNode;          // +0x460
};

struct Holder826063C8View {        // *(0x826063C8)
    uint8_t             _pad00[8];
    Lookup826063C8View* target;    // +0x08
};

// The draw-bucket manager at *0x826064F4.
struct DrawBucketView {
    uint8_t  _pad00[0x5C];
    uint32_t mask5C;               // +0x5C  passed as the bucket mask for the shadow and splash
};

// Shader globals (*0x825EBC40). A handle packs the dirty-bit index in bits
// 1..17 and the entry index in bits 18..31; the entry's low 16 bits pick the
// 16-byte value slot.
struct ShaderGlobalTableView {
    uint8_t   dirtyBits[0x100];    // +0x000
    uint32_t* entries;             // +0x100  8 bytes each; word 1 is used
    uint32_t  _104;
    Vec4*     values;              // +0x108
};

// Fixed-path asset folder stack at 0x825D0080 (shape of RAGE's ASSET.PushFolder);
// Initialize pops it by decrementing the depth inline.
struct AssetManagerView {
    uint8_t _pad000[0x600];
    int32_t folderDepth;           // +0x600
};

struct Options825C5EC8View {
    uint8_t _pad00[0x30];
    uint8_t flag30;                // +0x30  with it set (and the 0x822823E0 test true) Reset draws the ball 5x
};

}  // namespace gmball

// ── Globals ─────────────────────────────────────────────────────────────────
extern void*                         g_sda_base;          // r13: word 0 is the thread's TLS block
extern gmball::SimulatorView*        g_pPhysicsSim;       // @ 0x825F5BD0
extern gmball::LevelView*            g_pPhysicsLevel;     // @ 0x826065E4
extern pongBallInstance**            g_ppBallInst;        // @ 0x8271A2F4  where the current ball instance is published
extern gmBallNode*                   g_activeBallNode;    // @ 0x82606570
extern void*                         g_game_state_ptr;    // @ 0x8271A2F8
extern void*                         g_input_obj_ptr;     // @ 0x825EAB28
extern void*                         lbl_8271A310;        // @ 0x8271A310  root for pg_C2A0_g
extern gmball::SpinTextureSetView*   lbl_8271A7F8;        // @ 0x8271A7F8
extern gmball::Holder826063C8View*   lbl_826063C8;        // @ 0x826063C8
extern gmball::AssetManagerView      g_assetFolderStack;  // @ 0x825D0080
extern gmball::ShaderGlobalTableView* lbl_825EBC40;       // @ 0x825EBC40
extern "C" uint32_t                  g_grmShaderFx_boundContext;  // @ 0x825EBC54  bumped on every shader-global write
extern const uint8_t                 lbl_825D4C80[8];     // @ 0x825D4C80  0x80 >> n
extern const float                   lbl_825C5938;        // @ 0x825C5938  -1.0 in the image
extern const int32_t                 lbl_825C9A2C;        // @ 0x825C9A2C
extern gmball::Options825C5EC8View   lbl_825C5EC8;        // @ 0x825C5EC8
extern uint8_t                       lbl_82630710[];      // @ 0x82630710  data both trails are set up with
extern "C" void*                     g_drawBucket;        // @ 0x826064F4

// Message-sink list at 0x825F3864..0x825F3A68 (msg_event_handler.cpp names it an
// event queue): per entry a sink, a mask of message kinds and the byte 0x80.
extern uint32_t g_eventQueueIndex;      // @ 0x825F3864
extern void*    g_eventQueuePtrs[];     // @ 0x825F3868
extern uint32_t g_eventQueueMasks[];    // @ 0x825F3968
extern uint8_t  g_eventQueueFlags[];    // @ 0x825F3A68

// XML field handlers: each slot holds a rage::xmlNodeStruct* object; the
// registration takes the slot's address.
extern void* g_boolFieldType;   // @ 0x825CAF80  rage::xmlNodeStructBool
extern void* g_intFieldType;    // @ 0x825CAF90  rage::xmlNodeStructInt
extern void* g_floatFieldType;  // @ 0x825CAF94  rage::xmlNodeStructFloat

// MSVC RTTI (decorated name at +8)
struct RTTITypeDescriptor;
extern RTTITypeDescriptor g_typeDescriptor_phBound;        // @ 0x825D2C78  ".?AVphBound@rage@@"
extern RTTITypeDescriptor g_typeDescriptor_phBoundSphere;  // @ 0x825DE100  ".?AVphBoundSphere@rage@@"

// ── Callees ─────────────────────────────────────────────────────────────────
extern "C" void  sysMemAllocator_InitMainThread(void);                       // @ 0x820C0038
extern void      rage_free(void* ptr);                                        // @ 0x820C00C0
extern "C" void  RegisterSerializedField(void* node, const char* name, void* field,
                                         void* fieldType, int flags);        // @ 0x821A8F58
extern void      sgRMDrawable_RegisterFields(void* node);                     // @ 0x823D8F18
extern void      sgPhysicalObject_Initialize(void* node);                     // @ 0x823D9160  slot 23
extern void      sgPhysicalObject_Destruct(void* node);                       // @ 0x823D90A0
extern void      fiAssetFolders_Push(gmball::AssetManagerView* assets, const char* path);  // @ 0x822E2E60
extern "C" void* RTDynamicCast(void* object, int32_t vfDelta, RTTITypeDescriptor* sourceType,
                               RTTITypeDescriptor* targetType, int32_t isReference);  // @ 0x82430978
extern fxBallTrail*      fxBallTrail_Construct(void* mem);                    // @ 0x822812A8
extern void              fxBallSplash2D_ResetSplashes(fxBallSplash2D* splash); // @ 0x82389BD8 (gmBallNode_9BD8)
extern pongBallInstance* pongBallInstance_Construct(void* mem);               // @ 0x8227F870
extern void      game_4B60(void* scene, uint16_t handle);                     // @ 0x822C4B60  deactivates the object
extern void      game_3860(void* gameState, int kind, const char* name);      // @ 0x821D3860
extern "C" void* pg_C2A0_g(void* lookupRoot, uint32_t lookupKey);             // @ 0x821DC2A0
extern int       io_Input_poll_9D68(void* inputObj);                          // @ 0x821C9D68
extern uint32_t  game_A2F8(const char* name, int create);                     // @ 0x8215A2F8  returns a shader-global handle (inferred)
struct pongDrawBucket;
void pongDrawBucket_AddEntry(pongDrawBucket* bucket, void* renderable, uint32_t bucketMask);  // @ 0x822278D8

namespace gmball {

inline AllocatorView* ThreadAllocator() {
    void** tls = *static_cast<void***>(g_sda_base);
    return static_cast<AllocatorView*>(tls[1]);
}

inline void* RageNew(uint32_t size) {
    sysMemAllocator_InitMainThread();
    return ThreadAllocator()->Allocate(size, 16);
}

inline void RegisterMessageSink(void* sink, uint32_t mask) {
    uint32_t i = g_eventQueueIndex;
    g_eventQueueFlags[i] = 0x80;
    g_eventQueuePtrs[i] = sink;
    g_eventQueueMasks[i] = mask;
    g_eventQueueIndex = i + 1;
}

inline void SetShaderGlobal(uint32_t handle, const Vec4& value) {
    ShaderGlobalTableView* table = lbl_825EBC40;
    ++g_grmShaderFx_boundContext;
    uint32_t bit = (handle >> 1) & 0x1FFFF;
    uint32_t entryWord = table->entries[(handle >> 18) * 2 + 1];
    table->dirtyBits[bit >> 3] |= lbl_825D4C80[bit & 7];
    table->values[entryWord & 0xFFFF] = value;
}

inline fxBallTrail* NewTrail() {
    void* mem = RageNew(0xB4D0);
    return mem ? fxBallTrail_Construct(mem) : nullptr;
}

inline fxBallShadow* NewShadow() {
    auto* shadow = static_cast<RenderableView*>(RageNew(0x10));
    if (!shadow) return nullptr;
    ConstructRenderable(shadow);
    shadow->vtable = GameVtable(kVtable_fxBallShadow);
    return reinterpret_cast<fxBallShadow*>(shadow);
}

// The fxBallSpinTex constructor, inlined with fxBallSpin's and msgMsgSink's.
inline fxBallSpinTex* NewSpinTex() {
    auto* spin = static_cast<SpinTexView*>(RageNew(0x1A0));
    if (!spin) return nullptr;
    ConstructRenderable(&spin->renderable);
    spin->sinkVtable = GameVtable(kVtable_msgMsgSink);
    spin->f24 = 1.0f;
    spin->f1C = 1.0f;
    spin->f20 = 1.0f;
    spin->flag18 = 1;
    spin->renderable.vtable = GameVtable(kVtable_fxBallSpin);
    spin->flag19 = 1;
    spin->sinkVtable = GameVtable(kVtable_fxBallSpin_sink);
    for (Vec4& v : spin->vecB0) v = Splat(0.0f);
    spin->renderable.vtable = GameVtable(kVtable_fxBallSpinTex);
    spin->sinkVtable = GameVtable(kVtable_fxBallSpinTex_sink);
    return reinterpret_cast<fxBallSpinTex*>(spin);
}

// The fxBallSplash2D constructor, inlined; it ends by resetting the splashes.
inline fxBallSplash2D* NewSplash2D() {
    auto* splash = static_cast<Splash2DView*>(RageNew(0x240));
    if (!splash) return nullptr;
    ConstructRenderable(&splash->renderable);
    splash->renderable.vtable = GameVtable(kVtable_pongRenderable);
    splash->vtable = GameVtable(kVtable_fxBallSplash2D);
    splash->renderable.vtable = GameVtable(kVtable_fxBallSplash2D_render);
    auto* result = reinterpret_cast<fxBallSplash2D*>(splash);
    fxBallSplash2D_ResetSplashes(result);
    return result;
}

}  // namespace gmball

using namespace gmball;

// ── [0] ScalarDtor @ 0x82280B18 ───────────────────────────────────────────────
gmBallNode* gmBallNode::ScalarDtor(int flags) {
    vtable = GameVtable(kVtable_gmBallNode);
    renderEntryVtable = GameVtable(kVtable_gmBallNode_renderEnt);
    sinkVtable = GameVtable(kVtable_gmBallNode_sink);
    sinkVtable = GameVtable(kVtable_msgMsgSink);  // ~msgMsgSink, inlined
    sgPhysicalObject_Destruct(this);
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

// ── msgMsgSink-base slot 0 @ 0x82282498 ───────────────────────────────────────
// `addi r3,r3,-0x80; b 0x82280B18`: the deleting destructor through the +0x80 base.
gmBallNode* gmBallNode_SecondaryDtorThunk(void* sinkBase, int flags) {
    auto* node = reinterpret_cast<gmBallNode*>(static_cast<uint8_t*>(sinkBase) - 0x80);
    return node->ScalarDtor(flags);
}

// ── [21] LoadProperties @ 0x82280B98 ──────────────────────────────────────────
// Calls sgRMDrawable's registration directly (not sgPhysicalObject's 0x823D94C0)
// and registers "Fixed" itself.
void gmBallNode::LoadProperties() {
    sgRMDrawable_RegisterFields(this);
    RegisterSerializedField(this, "Fixed", &fixed, &g_boolFieldType, 0);
    RegisterSerializedField(this, "PopFlyMinHeight", &popFlyMinHeight, &g_floatFieldType, 0);
    RegisterSerializedField(this, "Scale", &scale, &g_floatFieldType, 0);
    RegisterSerializedField(this, "VisualSpinScale", &visualSpinScale, &g_floatFieldType, 0);
    RegisterSerializedField(this, "GamePace", &gamePace, &g_floatFieldType, 0);
    RegisterSerializedField(this, "GamePaceFactor", &gamePaceFactor, &g_floatFieldType, 0);
    RegisterSerializedField(this, "GamePaceNormalBias", &gamePaceNormalBias, &g_floatFieldType, 0);
    RegisterSerializedField(this, "GamePaceNetworkBias", &gamePaceNetworkBias, &g_floatFieldType, 0);
    RegisterSerializedField(this, "GamePaceStart", &gamePaceStart, &g_intFieldType, 0);
    RegisterSerializedField(this, "MinGamePaceDelta", &minGamePaceDelta, &g_floatFieldType, 0);
    RegisterSerializedField(this, "MaxGamePaceDelta", &maxGamePaceDelta, &g_floatFieldType, 0);
    RegisterSerializedField(this, "ServeTimeout", &serveTimeout, &g_floatFieldType, 0);
    RegisterSerializedField(this, "NetworkFastestBallTravelTime", &networkFastestBallTravelTime,
                            &g_floatFieldType, 0);
}

// ── [23] Initialize @ 0x82280D48 ──────────────────────────────────────────────
void gmBallNode::Initialize() {
    fiAssetFolders_Push(&g_assetFolderStack, "$/props");
    transform.d.x = 0.0f;
    transform.d.y = 4.0f;  // the float at 0x825C90BC
    transform.d.z = 0.0f;
    sgPhysicalObject_Initialize(this);
    --g_assetFolderStack.folderDepth;  // pop "$/props"

    // Mass properties of a thin spherical shell: I = 2/3 m r² about every axis.
    BallInstView* ball = View(inst);
    ArchetypeView* archetype = ball->archetype;
    archetype->typeFlags = 2;
    archetype->includeFlags = 0xFFFFFFFFu;
    float mass = archetype->GetMass();
    float radius = archetype->bound->radius;
    float inertia = mass * radius * radius * 0.6666667f;  // the float at 0x825D4164
    float angInertia[3] = {inertia, inertia, inertia};
    archetype->SetAngInertia(angInertia);

    // The asm stores through the result without a null check.
    ColliderView* collider = nullptr;
    if (g_pPhysicsSim->level->IsActive(ball->levelIndex)) {
        collider = g_pPhysicsSim->level->GetActiveCollider(ball->levelIndex);
    }
    collider->maxAngularSpeed = 125.66371f;  // 40π

    *g_ppBallInst = inst;
    storeScale = 1;

    // fsel clamps: a NaN falls to the lower bound.
    float s = (scale - 0.1f >= 0.0f) ? scale : 0.1f;
    s = (s - 10.0f >= 0.0f) ? 10.0f : s;
    scale = s;
    SetScale(s);

    float h = (popFlyMinHeight >= 0.0f) ? popFlyMinHeight : 0.0f;
    h = (h - 10.0f >= 0.0f) ? 10.0f : h;
    popFlyMinHeight = h;

    trails[0] = NewTrail();
    Trail_Setup(trails[0], 0, 0, lbl_82630710);
    trails[1] = NewTrail();
    Trail_Setup(trails[1], 0, 0, lbl_82630710);

    shadow = NewShadow();

    spinTex = NewSpinTex();
    SpinTex_Register(spinTex);
    SpinTextureSetView* textures = lbl_8271A7F8;
    SpinTex_SetTexture(spinTex, textures->records[textures->current].texture);

    splash = NewSplash2D();
    fxBallSplash2D_ResetSplashes(splash);
    RegisterMessageSink(splash, 1);
    auto* splashView = reinterpret_cast<Splash2DView*>(splash);
    for (int i = 0; i < 2; ++i) {
        splashView->marks[i].active = 0;
        splashView->marks[i + 2].active = 0;
    }
    RegisterMessageSink(&sinkVtable, 0x23);

    g_activeBallNode = this;
    lbl_826063C8->target->ballNode = this;
    View(drawInst)->mode0C = 2;

    auto* context = static_cast<GameContextView*>(g_input_obj_ptr);
    context->gamePace = gamePace;
    context->gamePaceA0 = context->gamePace;
    context->gamePaceFactor = gamePaceFactor;
    context->gamePaceNormalBias = gamePaceNormalBias;
    context->gamePaceNetworkBias = gamePaceNetworkBias;
    context->gamePaceStart = gamePaceStart;
    context->minGamePaceDelta = minGamePaceDelta;
    context->maxGamePaceDelta = maxGamePaceDelta;
    context->networkFastestBallTravelTime = networkFastestBallTravelTime;  // ServeTimeout isn't copied

    ballColorVar = game_A2F8("Ball_Color", 1);
}

// ── [24] Terminate @ 0x82281368 ───────────────────────────────────────────────
void gmBallNode::Terminate() {
    *g_ppBallInst = nullptr;
    rage_free(trails[0]);
    rage_free(trails[1]);
    rage_free(shadow);
    if (spinTex) {
        // deleting destructor through the msgMsgSink base at +0x10
        CallSlot<void>(&reinterpret_cast<SpinTexView*>(spinTex)->sinkVtable, 0, 1);
    }
    if (splash) {
        CallSlot<void>(splash, 0, 1);
    }
    g_activeBallNode = nullptr;
}

// ── [25] Reset @ 0x82281408 ───────────────────────────────────────────────────
// Puts the ball back for a new rally: back on the node's matrix, out of the
// physics level, effects cleared, ball colour and scale reapplied.
void gmBallNode::Reset() {
    CallSlot<void>(this, 32, &transform);  // sgPhysicalObject slot 32 (0x823D93A0)
    if (trails[0]) Trail_Reset(trails[0]);
    if (trails[1]) Trail_Reset(trails[1]);
    if (spinTex) SpinTex_Reset(spinTex);
    if (splash) fxBallSplash2D_ResetSplashes(splash);
    CallSlot<void>(this, 35, 0);  // sgPhysicalObject slot 35 (0x823D94B0): flag71 = drawInst+0x85 = 0

    BallInstView* ball = View(inst);
    if (g_pPhysicsLevel->IsActive(ball->levelIndex)) {
        game_4B60(g_pPhysicsSim, ball->levelIndex);
    }
    ball->archetype->includeFlags = 0;
    ball->flag55 = 1;
    if (ball->audio) {
        ball->audio->word32C = 0;
    }

    game_3860(g_game_state_ptr, 1, "gmBallNode::Reset");

    f094[2] = 1.0f;
    f094[1] = 1.0f;
    f094[0] = 1.0f;
    f0A0 = 0.0f;
    f0A4 = lbl_825C5938;

    auto* context = static_cast<GameContextView*>(g_input_obj_ptr);
    auto* record = static_cast<LookupRecordView*>(pg_C2A0_g(lbl_8271A310, context->lookupKey28));
    SetShaderGlobal(ballColorVar, record->ballColor);

    // Same test as 0x822823E0, inlined.
    bool test = false;
    if (static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr)) == 0) {
        test = (lbl_825C9A2C == 0);
    }
    float newScale = 1.0f;
    if (test && lbl_825C5EC8.flag30 != 0) {
        newScale = 5.0f;  // the float at 0x8202C504
    }
    g_activeBallNode->SetScale(newScale);
}

// ── [29] Draw @ 0x82281C10 ────────────────────────────────────────────────────
// Only the first trail is drawn.
void gmBallNode::Draw() {
    DrawInstView* draw = View(drawInst);
    if (draw->drawable60) {
        draw->Draw();
    }
    if (trails[0]) {
        Trail_Draw(trails[0]);
    }
    if (shadow) {
        auto* bucket = static_cast<DrawBucketView*>(g_drawBucket);
        reinterpret_cast<RenderableView*>(shadow)->sortValue = 100.0f;
        pongDrawBucket_AddEntry(reinterpret_cast<pongDrawBucket*>(bucket), shadow, bucket->mask5C);
    }
    if (spinTex) {
        SpinTex_Draw(spinTex);
    }
    if (splash) {
        auto* bucket = static_cast<DrawBucketView*>(g_drawBucket);
        reinterpret_cast<Splash2DView*>(splash)->renderable.sortValue = 300.0f;
        pongDrawBucket_AddEntry(reinterpret_cast<pongDrawBucket*>(bucket), AsRenderable(splash),
                                bucket->mask5C);
    }
}

// ── SetScale @ 0x82282318 ─────────────────────────────────────────────────────
// Scales the drawn ball and, if the bound is a sphere, its radius (0.02 per unit:
// a 40 mm ball at scale 1).
void gmBallNode::SetScale(float newScale) {
    View(drawInst)->scale = Splat(newScale);
    auto* sphere = static_cast<BoundView*>(RTDynamicCast(View(inst)->archetype->bound, 0,
                                                        &g_typeDescriptor_phBound,
                                                        &g_typeDescriptor_phBoundSphere, 0));
    if (sphere) {
        float radius = newScale * 0.02f;  // the float at 0x825C8138
        sphere->radius = radius;
        sphere->radiusSplat = Splat(radius);
        sphere->RadiusChanged();
    }
    if (storeScale) {
        scale = newScale;
    }
}

// ── [37] CreateInst @ 0x82282430 ──────────────────────────────────────────────
// sgPhysicalObject slot 36 (0x823D9708) calls this and stores the result at +0x74.
pongBallInstance* gmBallNode::CreateInst() {
    void* mem = RageNew(0xD0);
    return mem ? pongBallInstance_Construct(mem) : nullptr;
}

// ─────────────────────────────────────────────────────────────────────────────
// gmBallNode tertiary vtable destructor thunk  [rtti_7288_0 @ 0x82281CF8]
// Loads child object at this+28, then calls its destructor through vtable.
// ─────────────────────────────────────────────────────────────────────────────
void gmBallNode_TertiaryDtorThunk(gmBallNode* self) {
    // Load the secondary base object pointer at offset +28
    void* childObj = *reinterpret_cast<void**>(reinterpret_cast<uint8_t*>(self) + 28);

    // Call the child's destructor through its vtable slot 0
    void** childVtable = *reinterpret_cast<void***>(childObj);
    void (*destructor)(void*) = reinterpret_cast<void (*)(void*)>(childVtable[0]);
    destructor(childObj);
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance / pongBallHitData virtual method implementations
// ─────────────────────────────────────────────────────────────────────────────

// External helpers referenced by these methods.
extern "C" {
    // Global physics world / history ring accessor — fetches ring header ptr.
    // PPC literal: lis -32142 / lwz -23816 / lwz +20 → g_physWorld->historySystem
    void* pongPhysics_GetHistorySystem();                              // @ 0x8232E9F8 via global table

    // Event dispatcher used by vfn_24's 'swing hit' cases.
    int  pongBallInstance_DispatchSwingEvent(uintptr_t owner, uint32_t hitType,
                                             const pongBallInstance::Vec4* impactPos,
                                             uint32_t evFlags, uint32_t zero);  // @ 0x82280070

    // Audio cue for paddle impact — 8225E6E0.
    void pongBall_PlayPaddleImpactCue(uint32_t bitflag, uint32_t, uint32_t, uint32_t);

    // Game-logic updater called on the 'missed' path.
    void pongBallInstance_OnBallMissed(pongBallInstance* self);        // @ 0x8227FDB0

    // Remote player hit resolver used by the fast-path branch.
    void pongBall_ResolveRemoteHit(pongBallInstance* self, pongBallInstance* other,
                                   uint32_t impactHandle, uint32_t slotIndex,
                                   uint32_t flagByte);                 // @ 0x822CD730

    // XML serialization helpers for pongBallHitData::LoadProperties.
    void xmlNodeStruct_RegisterField(pongBallHitData* self,
                                     const char* name,
                                     void* addr,
                                     uint32_t typeTag,
                                     uint32_t arity);                  // @ 0x821A8F58
    void xmlNodeStruct_PostLoadBase(pongBallHitData* self);            // @ 0x821A8988
}

// Global static byte written/read by PostLoadProperties / LoadProperties.
// lis -32160 / +25741 → 0x8203E48D (.data byte, size 1) — a 'debug enabled' flag.
extern "C" uint8_t g_pongBallHitDataEnableFlag;                        // @ 0x8203E48D

namespace {
constexpr uint16_t kHitDataFlag_Enabled     = 0x1000;  // bit set when debug flag is on
constexpr uint16_t kHitDataFlag_InitialMask = 0x6000;  // OR'd on by PostLoadProperties
constexpr const char kHitDataNodeTypeName[] = "pongBallHitData";
} // namespace

// ── [2] pongBallInstance::GetMatrixAt60 @ 0x82280028 ─────────────────────────
// Trivially returns a pointer to the embedded 4×4 matrix stored at this+0x60.
pongBallInstance::Mat44* pongBallInstance::GetMatrixAt60() {
    return reinterpret_cast<Mat44*>(reinterpret_cast<uint8_t*>(this) + 0x60);
}

// ── [3] pongBallInstance::SetMatrixAt60 @ 0x82280030 ─────────────────────────
// Vector-copies a full 64-byte matrix from 'src' into this+0x60 via 4× vmx loads.
void pongBallInstance::SetMatrixAt60(const Mat44* src) {
    Mat44* dst = reinterpret_cast<Mat44*>(reinterpret_cast<uint8_t*>(this) + 0x60);
    dst->row0 = src->row0;
    dst->row1 = src->row1;
    dst->row2 = src->row2;
    dst->row3 = src->row3;
}

// ── [4] pongBallInstance::GetCurrentPosition @ 0x8227FF38 ────────────────────
// Reads current ball position from the physics history ring (row 0 = translation).
// When no entries yet, zeroes the output. The hash-to-slot math mirrors the PPC:
//   slot = ((count+1) * 0x88888889h) >> 32, adjusted, mod 120.
void pongBallInstance::GetCurrentPosition(Vec4* outPos) {
    void* hist = pongPhysics_GetHistorySystem();
    if (!hist) { *outPos = Vec4{0.f, 0.f, 0.f, 0.f}; return; }

    int32_t entryCount = *reinterpret_cast<int32_t*>(
        static_cast<uint8_t*>(hist) + 9640);
    if (entryCount <= 0) {
        *outPos = Vec4{0.f, 0.f, 0.f, 0.f};
        return;
    }

    uint8_t* ringBase   = static_cast<uint8_t*>(hist) + 32;
    int32_t  headCount  = *reinterpret_cast<int32_t*>(ringBase + 9604) + 1;
    // (headCount % 120) * 80 — 80 bytes per entry, row0 is first 16 bytes.
    int32_t  slotIndex  = static_cast<int32_t>(
        static_cast<uint32_t>(headCount) % 120u);
    uint8_t* entry      = ringBase + static_cast<size_t>(slotIndex) * 80u + 32u;

    *outPos = *reinterpret_cast<Vec4*>(entry);
}

// ── [5] pongBallInstance::GetCurrentVelocity @ 0x8227FFB0 ────────────────────
// Same ring geometry as GetCurrentPosition, but row at +48 (row2) holds velocity.
void pongBallInstance::GetCurrentVelocity(Vec4* outVel) {
    void* hist = pongPhysics_GetHistorySystem();
    if (!hist) { *outVel = Vec4{0.f, 0.f, 0.f, 0.f}; return; }

    int32_t entryCount = *reinterpret_cast<int32_t*>(
        static_cast<uint8_t*>(hist) + 9640);
    if (entryCount <= 0) {
        *outVel = Vec4{0.f, 0.f, 0.f, 0.f};
        return;
    }

    uint8_t* ringBase   = static_cast<uint8_t*>(hist) + 32;
    int32_t  headCount  = *reinterpret_cast<int32_t*>(ringBase + 9604) + 1;
    int32_t  slotIndex  = static_cast<int32_t>(
        static_cast<uint32_t>(headCount) % 120u);
    uint8_t* entry      = ringBase + static_cast<size_t>(slotIndex) * 80u + 48u;

    *outVel = *reinterpret_cast<Vec4*>(entry);
}

// ── [30] pongBallInstance::ValidateCollisionParams3 @ 0x8227FA28 ─────────────
// Three-argument validity gate — returns zero unconditionally in the shipped
// build. PPC only inspects the args via cmplwi; all paths fall through to 'r3=0'.
int pongBallInstance::ValidateCollisionParams3(uint32_t a, uint32_t b, uint32_t c) {
    (void)a; (void)b; (void)c;
    return 0;
}

// ── [24] pongBallInstance::ProcessCollisionAndActivate @ 0x8227FA48 ──────────
// Core collision reaction:
//   1. Resolve 'other' through the MI-vtable offset adjustment when needed.
//   2. Ask pongBall_ResolveRemoteHit for both primary and (if matched) secondary
//      link handles.
//   3. Build an impact vector = other.pos - self.ref_pos, and classify the
//      event via pongBallInstance_DispatchSwingEvent. Depending on outcome:
//        case 4 → play paddle audio cue (threshold check vs. m_speedSquared)
//        case 3/2 with no physics-throttle → call OnBallMissed
//        default with gate byte set → ActivateBall
// The tail after 0x8227FD24 copies the impact vector into the scratch at +80
// and issues further audio / event hooks; the case-4 branch below summarizes
// the paddle-impact-audio path that still awaits its dedicated vfn_24 lift.
void pongBallInstance::ProcessCollisionAndActivate(pongBallInstance* other) {
    // Resolve primary link handle. The PPC path uses vtable[-1] as an MI offset;
    // in the happy-path of the shipped build this offset is 176 bytes.
    uint32_t primaryHandle = other->m_primaryLinkPtr;
    if (primaryHandle == 0) {
        uintptr_t vptr      = reinterpret_cast<uintptr_t>(other->vtable);
        size_t    adjust    = static_cast<size_t>(vptr) * 176u;
        primaryHandle = *reinterpret_cast<uint32_t*>(
            reinterpret_cast<uint8_t*>(other) + adjust);
    }

    uint32_t hitHandleA =
        *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(other) + 12 + 16);
    pongBall_ResolveRemoteHit(this, other, hitHandleA, /*slot*/0, /*flag*/1);

    // Secondary branch — only when primary matches 'this'.
    if (primaryHandle == reinterpret_cast<uintptr_t>(this)) {
        uint32_t secondaryHandle = other->m_secondaryLinkPtr;
        if (secondaryHandle == 0) {
            uintptr_t vptr   = reinterpret_cast<uintptr_t>(other->vtable);
            size_t    adjust = static_cast<size_t>(vptr - 1) * 176u;
            secondaryHandle = *reinterpret_cast<uint32_t*>(
                reinterpret_cast<uint8_t*>(other) + adjust + 180u);
        }
        uint32_t hitHandleB =
            *reinterpret_cast<uint32_t*>(reinterpret_cast<uint8_t*>(other) + 12 + 16 + 4);
        pongBall_ResolveRemoteHit(this, other, hitHandleB, /*slot*/0, /*flag*/0);
        (void)secondaryHandle;
    }

    // impactPos = (other pose position) - (self pose ref) from vector slot at +64/+16.
    Vec4* otherRow = reinterpret_cast<Vec4*>(
        reinterpret_cast<uint8_t*>(other) + 12 + 64);
    Vec4* selfRef  = reinterpret_cast<Vec4*>(
        reinterpret_cast<uint8_t*>(other) + 12 + 64);   // PPC uses +0xb0 relative
    Vec4 impact{
        otherRow->x - selfRef->x,
        otherRow->y - selfRef->y,
        otherRow->z - selfRef->z,
        0.f
    };

    uint32_t evFlags =
        *reinterpret_cast<uint32_t*>(
            *reinterpret_cast<uint32_t**>(reinterpret_cast<uint8_t*>(other) + 12 + 16) + 16/4)
        & 0xDu;

    int classification = pongBallInstance_DispatchSwingEvent(
        reinterpret_cast<uintptr_t>(this), 0, &impact, evFlags, 0);

    switch (classification) {
    case 0: case 1: case 2: case 3:
        break;
    default:
        if (this->m_hitPolicyFlag != 0) {
            this->ActivateBall(other);
        }
        break;
    }

    // 'Missed' path (case 3 / case 2 without physics throttle) and case 4
    // paddle-impact audio are inlined in the original — summarized here.
    // Full re-expansion depends on pg_E6E0 and pongBall_PlayPaddleImpactCue
    // getting their own lifts; both are tracked in the ball-audio follow-up.
    if (classification == 3 || classification == 2) {
        void* histEntry = pongPhysics_GetHistorySystem();
        int32_t gate = histEntry
            ? *reinterpret_cast<int32_t*>(static_cast<uint8_t*>(histEntry) + 9640)
            : 0;
        if (gate == 0) {
            pongBallInstance_OnBallMissed(this);
        }
    } else if (classification == 4) {
        // Paddle-impact path. The scalar at flt_82079B18 is 0.000100f — an
        // epsilon/threshold multiplier (per xex_excavation_tt/float_constants.txt).
        // Full cue selection (8 vs 9 based on m_speedSquared × 0.0001f) will
        // land with the dedicated vfn_24 lift; current dispatch uses the default.
        pongBall_PlayPaddleImpactCue(/*bitflag*/1, 0, 0, 0);
    }
}

// ── pongBallHitData::PostLoadProperties [vfn_2] @ 0x821D6900 ─────────────────
// Sets m_flags based on the global enable byte, then OR-masks 0x6000 on top
// and chains to the base xmlNodeStruct post-load hook.
void pongBallHitData::PostLoadProperties() {
    uint16_t value = 0;
    if (g_pongBallHitDataEnableFlag != 0) {
        value = kHitDataFlag_Enabled;
    }
    this->m_flags = static_cast<uint16_t>(value | kHitDataFlag_InitialMask);
    xmlNodeStruct_PostLoadBase(this);
}

// File-scope extern decls (C linkage prohibited inside function bodies)
extern "C" uint32_t g_pongBallHitData_hashA;   // @ 0x8202861C
extern "C" uint32_t g_pongBallHitData_hashB;   // @ 0x8203F03C
extern "C" uint32_t g_pongBallHitData_hashC;   // @ 0x8203F038

// ── pongBallHitData::IsApplicable [vfn_20] @ 0x821D65C0 ──────────────────────
// Matches the passed attribute hash against three known property hashes.
bool pongBallHitData::IsApplicable(uint32_t contextHash) {
    if (contextHash == g_pongBallHitData_hashA) return true;
    if (contextHash == g_pongBallHitData_hashB) return true;
    return contextHash == g_pongBallHitData_hashC;
}

// ── pongBallHitData::GetNodeTypeName [vfn_22] @ 0x821D65B0 ───────────────────
// Returns the static node-type literal "pongBallHitData".
const char* pongBallHitData::GetNodeTypeName() {
    return kHitDataNodeTypeName;
}

// ── pongBallHitData::LoadProperties [vfn_21] @ 0x821D6608 ────────────────────
// Registers every serializable field with the XML system. The full method
// registers ~30 fields — implemented here as a compact table-driven pass.
void pongBallHitData::LoadProperties() {
    // KNOWN LIMITATION: the 19 fields below cover the first half of the
    // pass5 body; the remaining ~18 entries (offsets 256..0x15C) register
    // against string-table names in the lbl_825CAF9C family that still need
    // to be extracted from the binary. Adding them here without those names
    // would introduce placeholder string literals — left as a deliberate gap.
    struct FieldDesc { uint32_t offset; const char* name; uint32_t type; };
    static const FieldDesc kFields[] = {
        { 16,  "HitZone",        0 }, { 20,  "SwingType",      0 },
        { 24,  "Dir",            0 }, { 32,  "Pos",            0 },
        { 48,  "Power",          0 }, { 96,  "Aim",            0 },
        { 112, "Timing",         0 }, { 128, "Spin",           0 },
        { 132, "Slice",          0 }, { 136, "Arc",            0 },
        { 140, "TargetSpeed",    0 }, { 144, "Accuracy",       0 },
        { 148, "Reflex",         0 }, { 152, "StaminaDrain",   0 },
        { 156, "CooldownMs",     0 }, {  64, "AnimClip",       0 },
        { 160, "Ai",             0 }, { 176, "AiTarget",       0 },
        { 308, "CurveMul",       0 },
    };
    for (const FieldDesc& fd : kFields) {
        xmlNodeStruct_RegisterField(
            this, fd.name,
            reinterpret_cast<uint8_t*>(this) + fd.offset,
            fd.type, 0u);
    }

    // Mirror the global 'enabled' byte from the parsed flag bit.
    g_pongBallHitDataEnableFlag =
        (this->m_flags & kHitDataFlag_Enabled) ? 1 : 0;
}

// ────────────────────────────────────────────────────────────────────────────
// pongBallInstance_4980_g @ 0x822C4980 | size: 0x1DC
// No pseudocode available — emitted as a valid no-op so it links while the
// real body is lifted in a later pass. Signature derived from call sites in
// player code (pongPlayer calls this on the player manager pointer).
// ────────────────────────────────────────────────────────────────────────────
void pongBallInstance_4980_g(void* instance, int a, int b, int c, int d) {
    (void)instance; (void)a; (void)b; (void)c; (void)d;
}

// 6-arg overload — call site in phUpdateObject::Reset uses
// (void*, unsigned short, int, int, int, int). Kept as a no-op stub.
void pongBallInstance_4980_g(void* instance, unsigned short s,
                             int a, int b, int c, int d) {
    (void)instance; (void)s; (void)a; (void)b; (void)c; (void)d;
}

// ─────────────────────────────────────────────────────────────────────────────
// pongBallInstance_DispatchHit (C++ linkage, 7 args) — used by pongBallInstance
// hit/remote-hit paths. No matching binary symbol; stubbed here to link.
// ─────────────────────────────────────────────────────────────────────────────
void pongBallInstance_DispatchHit(pongBallInstance* self, unsigned short player,
                                  void* a, void* b, void* c, void* d, void* e) {
    (void)self; (void)player; (void)a; (void)b; (void)c; (void)d; (void)e;
}

// ─────────────────────────────────────────────────────────────────────────────
// C-linkage ball-event bridges referenced from ball::vfn_24 (swing resolver).
// ─────────────────────────────────────────────────────────────────────────────
extern "C" {
    int pongBallInstance_DispatchSwingEvent(uintptr_t owner, uint32_t hitType,
                                            const pongBallInstance::Vec4* impactPos,
                                            uint32_t evFlags, uint32_t zero) {
        (void)owner; (void)hitType; (void)impactPos; (void)evFlags; (void)zero;
        return 0;
    }

    void pongBallInstance_OnBallMissed(pongBallInstance* self) { (void)self; }
}

// ─────────────────────────────────────────────────────────────────────────────
// pongLerpQueue_Update — synthetic linker bridge called from
// pongPlayer::UpdatePhysicsAndSwingInput. The full lerp queue is in
// src/game/pong_lerp_queue.cpp (not yet in CMakeLists). Stub here.
// ─────────────────────────────────────────────────────────────────────────────
void pongLerpQueue_Update(void* queue) { (void)queue; }


// ─────────────────────────────────────────────────────────────────────────────
// Ball collision-pair broadphase seeders — lifted from pass5_final recomp.
//
// These fill the 17152 B physics collision-pair scratch block at 0x825CBCF0
// (also populated by phSimulator::vfn_4 / phArticulatedCollider::vfn_5 /
// phLevelNew::vfn_27 — hence *not* a ball-specific global, the ball code just
// re-uses the engine pair buffer). The block holds two "slots" at byte
// offsets 16912..17076 — slot 0 (primary / chooser side) and slot 1
// (secondary / opponent side). Each slot stores:
//   +16912/+16916 : data-area pointer  (ball +16 + 16)
//   +17056/+17060 : sub-object pointer chained via (ball+16)->+4->+12
//   +17064/+17068 : flag slot (also cleared / overwritten to 0)
//   +17072/+17076 : back-reference to the ball instance
//   +16928..+16976 / +16992..+17040 : 4×16 B matrix rows copied from ball+32
//
// The raw engine helper at 0x82294330 still carries its anonymous
// `util_4330` name in the binary symbol map (no RTTI / string anchor), but
// its semantic role is "clear the pair-broadphase scratch block". We wrap it
// in a named extern so call-sites read meaningfully.
// ─────────────────────────────────────────────────────────────────────────────

// Raw engine symbol — ph/ball pair-broadphase scratch clear.
// @ 0x82294330 | size: 0xB4. Shared with phSimulator_vfn_4 etc.
extern "C" void util_4330(void* pairScratch, void* partnerHint);

// Semantic alias — same entry point, readable name at the call site.
inline void PhysicsPairBroadphase_Clear(void* pairScratch, void* partnerHint) {
    util_4330(pairScratch, partnerHint);
}

namespace {

// Read the ordering/priority byte used to decide which ball wins "slot 0".
// The chain is (ball+16)->+4->+12, reading byte at +4 of the final pointer.
// Lower 3 bits only participate in the compare.
inline uint8_t ReadBallPriorityByte(pongBallInstance* ball) {
    auto* ballBytes    = reinterpret_cast<uint8_t*>(ball);
    auto* dataPtr      = *reinterpret_cast<uint8_t**>(ballBytes + 16);
    auto* subLevel1    = *reinterpret_cast<uint8_t**>(dataPtr + 4);
    auto* subLevel2    = *reinterpret_cast<uint8_t**>(subLevel1 + 12);
    return *(subLevel2 + 4);
}

// Fill slot 0 of g_pairBroadphaseScratch with (ball, matrix-rows, metadata).
inline void WriteBallToSlot0(uint8_t* state, pongBallInstance* ball) {
    auto* ballBytes    = reinterpret_cast<uint8_t*>(ball);
    auto* dataPtr      = *reinterpret_cast<uint8_t**>(ballBytes + 16);
    auto* subLevel1    = *reinterpret_cast<uint8_t**>(dataPtr + 4);
    auto* subLevel2    = *reinterpret_cast<uint8_t**>(subLevel1 + 12);

    *reinterpret_cast<uint32_t*>(state + 17064) = 0u;
    *reinterpret_cast<uint32_t*>(state + 17072) = reinterpret_cast<uintptr_t>(ball);
    *reinterpret_cast<uint32_t*>(state + 17056) = reinterpret_cast<uintptr_t>(subLevel2);
    *reinterpret_cast<uint32_t*>(state + 16912) = reinterpret_cast<uintptr_t>(dataPtr + 16);

    const uint8_t* mat = ballBytes + 32;
    memcpy(state + 16928, mat +  0, 16);
    memcpy(state + 16944, mat + 16, 16);
    memcpy(state + 16960, mat + 32, 16);
    memcpy(state + 16976, mat + 48, 16);
}

// Fill slot 1 of g_pairBroadphaseScratch.
inline void WriteBallToSlot1(uint8_t* state, pongBallInstance* ball) {
    auto* ballBytes    = reinterpret_cast<uint8_t*>(ball);
    auto* dataPtr      = *reinterpret_cast<uint8_t**>(ballBytes + 16);
    auto* subLevel1    = *reinterpret_cast<uint8_t**>(dataPtr + 4);
    auto* subLevel2    = *reinterpret_cast<uint8_t**>(subLevel1 + 12);

    *reinterpret_cast<uint32_t*>(state + 17068) = 0u;
    *reinterpret_cast<uint32_t*>(state + 17076) = reinterpret_cast<uintptr_t>(ball);
    *reinterpret_cast<uint32_t*>(state + 17060) = reinterpret_cast<uintptr_t>(subLevel2);
    *reinterpret_cast<uint32_t*>(state + 16916) = reinterpret_cast<uintptr_t>(dataPtr + 16);

    const uint8_t* mat = ballBytes + 32;
    memcpy(state + 16992, mat +  0, 16);
    memcpy(state + 17008, mat + 16, 16);
    memcpy(state + 17024, mat + 32, 16);
    memcpy(state + 17040, mat + 48, 16);
}

} // namespace

/**
 * BallCollisionPair_SeedFromBothBalls @ 0x822CD228 | size: 0x194
 *
 * Prepares the physics collision-pair broadphase scratch for a ball-vs-ball
 * contact. Clears the block, then writes both ball slots (0 and 1) ordered
 * by the 3-bit priority tag read via the chain (ball+16)->+4->+12+4. The
 * ball with the *smaller* tag occupies slot 0 (priority branch: `blt`).
 *
 * NOTE: this is NOT a pongBallInstance member — r3 on entry is the pair
 * scratch block (g_pairBroadphaseScratch), not a `this` pointer. The two
 * ball arguments arrive in r4/r5.
 */
void BallCollisionPair_SeedFromBothBalls(pongBallInstance* ballA,
                                         pongBallInstance* ballB) {
    extern uint8_t g_pairBroadphaseScratch[];  // @ 0x825CBCF0, 17152 B

    PhysicsPairBroadphase_Clear(g_pairBroadphaseScratch, ballB);

    const uint8_t tagA = ReadBallPriorityByte(ballA);
    const uint8_t tagB = ReadBallPriorityByte(ballB);

    pongBallInstance* slot0Ball;
    pongBallInstance* slot1Ball;
    if (tagB < tagA) {
        // Less-than branch: ballA keeps slot 0, ballB goes to slot 1.
        slot0Ball = ballA;
        slot1Ball = ballB;
    } else {
        slot0Ball = ballB;
        slot1Ball = ballA;
    }

    WriteBallToSlot0(g_pairBroadphaseScratch, slot0Ball);
    WriteBallToSlot1(g_pairBroadphaseScratch, slot1Ball);
}

/**
 * BallCollisionPair_SeedFromOneBall @ 0x822CD3C0 | size: 0x13C
 *
 * Asymmetric seeder used when only one of the two contact participants is a
 * ball (the other is a non-ball collider whose priority byte lives one chain
 * deeper: (other+4)->+12+4). The ball goes to whichever slot the priority
 * ordering dictates; the non-ball side is populated via the matrix-snapshot
 * helper for the opposite slot.
 *
 *   if (ball tag <= other tag):  ball -> slot 0 directly,
 *                                 SnapshotMatrixToGlobalSlot1(ball) fills slot 1.
 *   else:                        SnapshotMatrixToGlobalSlot0(ball) fills slot 0,
 *                                 ball -> slot 1 directly.
 *
 * (See pongBallInstance_1FA0 for the parallel control-flow pattern.)
 */
void BallCollisionPair_SeedFromOneBall(pongBallInstance* ball,
                                       pongBallInstance* other) {
    extern uint8_t g_pairBroadphaseScratch[];  // @ 0x825CBCF0

    PhysicsPairBroadphase_Clear(g_pairBroadphaseScratch, other);

    auto* otherBytes  = reinterpret_cast<uint8_t*>(other);
    auto* otherSub1   = *reinterpret_cast<uint8_t**>(otherBytes + 4);
    auto* otherSub2   = *reinterpret_cast<uint8_t**>(otherSub1 + 12);
    const uint8_t tagOther = *(otherSub2 + 4);
    const uint8_t tagBall  = ReadBallPriorityByte(ball);

    if (tagOther <= tagBall) {
        WriteBallToSlot0(g_pairBroadphaseScratch, ball);
        pongBallInstance::SnapshotMatrixToGlobalSlot1(ball);
    } else {
        pongBallInstance::SnapshotMatrixToGlobalSlot0(ball);
        WriteBallToSlot1(g_pairBroadphaseScratch, ball);
    }
}

/**
 * pongBallInstance secondary-vtable scalar-deleting thunk
 * @ 0x82280890 | size: 0x8
 *
 * Already lifted above as `pongBallInstance_SecondaryDtorThunk`. The adjusted
 * `this` offset of -80 bytes matches the location of the secondary vtable
 * pointer (+80) inside the pongBallInstance layout.
 */

/**
 * pongBallAudio::ScalarDtor(int flags)   [vtable slot 0 @ 0x8228ABE0 | 0x50]
 *
 * MSVC scalar-deleting destructor: runs the inline ~pongBallAudio() body
 * (delegated to the base audControl3d destructor) and, if the low bit of
 * `flags` is set, releases the heap slab. This is the standard two-arg
 * virtual destructor thunk the compiler emits for classes with virtual dtors.
 *
 * Matches the `pongPaddle::ScalarDtor(int flags)` pattern already used
 * elsewhere in the project (pong_network_classes.cpp).
 */
void pongBallAudio::ScalarDtor(int flags) {
    extern void audControl3d_Destructor(pongBallAudio* obj);  // @ 0x8228AC30
    extern void rage_free(void* ptr);                         // @ 0x820C00C0

    // Inline ~pongBallAudio() — same call the stack-scoped dtor makes.
    audControl3d_Destructor(this);

    if (flags & 1) {
        rage_free(this);
    }
}


// ============================================================================
// Ball/physics utility stubs (SIMD-heavy, pending full lift)
// Moved from stubs.cpp to their correct source file.
// ============================================================================

/**
 * game_36E8 @ 0x822436E8 | size: 0x37C
 * Animation/physics data copy — copies 892 bytes of SIMD-aligned data
 * between ball state buffers. Used during ball trajectory computation.
 * TODO: Full SIMD lift.
 */
void game_36E8(void* dest, const float* src) {
    (void)dest; (void)src;
}

/**
 * game_AA88 @ 0x822CAA88 | size: 0xE8
 * phInst matrix update — copies a 4x4 SIMD matrix and dispatches
 * a vtable call to update the physics instance transform.
 * TODO: Full SIMD lift.
 */
void game_AA88(void* physInst) {
    (void)physInst;
}

/**
 * game_D500 @ 0x822CD500 | size: 0xEC
 * Creature instance matrix binding — copies a SIMD matrix from source
 * to the creature instance's transform slot.
 * TODO: Full SIMD lift.
 */
void game_D500(void* creatureInst, void* srcMatrix, void* destSlot) {
    (void)creatureInst; (void)srcMatrix; (void)destSlot;
}

/**
 * game_DA60 @ 0x822CDA60 | size: 0xD0
 * Physics weight computation loop — iterates over physics instances
 * and computes interpolation weights for ball trajectory prediction.
 * TODO: Full SIMD lift.
 */
void game_DA60() {
    // No-op until physics interpolation is active
}

/**
 * util_D150 @ 0x8227D150 | size: 0xCC
 * datResource_Load — loads a 4x4 matrix from a resource data block into
 * the object's transform at offset +32, stores the data pointer at +20,
 * and optionally notifies a global physics manager via vtable dispatch.
 * TODO: Full SIMD lift (4 vector loads + stores).
 */
void util_D150(void* obj, void* resourceData) {
    if (!obj || !resourceData) return;
    // Store resource data pointer at +20
    *reinterpret_cast<void**>(static_cast<uint8_t*>(obj) + 20) = resourceData;
    // TODO: Copy 4x vec4 from resourceData to obj+32 (SIMD)
    // TODO: Check resource status ID and notify physics manager
}

// 3-arg overload used by some callers
void util_D150(void* obj, void* a, void* b) {
    (void)obj; (void)a; (void)b;
}

/**
 * util_8FD0 @ 0x822C8FD0 | size: 0x5C
 * pongCreatureInst cleanup — resets vtable to base class, releases
 * the child object at +4 if present, then sets the base vtable.
 * Alias: pongCreatureInst_9030_g
 */
void util_8FD0(void* obj) {
    if (!obj) return;
    uint8_t* self = static_cast<uint8_t*>(obj);
    // Clear child pointer at +4
    void* child = *reinterpret_cast<void**>(self + 4);
    if (child) {
        // TODO: Call util_9D98(child, 1) to release child
    }
    *reinterpret_cast<void**>(self + 4) = nullptr;
}

