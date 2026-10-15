/**
 * pong_match.cpp — Match logic and game mode implementations
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */

#include "pong_match.hpp"
#include <cstdint>
#include <cstddef>

// Forward declarations for external functions
extern "C" {
    void hsmContext_SetNextState(void* context, int stateId);
    int PongNetGameModeCoordinator_GetGameState(void* coordinator);
    void atSingleton_GetValue(void* event, void* typeInfo, void* outValue);
    void nop_LogDebug(const char* message);
}

// External globals
extern uint8_t g_spectatorModeEnabled;
extern void* g_pongGameInstance;
extern void* g_playerDataArray;

// Event type constants
enum GameEventType {
    EVENT_SPECTATOR_MODE_TOGGLE = 2083,
    EVENT_SPECTATOR_EXIT = 2145,
    EVENT_NETWORK_PLAYER_JOINED = 14369,
    EVENT_NETWORK_PLAYER_LEFT = 14370,
    EVENT_RETURN_TO_LOBBY = 14376,
    EVENT_SPECTATOR_READY = 2060
};

// ─────────────────────────────────────────────────────────────────────────────
// gmLogicSpectator::ProcessEvent() [vtable slot 18 @ 0x8238D660]
// 
// Event handler for spectator game mode logic. Processes various game events
// including spectator mode toggles, network player join/leave events, and
// state transitions for the spectator viewing system.
// ─────────────────────────────────────────────────────────────────────────────
void gmLogicSpectator::ProcessEvent(void* event) {
    // Get current state handler from state array
    void* currentStateHandler = nullptr;
    if (m_currentStateIndex <= 17) {
        currentStateHandler = m_stateArray[m_currentStateIndex];
    }
    
    // Read event type from event object (first 2 bytes)
    uint16_t eventType = *(uint16_t*)event;
    
    // Handle spectator mode toggle
    if (eventType == EVENT_SPECTATOR_MODE_TOGGLE) {
        g_spectatorModeEnabled = 1;
        goto dispatch_to_state;
    }
    
    // Handle spectator exit - transition to state 17
    if (eventType == EVENT_SPECTATOR_EXIT) {
        hsmContext_SetNextState(this, 17);
        goto dispatch_to_state;
    }
    
    // Handle network player joined event
    if (eventType == EVENT_NETWORK_PLAYER_JOINED) {
        // Calculate player coordinator offset: playerIndex * 2784 + 36256
        uint32_t playerIndex = *(uint32_t*)((char*)g_pongGameInstance + 4);
        void* playerCoordinator = nullptr;
        
        if (playerIndex <= 3) {
            uint32_t offset = playerIndex * 2784 + 36256;
            playerCoordinator = (char*)g_playerDataArray + offset;
        }
        
        // Check if game state is >= 5 (in-game)
        int gameState = PongNetGameModeCoordinator_GetGameState(playerCoordinator);
        if (gameState < 5) {
            goto dispatch_to_state;
        }
        
        // Check if game state is <= 6 (not post-game)
        gameState = PongNetGameModeCoordinator_GetGameState(playerCoordinator);
        if (gameState > 6) {
            goto dispatch_to_state;
        }
        
        // Check if game object exists and has valid replay buffer
        if (m_pGameObject == nullptr) {
            goto dispatch_to_state;
        }
        
        int replayBufferIndex = *(int*)((char*)m_pGameObject + 992);
        if (replayBufferIndex == -1) {
            goto dispatch_to_state;
        }
        
        // Extract player ID from event
        int eventPlayerId;
        atSingleton_GetValue(event, (void*)0x82027898, &eventPlayerId);
        
        // Set spectator mode active
        m_spectatorModeActive = 1;
        
        // Check if event player matches game object's player
        int gameObjectPlayerId = *(int*)((char*)m_pGameObject + 992);
        m_isSpectatingLocalPlayer = (eventPlayerId == gameObjectPlayerId) ? 1 : 0;
        
        goto dispatch_to_state;
    }
    
    // Handle network player left event
    if (eventType == EVENT_NETWORK_PLAYER_LEFT) {
        // Similar logic to player joined
        uint32_t playerIndex = *(uint32_t*)((char*)g_pongGameInstance + 4);
        void* playerCoordinator = nullptr;
        
        if (playerIndex <= 3) {
            uint32_t offset = playerIndex * 2784 + 36256;
            playerCoordinator = (char*)g_playerDataArray + offset;
        }
        
        int gameState = PongNetGameModeCoordinator_GetGameState(playerCoordinator);
        if (gameState < 5) {
            goto dispatch_to_state;
        }
        
        gameState = PongNetGameModeCoordinator_GetGameState(playerCoordinator);
        if (gameState > 6) {
            goto dispatch_to_state;
        }
        
        // Extract player IDs from event
        int playerId1, playerId2;
        atSingleton_GetValue(event, (void*)0x82030084, &playerId1);
        atSingleton_GetValue(event, (void*)0x82030088, &playerId2);
        
        // Set spectator mode based on player 2 presence
        m_spectatorModeActive = (playerId1 != 0) ? 2 : 3;
        m_isSpectatingLocalPlayer = (playerId2 != 0) ? 1 : 0;
        
        goto dispatch_to_state;
    }
    
    // Handle return to lobby - transition to state 11
    if (eventType == EVENT_RETURN_TO_LOBBY) {
        hsmContext_SetNextState(this, 11);
        goto dispatch_to_state;
    }
    
    // Handle spectator ready event
    if (eventType == EVENT_SPECTATOR_READY) {
        if (m_spectatorModeActive != 0) {
            nop_LogDebug("Spectator ready - exiting spectator mode");
            m_spectatorModeActive = 0;
        }
    }
    
dispatch_to_state:
    // Dispatch event to current state handler if it exists
    if (currentStateHandler != nullptr) {
        // Virtual call to state handler's ProcessEvent method (vtable slot 16)
        void** vtable = *(void***)currentStateHandler;
        typedef void (*ProcessEventFn)(void*, void*);
        ProcessEventFn processEvent = (ProcessEventFn)vtable[16];
        processEvent(currentStateHandler, event);
    }
    
    // Also dispatch to game object if it exists
    if (m_pGameObject != nullptr) {
        void** vtable = *(void***)m_pGameObject;
        typedef void (*ProcessEventFn)(void*, void*);
        ProcessEventFn processEvent = (ProcessEventFn)vtable[5];
        processEvent(m_pGameObject, event);
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// statePostGame — Post-game state machine functions
//
// Shared between gmLogicSinglesMatch::statePostGame [vtable @ 0x8203168C]
// and gmLogicSpectator::statePostGame [vtable @ 0x8206BDDC].
// Both vtables point to the same function addresses.
//
// statePostGame struct layout:
//   +0x00: void** vtable
//   +0x04: void*  m_pHsmContext      — owning HSM context for state transitions
//   +0x08: void*  m_pParentLogic     — owning gmLogic instance
//   +0x10: uint8_t m_bScoresProcessed — post-game scores submitted
//   +0x11: uint8_t m_bExitReady       — ready to transition out
// ═════════════════════════════════════════════════════════════════════════════

// External functions used by statePostGame methods
extern "C" {
    void stateServeBounce_OnEnter_Spectator(void* state); // @ 0x8238D9A8
    void PostPageGroupMessage(int msgCode, int mask,
                              int paramCount, void* params);  // pg_E6E0 @ 0x8225E6E0
    bool IsNetworkClientActive(void* client);  // pg_10E0_g @ 0x821010E0
    void RemoveNodeFromList(void* container, void* node); // SinglesNetworkClient_F508_g @ 0x823CF508
    void* FindPostPointMessage(void* container);           // statePostPoint_E7E0_g @ 0x823CE7E0
    void ShowUnlockProgressDialog(void* unlockData, int mode, int count,
                                  uint64_t p1, uint64_t p2,
                                  uint64_t p3, uint64_t p4, int flags); // util_94B8 @ 0x823794B8
}

// Globals for post-game logic
extern void* g_input_obj_ptr;      // @ 0x825EAB28 — match context singleton
extern void* g_render_obj_ptr;     // @ 0x825EAB2C — network client singleton
extern void* g_pMatchResultData;   // @ 0x8271A320 — unlock eligibility (+16,+20 = slot IDs)
extern void* g_pTournamentData;    // @ 0x8271A334 — tournament progress (+44=total,+128=current)
extern void* g_pNetworkStateFlags; // @ 0x8271A340 — network session state (+8=mode)

// ExitPostGameMessage class identifier for linked list lookups
extern uint32_t g_exitPostGameMsgClassId; // @ 0x825D1218 — compared against vfn_6 return
// Message handler pool descriptor (+8 = pool manager ptr, 12-byte node stride)
extern char g_messagePoolInfo[];           // @ 0x825D1224
// Dialog parameters (two uint64_t values)
extern uint64_t g_unlockDialogParams[2];   // @ 0x8261A0C0

// Post-game message codes
static constexpr uint16_t MSG_ENTER_POST_GAME     = 8197;
static constexpr uint16_t MSG_EXIT_POST_GAME      = 8200;
static constexpr uint16_t MSG_POST_GAME_SPECTATOR = 10252;
static constexpr uint16_t MSG_EXIT_MATCH          = 2139;
static constexpr uint16_t MSG_FADE_TRANSITION     = 10254;
static constexpr uint16_t MSG_CLEANUP_MATCH       = 2075;

// Forward declarations for batch functions
void* statePostGame_FindExitMessage(void* container);   // E948_g
void  statePostGame_RemoveExitMessage(void* gameObj);    // CC58
void* statePostGame_AllocateMessageNode();               // 9820_g

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame::GetName  [vtable slot 13 @ 0x8210BD48] | size: 0x0C
// Returns the state name string for HSM debugging/identification.
// ─────────────────────────────────────────────────────────────────────────────
const char* statePostGame_GetName(void* /*self*/) { // @ 0x8210BD48
    return "PostGame";
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame::CanTransitionTo  [vtable slot 15 @ 0x8210BD20] | size: 0x28
// Returns true if this state accepts transitions to the given target state.
// Singles match variant: accepts PostMatch(28), PostTourney(29), MainMenu(30).
// ─────────────────────────────────────────────────────────────────────────────
bool statePostGame_CanTransitionTo(void* /*self*/, int targetStateId) { // @ 0x8210BD20
    return (targetStateId == 28 || targetStateId == 29 || targetStateId == 30);
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame::CanTransitionTo (spectator)  [vtable slot 15 @ 0x82390258] | size: 0x28
// Spectator variant: accepts states 3, 16, 17.
// ─────────────────────────────────────────────────────────────────────────────
bool statePostGame_CanTransitionTo_Spectator(void* /*self*/, int targetStateId) { // @ 0x82390258
    return (targetStateId == 16 || targetStateId == 3 || targetStateId == 17);
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame_FindExitMessage @ 0x823CE948 | size: 0x74
// Searches the message handler linked list (at container+92) for an
// ExitPostGameMessage node. Returns the handler object if found, else nullptr.
// ─────────────────────────────────────────────────────────────────────────────
void* statePostGame_FindExitMessage(void* container) { // @ 0x823CE948
    // Linked list head at container+92
    // Node layout: +0=handler object ptr, +12=next node ptr
    void* node = *(void**)((char*)container + 92);

    while (node != nullptr) {
        void* handler = *(void**)node;

        // Call vfn_6 (GetClassId) on the handler object
        void** vtable = *(void***)handler;
        typedef uint32_t (*GetClassIdFn)(void*);
        uint32_t classId = ((GetClassIdFn)vtable[6])(handler);

        if (classId == g_exitPostGameMsgClassId) {
            return handler;
        }

        node = *(void**)((char*)node + 12);
    }
    return nullptr;
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame_RemoveExitMessage @ 0x823CCC58 | size: 0x7C
// Finds the ExitPostGameMessage handler in the game object's driver list,
// calls its cleanup virtual (vfn_4), and removes it from the linked list.
// ─────────────────────────────────────────────────────────────────────────────
void statePostGame_RemoveExitMessage(void* gameObj) { // @ 0x823CCC58
    char* container = (char*)gameObj + 4364;
    void* node = *(void**)((char*)container + 92);

    while (node != nullptr) {
        void* handler = *(void**)node;

        void** vtable = *(void***)handler;
        typedef uint32_t (*GetClassIdFn)(void*);
        uint32_t classId = ((GetClassIdFn)vtable[6])(handler);

        if (classId == g_exitPostGameMsgClassId) {
            // Cleanup the handler via vfn_4
            typedef void (*CleanupFn)(void*);
            ((CleanupFn)vtable[4])(handler);

            // Remove node from the linked list
            RemoveNodeFromList(container, node);
            return;
        }

        node = *(void**)((char*)node + 12);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame_AllocateMessageNode @ 0x823B9820 | size: 0x8C
// Allocates a node from the ExitPostGameMessage pool. The pool uses an
// intrusive free list with uint16_t indices and 12-byte node stride.
// Returns the allocated node address, or nullptr if pool is empty.
// ─────────────────────────────────────────────────────────────────────────────
void* statePostGame_AllocateMessageNode() { // @ 0x823B9820
    // Pool manager pointer is at g_messagePoolInfo+8
    char* poolMgr = *(char**)(g_messagePoolInfo + 8);

    // Free list head index at poolMgr+28
    uint16_t freeHead = *(uint16_t*)(poolMgr + 28);
    if (freeHead == 0xFFFF) {
        return nullptr;
    }

    // Compute node address: poolMgr + freeHead * 12
    char* node = poolMgr + (uint32_t)freeHead * 12;

    // Read the next free index from node+10
    uint16_t nextFree = *(uint16_t*)(node + 10);

    // Update free list head
    *(uint16_t*)(poolMgr + 28) = nextFree;

    // If next free node exists, clear its prev-link
    if (nextFree != 0xFFFF) {
        char* nextNode = poolMgr + (uint32_t)nextFree * 12;
        *(uint16_t*)(nextNode + 8) = 0xFFFF;
    }

    // Clear this node's next-free link
    *(uint16_t*)(node + 10) = 0xFFFF;

    // Decrement free count at poolMgr+24
    *(uint16_t*)(poolMgr + 24) -= 1;

    return node;
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame::OnEvent (spectator)  [vtable slot 16 @ 0x823901A0] | size: 0xB8
// Handles MSG_EXIT_POST_GAME (8200) events in spectator context.
// If network is active, transitions to state 16.
// If offline, sends cleanup messages and transitions to state 3.
// ─────────────────────────────────────────────────────────────────────────────
void statePostGame_OnEvent_Spectator(void* self, void* event) { // @ 0x823901A0
    uint16_t eventType = *(uint16_t*)event;

    if (eventType != MSG_EXIT_POST_GAME) {
        return;
    }

    // Check if network client is currently active
    if (IsNetworkClientActive(g_render_obj_ptr)) {
        // Network active — transition to PostGame-with-network state
        void* hsmContext = *(void**)((char*)self + 0x04);
        hsmContext_SetNextState(hsmContext, 16);
    } else {
        // Offline — send cleanup messages and return to lobby
        PostPageGroupMessage(MSG_EXIT_MATCH, 64, 0, nullptr);

        uint32_t fadeParam = 1;
        PostPageGroupMessage(MSG_FADE_TRANSITION, 64, 1, &fadeParam);

        PostPageGroupMessage(MSG_CLEANUP_MATCH, 64, 0, nullptr);

        void* hsmContext = *(void**)((char*)self + 0x04);
        hsmContext_SetNextState(hsmContext, 3);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper: process ExitPostGameMessage dispatching for spectator states.
// Shared logic between OnEnter_Spectator and Update_Spectator.
// ─────────────────────────────────────────────────────────────────────────────
static void ProcessExitPostGameDrivers(void* self) {
    // Access the match object through parentLogic: *(parentLogic+44)
    void* parentLogic = *(void**)((char*)self + 0x08);
    void* matchObj = *(void**)((char*)parentLogic + 44);

    if (matchObj == nullptr) {
        return;
    }

    char* driverContainer = (char*)matchObj + 4364;

    // Check if ExitPostGameMessage handler already exists
    void* exitHandler = statePostGame_FindExitMessage(driverContainer);

    if (exitHandler != nullptr) {
        // Handler exists — clean it up and remove it
        statePostGame_RemoveExitMessage(matchObj);
        return;
    }

    // No exit handler yet — check if a PostPoint handler exists
    void* postPointHandler = FindPostPointMessage(driverContainer);
    if (postPointHandler == nullptr) {
        return;
    }

    // Allocate a new message node and dispatch it
    void* newNode = statePostGame_AllocateMessageNode();
    if (newNode == nullptr) {
        return;
    }

    // Initialize via vfn_4, then process via vfn_5
    void** vtable = *(void***)newNode;
    typedef void (*VoidFn)(void*);
    ((VoidFn)vtable[4])(newNode);
    ((VoidFn)vtable[5])(newNode);
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame::Update (spectator)  [vtable slot 10 @ 0x823900D8] | size: 0xC4
// Per-frame update for spectator post-game state. Processes pending
// ExitPostGameMessage handlers in the driver list.
// ─────────────────────────────────────────────────────────────────────────────
void statePostGame_Update_Spectator(void* self) { // @ 0x823900D8
    ProcessExitPostGameDrivers(self);
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame::OnEnter (spectator)  [vtable slot 11 @ 0x8238FFD0] | size: 0x108
// State entry for spectator post-game. Initializes parent state, sends
// post-game UI messages, and processes ExitPostGameMessage driver setup.
// ─────────────────────────────────────────────────────────────────────────────
void statePostGame_OnEnter_Spectator(void* self) { // @ 0x8238FFD0
    // Call parent state's OnEnter (spectator variant)
    stateServeBounce_OnEnter_Spectator(self);

    // Send "enter post-game" message
    PostPageGroupMessage(MSG_ENTER_POST_GAME, 64, 0, nullptr);

    // If not in network mode, also send the spectator-specific message
    void* networkFlags = g_pNetworkStateFlags;
    int networkMode = *(int*)((char*)networkFlags + 8);
    if (networkMode == 0) {
        PostPageGroupMessage(MSG_POST_GAME_SPECTATOR, 64, 0, nullptr);
    }

    // Process ExitPostGameMessage driver setup
    ProcessExitPostGameDrivers(self);
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostGame::PostGameCheck @ 0x8210C738 | size: 0x134
// Determines post-game unlock/progression state. Called as vfn_14 in the
// singles match context. Checks whether the player won the final game of a
// tournament, has pending unlocks, or needs a progression dialog shown.
// Always sets m_bExitReady when complete.
// ─────────────────────────────────────────────────────────────────────────────
void statePostGame_PostGameCheck(void* self) { // @ 0x8210C738
    // Skip if already processed
    uint8_t* pExitReady = (uint8_t*)((char*)self + 0x11);
    if (*pExitReady) {
        return;
    }

    void* matchCtx = g_input_obj_ptr;
    int gameMode = *(int*)((char*)matchCtx + 8);

    bool isFinalGameWinner = false;

    // In network mode (gameMode==3), check if player won the final game
    if (gameMode == 3) {
        void* netClient = g_render_obj_ptr;
        int player1Score = *(int*)((char*)netClient + 28);
        int player2Score = *(int*)((char*)netClient + 32);

        if (player1Score > player2Score) {
            // Player 1 won this game — check if it's the final game
            void* tournamentData = g_pTournamentData;
            int totalGames = *(int*)((char*)tournamentData + 44);
            int currentGame = *(int*)((char*)tournamentData + 128);

            if (currentGame == totalGames - 1) {
                isFinalGameWinner = true;
            }
        }
    }

    if (!isFinalGameWinner) {
        // Check unlock eligibility: two slot IDs at +16 and +20
        void* unlockData = g_pMatchResultData;
        int unlockSlot1 = *(int*)((char*)unlockData + 16);
        int unlockSlot2 = *(int*)((char*)unlockData + 20);

        // If either slot has content (not -1), pending unlocks exist
        bool hasUnlockPending = !(unlockSlot1 == -1 && unlockSlot2 == -1);

        if (hasUnlockPending) {
            // Content to unlock — will be handled by subsequent state
        } else {
            // No unlocks pending — show progression/continue dialog
            ShowUnlockProgressDialog(
                unlockData, 2, 1,
                g_unlockDialogParams[0], g_unlockDialogParams[1],
                g_unlockDialogParams[0], g_unlockDialogParams[1],
                0);
        }
    }

    // Mark post-game check as complete
    *pExitReady = 1;
}


// ═════════════════════════════════════════════════════════════════════════════
// gmLogicSwingPractice::stateMainMenu — HSM state for swing practice main menu
//
// Vtable @ 0x820304FC. Inherits from hsmState.
// State struct layout:
//   +0x00: void** vtable
//   +0x04: void*  m_pHsmContext     — owning HSM context
//   +0x08: void*  m_pParentLogic    — owning gmLogicSwingPractice instance
// ═════════════════════════════════════════════════════════════════════════════

// External functions for stateMainMenu
extern "C" {
    void stateServeBounce_OnEnter(void* self, int param);           // @ 0x82106A60
    void gmLogicSwingPractice_OnExit(void* parentLogic);            // pongPlayer_2DF0_h @ 0x82102DF0
}

// Mutable global: swing practice fade time
extern float g_swingPracticeFadeTime;  // @ 0x825C9A28

// ─────────────────────────────────────────────────────────────────────────────
// stateMainMenu::GetName  [vtable slot 13 @ 0x82101F20] | size: 0x0C
// Returns the state name string for HSM debugging/identification.
// ─────────────────────────────────────────────────────────────────────────────
const char* stateMainMenu_GetName(void* /*self*/) { // @ 0x82101F20
    return "MainMenu";
}

// ─────────────────────────────────────────────────────────────────────────────
// stateMainMenu::OnEnter  [vtable slot 11 @ 0x821037D8] | size: 0x28
// Enters the main menu state. Retrieves the parent logic's UI page group
// (at parentLogic+148) and calls its Open method (vtable slot 4) to display
// the main menu screen overlay.
// ─────────────────────────────────────────────────────────────────────────────
void stateMainMenu_OnEnter(void* self) { // @ 0x821037D8
    void* parentLogic = *(void**)((char*)self + 8);
    void* pageGroup = *(void**)((char*)parentLogic + 148);

    if (pageGroup == nullptr) {
        return;
    }

    // Call Open on the page group sub-object at +384
    // vtable slot 4 (Open/Show)
    void* pageGroupUI = (void*)((char*)pageGroup + 384);
    void** vtable = *(void***)pageGroupUI;
    typedef void (*OpenFn)(void*);
    ((OpenFn)vtable[4])(pageGroupUI);
}

// ─────────────────────────────────────────────────────────────────────────────
// stateMainMenu::OnExit  [vtable slot 12 @ 0x82103800] | size: 0x08
// Exits the main menu state by delegating to the parent logic's exit handler.
// ─────────────────────────────────────────────────────────────────────────────
void stateMainMenu_OnExit(void* self) { // @ 0x82103800
    void* parentLogic = *(void**)((char*)self + 8);
    gmLogicSwingPractice_OnExit(parentLogic);
}

// ─────────────────────────────────────────────────────────────────────────────
// stateMainMenu::CanTransitionTo  [vtable slot 15 @ 0x82103808] | size: 0x18
// Returns true if the target state ID is 3 (the Aim state in swing practice).
// ─────────────────────────────────────────────────────────────────────────────
bool stateMainMenu_CanTransitionTo(void* /*self*/, int targetStateId) { // @ 0x82103808
    return (targetStateId == 3);
}

// ─────────────────────────────────────────────────────────────────────────────
// stateMainMenu::OnEvent  [vtable slot 16 @ 0x82103820] | size: 0x58
// Handles event 2063 (MSG_START_PRACTICE). When received, transitions the
// HSM context to state 3 (Aim) and sets the fade time to 0.5 seconds.
// ─────────────────────────────────────────────────────────────────────────────
void stateMainMenu_OnEvent(void* self, void* event) { // @ 0x82103820
    uint16_t eventType = *(uint16_t*)event;

    if (eventType != 2063) {
        return;
    }

    // Transition to Aim state (state 3)
    void* hsmContext = *(void**)((char*)self + 8);
    hsmContext_SetNextState(hsmContext, 3);

    // Set fade time to 0.5 seconds for the transition
    g_swingPracticeFadeTime = 0.5f;
}

// ═════════════════════════════════════════════════════════════════════════════
// gmLogicSinglesMatch::statePostMatch — HSM state after match completion
//
// Vtable @ 0x82031844. Inherits from hsmState.
// State struct layout:
//   +0x00: void** vtable
//   +0x04: void*  m_pHsmContext      — owning HSM context
//   +0x08: void*  m_pParentLogic     — owning gmLogicSinglesMatch instance
//   +0x10: uint8_t m_bReadyToExit    — set when exit event received
//   +0x11: uint8_t m_bReturnToLobby  — set when returning to lobby
// ═════════════════════════════════════════════════════════════════════════════

// External functions for statePostMatch
extern "C" {
    void statePostMatch_ProcessExit(void* self);    // pg_C5B0 @ 0x8210C5B0
    void statePostMatch_ProcessReturn(void* self);  // statePostGame_C738_p46 @ 0x8210C738
}

// External globals for statePostMatch
// g_input_obj_ptr @ 0x825EAB28 — already declared above
// g_render_obj_ptr @ 0x825EAB2C — already declared above
// g_pNetworkStateFlags @ 0x8271A340 — already declared above

// Player data array with per-player state blocks
extern char g_playerDataArray2[]; // lbl_8261A3D0 @ 0x8261A3D0 (832 bytes)

// ─────────────────────────────────────────────────────────────────────────────
// statePostMatch::GetName  [vtable slot 13 @ 0x8210C5A0] | size: 0x0C
// Returns the state name string for HSM debugging/identification.
// ─────────────────────────────────────────────────────────────────────────────
const char* statePostMatch_GetName(void* /*self*/) { // @ 0x8210C5A0
    return "PostMatch";
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostMatch::CanTransitionTo  [vtable slot 15 @ 0x8210C588] | size: 0x18
// Returns true if the target state ID is 33 (return to main menu / lobby).
// ─────────────────────────────────────────────────────────────────────────────
bool statePostMatch_CanTransitionTo(void* /*self*/, int targetStateId) { // @ 0x8210C588
    return (targetStateId == 33);
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostMatch::OnEvent  [vtable slot 16 @ 0x8210C558] | size: 0x2C
// Handles event MSG_EXIT_POST_MATCH (8201). Sets the m_bReadyToExit flag
// so the Update function knows to begin exit processing.
// ─────────────────────────────────────────────────────────────────────────────
void statePostMatch_OnEvent(void* self, void* event) { // @ 0x8210C558
    uint16_t eventType = *(uint16_t*)event;

    if (eventType != 8201) {
        return;
    }

    // Signal that exit was requested
    *(uint8_t*)((char*)self + 16) = 1;
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostMatch::Update  [vtable slot 10 @ 0x8210C530] | size: 0x24
// Checks exit flags each frame. If m_bReturnToLobby (+17) is set, processes
// the lobby return. If m_bReadyToExit (+16) is set, processes the exit.
// ─────────────────────────────────────────────────────────────────────────────
void statePostMatch_Update(void* self) { // @ 0x8210C530
    uint8_t returnToLobby = *(uint8_t*)((char*)self + 17);
    if (returnToLobby != 0) {
        statePostMatch_ProcessExit(self);
        return;
    }

    uint8_t readyToExit = *(uint8_t*)((char*)self + 16);
    if (readyToExit == 0) {
        return;
    }

    statePostMatch_ProcessReturn(self);
}

// ─────────────────────────────────────────────────────────────────────────────
// statePostMatch::OnEnter  [vtable slot 11 @ 0x8210C368] | size: 0x1C4
// Enters the post-match state. Calls the base OnEnter (stateServeBounce_vfn_11),
// clears the exit flags, determines whether it's a network match (mode 4 or 5),
// sends match-end page group messages, and configures per-player state blocks.
// ─────────────────────────────────────────────────────────────────────────────
void statePostMatch_OnEnter(void* self) { // @ 0x8210C368
    // Call base OnEnter with param=0
    void* origR3 = self;
    // Reuse self as r3, r4=0 for stateServeBounce_vfn_11
    stateServeBounce_OnEnter(self, 0);

    // Clear exit flags
    char* state = (char*)origR3;
    *(uint8_t*)(state + 16) = 0;
    *(uint8_t*)(state + 17) = 0;

    // Check network game mode from g_input_obj_ptr
    void* inputObj = g_input_obj_ptr;
    int gameMode = *(int*)((char*)inputObj + 8);

    // Determine if this is a network match (mode 4 or 5)
    bool isNetworkMatch = (gameMode == 4) || (gameMode == 5);

    // Send match completion message (2130) to page group system
    PostPageGroupMessage(2130, 64, 0, nullptr);

    // Re-read game mode for post-match logic
    void* inputObj2 = g_input_obj_ptr;
    int gameMode2 = *(int*)((char*)inputObj2 + 8);

    // Check if mode 4 or 5 (network modes)
    bool isNetworkMode = (gameMode2 == 4) || (gameMode2 == 5);

    if (!isNetworkMode) {
        // Check if mode 3 (local exhibition match)
        bool isExhibition = (gameMode2 == 3);

        if (isExhibition) {
            // For exhibition mode, check tournament progress
            void* renderObj = g_render_obj_ptr;
            int currentRound = *(int*)((char*)renderObj + 28);
            int totalRounds = *(int*)((char*)renderObj + 32);

            // Only show match stats if not the final round winner
            if (currentRound <= totalRounds) {
                isExhibition = false;
            }
        }

        if (!isExhibition) {
            // Non-network, non-final-exhibition: show match stats
            isNetworkMode = true;
        }
    }

    // Configure per-player result fields in the match context
    // inputObj2+25 = show result banner flag
    // inputObj2+24 = result submitted flag  
    // inputObj2+48 = post-match UI mode
    *(uint8_t*)((char*)inputObj2 + 25) = isNetworkMode ? 0 : 1;
    *(uint8_t*)((char*)inputObj2 + 24) = 0;

    if (isNetworkMatch) {
        // Network match: set UI mode to 4 (network post-match)
        *(uint32_t*)((char*)inputObj2 + 48) = 4;
    } else {
        // Local/offline match: set UI mode to 1 (local post-match)
        *(uint32_t*)((char*)inputObj2 + 48) = 1;
    }

    // Send post-match enter message (8198) to page group
    PostPageGroupMessage(8198, 64, 0, nullptr);

    // Check network session state
    void* networkState = g_pNetworkStateFlags;
    uint8_t networkMode = *(uint8_t*)((char*)networkState + 8);

    if (networkMode == 0) {
        // Offline mode: also send spectator dismiss message (10253)
        PostPageGroupMessage(10253, 64, 0, nullptr);
    }

    // Configure per-player data blocks
    // Block 1 at g_playerDataArray2 + 260/261
    g_playerDataArray2[261] = 0;    // clear secondary flag
    g_playerDataArray2[260] = 1;    // set primary flag

    // Block 2 at g_playerDataArray2 + 676/677
    g_playerDataArray2[677] = 0;    // clear secondary flag
    g_playerDataArray2[676] = 1;    // set primary flag
}

// ═════════════════════════════════════════════════════════════════════════════
// gmLogicSinglesMatch::stateHelpTips — HSM state for in-match help tip display
//
// Vtable @ 0x8203131C. Inherits from hsmState.
// State struct layout:
//   +0x00: void** vtable
//   +0x04: void*  m_pHsmContext     — owning HSM context
//   +0x08: void*  m_pParentLogic    — owning gmLogicSinglesMatch instance
//   +0x10: uint8_t m_bTipChanged    — set when a new tip is queued
//   +0x11: uint8_t m_bDismissed     — set after dismiss message sent
// ═════════════════════════════════════════════════════════════════════════════

// External function for stateHelpTips
extern "C" {
    void stateHelpTips_ShowTip(void* self);  // stateHelpTips_AA50 @ 0x8210AA50
}

// ─────────────────────────────────────────────────────────────────────────────
// stateHelpTips::GetName  [vtable slot 13 @ 0x8210AAE8] | size: 0x0C
// Returns the state name string for HSM debugging/identification.
// ─────────────────────────────────────────────────────────────────────────────
const char* stateHelpTips_GetName(void* /*self*/) { // @ 0x8210AAE8
    return "HelpTips";
}

// ─────────────────────────────────────────────────────────────────────────────
// stateHelpTips::OnLeave  [vtable slot 14 @ 0x8210AA40] | size: 0x0C
// Clears the dismissed flag when leaving the state.
// ─────────────────────────────────────────────────────────────────────────────
void stateHelpTips_OnLeave(void* self) { // @ 0x8210AA40
    *(uint8_t*)((char*)self + 17) = 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// stateHelpTips::OnEnter  [vtable slot 11 @ 0x8210A8E8] | size: 0x44
// Enters the help tips state. Calls base OnEnter, clears both flags,
// then immediately shows the first tip.
// ─────────────────────────────────────────────────────────────────────────────
void stateHelpTips_OnEnter(void* self) { // @ 0x8210A8E8
    // Call base OnEnter with param=0
    stateServeBounce_OnEnter(self, 0);

    // Clear flags
    *(uint8_t*)((char*)self + 17) = 0;
    *(uint8_t*)((char*)self + 16) = 0;

    // Show the initial tip
    stateHelpTips_ShowTip(self);
}

// ─────────────────────────────────────────────────────────────────────────────
// stateHelpTips::Update  [vtable slot 10 @ 0x8210A930] | size: 0x7C
// Called each frame. If m_bTipChanged is set, refreshes the tip display
// and clears the flag. Otherwise, if not yet dismissed, sends the dismiss
// message (2138) and sets the dismissed flag.
// ─────────────────────────────────────────────────────────────────────────────
void stateHelpTips_Update(void* self) { // @ 0x8210A930
    char* state = (char*)self;

    // Check if a new tip was queued
    uint8_t tipChanged = *(uint8_t*)(state + 16);
    if (tipChanged != 0) {
        // Refresh the tip display
        stateHelpTips_ShowTip(self);
        *(uint8_t*)(state + 16) = 0;
        return;
    }

    // If already dismissed, nothing more to do
    uint8_t dismissed = *(uint8_t*)(state + 17);
    if (dismissed != 0) {
        return;
    }

    // Send dismiss help tips message (2138) to page group system
    PostPageGroupMessage(2138, 64, 0, nullptr);

    // Mark as dismissed
    *(uint8_t*)(state + 17) = 1;
}

// ═════════════════════════════════════════════════════════════════════════════
// gmLogicSinglesMatch::stateAnticipationCam — HSM state for pre-serve camera
//
// Vtable @ 0x82030E8C. Inherits from hsmState.
// ═════════════════════════════════════════════════════════════════════════════

// ─────────────────────────────────────────────────────────────────────────────
// stateAnticipationCam::GetName  [vtable slot 13 @ 0x82107708] | size: 0x0C
// Returns the state name string for HSM debugging/identification.
// ─────────────────────────────────────────────────────────────────────────────
const char* stateAnticipationCam_GetName(void* /*self*/) { // @ 0x82107708
    return "AnticipationCam";
}


// ═════════════════════════════════════════════════════════════════════════════
// gmLogicSinglesMatch — Singles match state machine
//
// Anchored by the state-transition log string
//   "gmLogicSinglesMatch's next state was %s, is %s"
// and by
//   "gmLogicSinglesMatch::MidGame(): Unknown PointsPerGame enum value = %d"
//
// The class's state family (from RTTI typeinfos) spans 33 sub-states, grouped
// into: setup (stateInit, statePreMatchSync, statePreMatch, statePreGame,
// stateAnticipationCam, statePrePreServe, statePreServeSpectatorSyncState,
// stateServeBounce, stateServe, ...), mid-game (stateReplay, stateReplayNego-
// tiation(PreSync), statePostPoint, statePostPointCS, statePostGame), and
// closure (statePostMatch, statePostTourney, statePostTourneyMovie,
// statePostPostGame, stateSaveDialog, stateUnlockDialog). All substates
// inherit from hsmState and live in the vtable @ 0x82030CC4 family.
//
// Struct layout (fields actually touched by the vfns below):
//   +0x04  uint32_t  m_flags               (or state count?)
//   +0x08  void**    m_stateArray           (array of hsmState*)
//   +0x0c  int32_t   m_currentStateIndex    (-1 == none)
//   +0x1c  float     m_elapsedTotal         (vfn_11 accumulator)
//   +0x20  uint8_t   m_updateReplayTimer
//   +0x24  float     m_elapsedReplay
//   +0x28  float     m_elapsedBonus         (only if state==3)
//   +0x30  void*     m_pNetworkClient       (nullable)
//   +0x34  uint8_t   m_isTrainingDrill      (enables substate 21)
//   +0x36  uint8_t   m_bFlagB
//   +0x38  uint32_t  m_someCounter
// ═════════════════════════════════════════════════════════════════════════════

// Named externs for the match log/error strings (documented anchors)
extern char g_str_gmLogicSinglesMatch_nextState[];       // "gmLogicSinglesMatch's next state was %s, is %s"
extern char g_str_gmLogicSinglesMatch_MidGameBadEnum[];  // "gmLogicSinglesMatch::MidGame(): Unknown PointsPerGame enum value = %d"
extern char g_str_gmLogicSinglesMatch_replayOnEnter[];   // "gmLogicSinglesMatch::stateReplay::onEnterState"

// External helpers referenced by the vfns below (real PPC recomp names)
extern "C" {
    void  singles_Timer_58E0_h(void* self);                 // +0x821058E0
    void  singles_5860(void* self);                         // +0x82105860 (base_onExit chain)
    void  singles_5B70(void* self);                         // +0x82105B70 (base_onEnter chain)
    void  singles_5D38_dispatch(void* self);                // +0x82105D38
    void* SinglesNetworkClient_25D0_v12(void* netClient);   // +0x823D25D0 — network tick
    void  PostGlobalMessage(int msgId, int mask, int argc, void* args); // pg_E6E0 @ 0x8225E6E0
    void  hsmContext_SetNextState(void* self, int stateId);
    uint8_t IsNetworkActiveAndNotDisconnected();            // pg_10E0_g @ 0x821010E0
    bool  CanDispatchTrainingEvent_21(void* self, int evtId); // atSingleton_67E0_g @ 0x821067E0
}

// ─────────────────────────────────────────────────────────────────────────────
// gmLogicSinglesMatch::vfn_10  [slot 10 @ 0x82105AA8] | size: 0x4C
// Mini-destructor / reset hook. Chains base reset + timer reset + clears
// training-drill flags and counters (+44, +54, +56).
// ─────────────────────────────────────────────────────────────────────────────
void gmLogicSinglesMatch_vfn_10(void* self) { // @ 0x82105AA8
    singles_5860(self);                     // base deinit
    singles_5B70(self);                     // timer/serve reset
    singles_Timer_58E0_h(self);             // secondary timer reset
    *(uint8_t*)((char*)self + 44) = 0;
    *(uint8_t*)((char*)self + 54) = 0;
    *(uint32_t*)((char*)self + 56) = 0;
}

// ─────────────────────────────────────────────────────────────────────────────
// gmLogicSinglesMatch::vfn_12  [slot 12 @ 0x821057C0] | size: 0x9C
// Per-frame dispatch. If a network client is attached at +0x30, tick it and,
// if its session is positive, run the internal dispatch chain. Also gates a
// "state 21" (training drill) event on m_isTrainingDrill.
// ─────────────────────────────────────────────────────────────────────────────
void gmLogicSinglesMatch_vfn_12(void* self) { // @ 0x821057C0
    void* netClient = *(void**)((char*)self + 48);
    if (netClient != nullptr) {
        // The game returns vtable@0x82030D60 via the v12 helper, effectively
        // (char*)netClient + 0x0D60 — a subobject handled by SinglesNetwork-
        // Client_25D0_v12. Treat as "if tick returned > 0, run dispatch".
        SinglesNetworkClient_25D0_v12((char*)netClient + 3424);
        int32_t tickResult = *(int32_t*)((char*)netClient + 3424);
        if (tickResult > 0) {
            singles_5D38_dispatch(self);
        }
    }

    // Training-drill pipe: +0x34 flag, sub-state index at +0x0C must be [1,19]
    if (*(uint8_t*)((char*)self + 52) != 0) {
        int32_t idx = *(int32_t*)((char*)self + 12);
        if (idx >= 1 && idx < 20) {
            CanDispatchTrainingEvent_21(self, 21);
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// gmLogicSinglesMatch::vfn_13  [slot 13 @ 0x82105AF8] | size: 0x78
// CanTransitionTo(stateId). Rejects out-of-range ids, fast-paths the training-
// drill virtual state (21), then delegates to the current sub-state's
// vtable slot 15 (CanTransitionTo). Accepts state 3 when no sub-state set.
// ─────────────────────────────────────────────────────────────────────────────
bool gmLogicSinglesMatch_vfn_13(void* self, int stateId) { // @ 0x82105AF8
    int32_t stateCount = *(int32_t*)((char*)self + 4);
    if (stateId >= stateCount) {
        return false;
    }

    // Training-drill virtual state
    if (*(uint8_t*)((char*)self + 52) != 0 && stateId == 21) {
        return true;
    }

    int32_t curIdx = *(int32_t*)((char*)self + 12);
    if (curIdx != -1) {
        void** stateArray = *(void***)((char*)self + 8);
        void* curState = stateArray[curIdx];
        if (curState != nullptr) {
            void** vt = *(void***)curState;
            typedef bool (*CanTransFn)(void*, int);
            return ((CanTransFn)vt[15])(curState, stateId);
        }
    }

    // No active state: only allow transition to state 3 (stateAnticipationCam)
    return stateId == 3;
}

// ─────────────────────────────────────────────────────────────────────────────
// gmLogicSinglesMatch::vfn_20  [slot 20 @ 0x82106788] | size: 0x58
// Teardown / "force exit" hook. If a network client is attached, posts
// event 14372 (MSG_NETWORK_FORCE_EXIT) and nulls the +0x30 pointer.
// ─────────────────────────────────────────────────────────────────────────────
void gmLogicSinglesMatch_vfn_20(void* self) { // @ 0x82106788
    if (*(void**)((char*)self + 48) != nullptr) {
        uint32_t arg = 1;
        PostGlobalMessage(14372, 0, 1, &arg);
        *(void**)((char*)self + 48) = nullptr;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// gmLogicSinglesMatch::stateReplay::onEnterState  @ 0x8210AFD0 | size: 0x168
//
// Runs the base OnEnter (0x82106A60, with 0), posts message 0x850, clears the
// state's bytes at +0x11..+0x13 and the byte at 0x82606670, and logs
// "gmLogicSinglesMatch::stateReplay::onEnterState" through game_3860.
// Without a replay (match context +0x1D clear) it clears +0x10 and calls
// 0x8210B320. Otherwise it hands the replay's last entry to 0x821676A8 (unless
// the replay's byte +0x68CFB is set), copies a word from 0x8271A324+0x110 into
// the replay when +0x68CFC is set, runs 0x821CCE00 on the replay, sets
// +0x68CF4 when +0x68CF9 is set, and finally sets +0x10 and context +0x25.
// ─────────────────────────────────────────────────────────────────────────────

struct stateReplayView {
    uint8_t _pad00[0x10];
    uint8_t m_hasReplay;  // +0x10
    uint8_t field_11;     // +0x11
    uint8_t field_12;     // +0x12
    uint8_t field_13;     // +0x13
};

struct singlesMatchContextView {   // *(0x8271A2FC)
    uint8_t _pad00[0x1D];
    uint8_t m_replayAvailable;     // +0x1D
    uint8_t _pad1E[7];
    uint8_t m_replayRunning;       // +0x25
};

struct replayEntry {               // 16 bytes
    uint8_t bytes[16];
};

struct replayEntryList {
    replayEntry* m_entries;        // +0x00
    uint16_t     m_count;          // +0x04
};

struct replayDataView {            // *(0x8271A2EC)
    uint8_t          _pad00000[0x68CF4];
    int32_t          field_68CF4;  // +0x68CF4  set to 1 when +0x68CF9 is set
    uint8_t          _pad68CF8[1];
    uint8_t          field_68CF9;  // +0x68CF9
    uint8_t          _pad68CFA[1];
    uint8_t          field_68CFB;  // +0x68CFB  skips the entry hand-off
    uint8_t          field_68CFC;  // +0x68CFC  copy 0x8271A324+0x110 into +0x68D00
    uint8_t          _pad68CFD[1];
    uint8_t          field_68CFE;  // +0x68CFE  use entry 0 - 1 instead of the last one
    uint8_t          _pad68CFF[1];
    void*            field_68D00;  // +0x68D00
    uint8_t          _pad68D04[0xC];
    replayEntryList* m_entryList;  // +0x68D10
};

struct lbl_8260641CView {          // *(0x8260641C)
    uint8_t _pad00[0x2C];
    void*   field_2C;              // +0x2C  first argument to 0x821676A8
};

struct lbl_8271A324View {          // *(0x8271A324)
    uint8_t _pad000[0x110];
    void*   field_110;             // +0x110
};

extern "C" {
    void stateServeBounce_OnEnter(void* self, int param);  // @ 0x82106A60
    void stateReplay_B320_fallback(void* self);            // @ 0x8210B320
}
extern singlesMatchContextView* g_pActiveMatchContext;  // @ 0x8271A2FC
extern replayDataView*          g_pReplayStateData;     // @ 0x8271A2EC
extern lbl_8271A324View*        lbl_8271A324;           // @ 0x8271A324
extern lbl_8260641CView*        lbl_8260641C;           // @ 0x8260641C
extern uint8_t                  g_ReplayActive;         // @ 0x82606670 (the earlier lift's name; unproven)
extern void* g_game_state_ptr;                          // @ 0x8271A2F8
void game_3860(void* gameState, int kind, const char* name);  // @ 0x821D3860, lifted below
extern void game_76A8(void* owner, replayEntry* entry);       // @ 0x821676A8
extern void util_CE00(replayDataView* replay);                // @ 0x821CCE00

void gmLogicSinglesMatch_stateReplay_OnEnter(void* self) { // @ 0x8210AFD0
    stateReplayView* state = static_cast<stateReplayView*>(self);

    stateServeBounce_OnEnter(self, 0);
    PostGlobalMessage(0x850, 0x40, 0, nullptr);

    uint8_t replayAvailable = g_pActiveMatchContext->m_replayAvailable;
    state->field_11 = 0;
    state->field_12 = 0;
    state->field_13 = 0;
    g_ReplayActive = 0;
    game_3860(g_game_state_ptr, 1, "gmLogicSinglesMatch::stateReplay::onEnterState");

    if (replayAvailable == 0) {
        state->m_hasReplay = 0;
        stateReplay_B320_fallback(self);
        return;
    }

    replayDataView* replay = g_pReplayStateData;
    if (replay->field_68CFB == 0) {
        uint16_t count = 0;
        if (replay->field_68CFE == 0 && replay->m_entryList != nullptr) {
            count = replay->m_entryList->m_count;
        }
        game_76A8(lbl_8260641C->field_2C, replay->m_entryList->m_entries + count - 1);
        replay = g_pReplayStateData;
    }

    if (replay->field_68CFC != 0) {
        replay->field_68D00 = lbl_8271A324->field_110;
    }

    util_CE00(replay);

    if (replay->field_68CF9 != 0) {
        replay->field_68CF4 = 1;
    }

    state->m_hasReplay = 1;
    g_pActiveMatchContext->m_replayRunning = 1;
}

// ─────────────────────────────────────────────────────────────────────────────
// gmLogicSinglesMatch::MidGame  @ 0x8238CA38 | size: 0x10 (thunk)
//
// Tiny dispatch thunk — the strings index points at the typeinfo that fires
// the error log "MidGame(): Unknown PointsPerGame enum value = %d". The real
// body is a tail-call to a jump table over m_PointsPerGame (0..N-1).
// Shape observed in similar 0x10-byte vfn thunks across this codebase:
//     r11 = this->vtable;
//     r3  = this + 8;        // private "match state" context
//     mtctr [r11 + <slot>];
//     bctr
// Documented here as a tail-call. The out-of-range case hits the error str.
// ─────────────────────────────────────────────────────────────────────────────
void gmLogicSinglesMatch_MidGame(void* self) { // @ 0x8238CA38
    // Tail-call through vtable into the PointsPerGame jump-table impl.
    // Default (out-of-range) slot logs g_str_gmLogicSinglesMatch_MidGameBadEnum.
    void** vt = *(void***)self;
    typedef void (*MidGameImplFn)(void*);
    ((MidGameImplFn)vt[/*slot filled by the dispatcher*/ 0])((char*)self + 8);
}


// ═════════════════════════════════════════════════════════════════════════════
// gmLogicSwingPractice — single-player swing practice mode
//
// Vtable @ 0x820303F4. Slot 8 (0x821020D8) builds the eight HSM states into
// m_states: statePreInit, stateInit, stateMainMenu, stateAim, stateShoot,
// stateAwaitReturnHit, stateReturnHit, statePostPoint. Each one is
// {vtable, 0, owning gmLogicSwingPractice*, ...}.
//
// Besides the HSM states the logic owns eleven objects at +0x28 (one active,
// index at +0x54), the ball robot at +0x94 and the practice target at +0x98.
// Their vtable slots used here: 0 scalar deleting destructor, 6 Update(dt),
// 8 OnMessage(msg), 9 (stateAim passes 1).
// ═════════════════════════════════════════════════════════════════════════════

// Loads a virtual function out of an object's vtable (the guest's
// `lwz r11,0(r3); lwz r11,slot*4(r11); mtctr; bctrl`).
template <typename Fn>
static Fn VirtualSlot(const void* object, int slot) {
    return reinterpret_cast<Fn>((*static_cast<void* const* const*>(object))[slot]);
}

// rage::sysTimeManager instance (vtable 0x82038CA8). The image holds 1/60 at
// +0x08 and 60.0 at +0x0C; +0x08 is what the game scales per-frame motion by.
struct sysTimeManagerView {
    void**   vtable;            // +0x00
    uint32_t field_04;          // +0x04
    float    m_frameSeconds;    // +0x08
    float    m_framesPerSecond; // +0x0C
};
extern sysTimeManagerView g_sysTimeManager;  // @ 0x825CAEB8

extern void* g_game_state_ptr;               // @ 0x8271A2F8
// Set elsewhere; stateAim moves the target to a new random spot and clears it.
extern uint8_t g_swingPracticeMoveTarget;    // @ 0x8260637A (lbl_8260637A)

extern void rage_free(void* ptr);            // @ 0x820C00C0
// @ 0x82101FD0 — gmLogicSwingPractice's destructor body: deletes the eleven
// children, the ball robot and the target, tears down +0x18, then runs gmLogic's.
extern void gmLogicSwingPractice_Destruct(gmLogicSwingPractice* logic);
// @ 0x821129D0 — wraps a value into [min, max] (lifted, unbuilt, in cm_cam_actions.cpp).
extern "C" float WrapValueInRange(float value, float min, float max);
// @ 0x82112508 (LocomotionStateAnim_2508_h) — per-frame update of the object at
// +0x94. Its neighbours 0x821120A8..0x821129C8 are gmBallRobot's methods.
extern void gmBallRobot_Update(gmBallRobot* robot);
// @ 0x82113A98 (gmPracticeTarget_3A98_p46) — puts the target at a random spot
// on the table (RNG at 0x825CA2C8, table size via 0x8271A304) and hands the
// position to 0x82113BA8. stateAim passes 1 in r4; the callee never reads it.
extern void gmPracticeTarget_PlaceRandomly(gmPracticeTarget* target, int unused);
// @ 0x821D3860 — game_3860, lifted at the end of this file.
void game_3860(void* gameState, int kind, const char* name);
// @ 0x8225E480 (pg_E480) — posts a message whose arguments follow a format
// string ('i' and 'f', 32 bits each); floats travel as their bit patterns.
extern void PostPageGroupMessageFmt(uint32_t messageId, uint32_t mask, const char* format, ...);

static uint32_t FloatBits(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    return bits;
}

static const float kTwoPi = 6.28318548f;     // @ 0x8202C02C
static const float kMinusPi = -3.14159274f;  // @ 0x82079B2C
static const float kPi = 3.14159274f;        // @ 0x82079B30

/**
 * gmLogicSwingPractice::ScalarDeletingDtor  [slot 0] @ 0x82101F80 | size: 0x50
 *
 * Runs the destructor body, then frees the object when bit 0 of flags is set.
 */
gmLogicSwingPractice* gmLogicSwingPractice::ScalarDeletingDtor(uint32_t flags) {
    gmLogicSwingPractice_Destruct(this);
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

/**
 * gmLogicSwingPractice::ResetTarget  [slot 10] @ 0x82102A58 | size: 0x34
 *
 * Lets the target spin again and re-arms it; unless a confirmation is pending,
 * no child stays active.
 */
void gmLogicSwingPractice::ResetTarget() {
    m_pTarget->m_spinStopped = 0;
    m_pTarget->field_17 = 1;
    m_pTarget->field_16 = 0;
    if (m_awaitingConfirm != 0) {
        return;
    }
    m_activeChild = -1;
}

/**
 * gmLogicSwingPractice::Update  [slot 11] @ 0x82102A90 | size: 0xCC
 *
 * Spins the target one turn per second (angle kept in [-pi, pi]), updates the
 * ball robot and passes the frame time to the active child's slot 6.
 */
void gmLogicSwingPractice::Update() {
    if (m_targetEnabled != 0) {
        gmPracticeTarget* target = m_pTarget;
        if (target != nullptr && target->m_spinStopped == 0) {
            target->m_spinAngle = g_sysTimeManager.m_frameSeconds * kTwoPi + target->m_spinAngle;
            target->m_spinAngle = WrapValueInRange(target->m_spinAngle, kMinusPi, kPi);
        }
    }

    if (m_pBallRobot != nullptr) {
        gmBallRobot_Update(m_pBallRobot);
    }

    if (HasActiveChild()) {
        gmLogicChild* child = m_children[m_activeChild];
        VirtualSlot<void (*)(gmLogicChild*, float)>(child, 6)(child, g_sysTimeManager.m_frameSeconds);
    }
}

/**
 * gmLogicSwingPractice::CanTransitionTo  [slot 13] @ 0x82102B60 | size: 0x5C
 *
 * Out-of-range ids are refused. Otherwise the current HSM state decides
 * (tail call to its slot 15 with the same id); with no current state only
 * state 1 is allowed.
 */
bool gmLogicSwingPractice::CanTransitionTo(int32_t stateId) {
    if (stateId >= m_stateCount) {
        return false;
    }
    if (m_currentState != -1) {
        hsmState* state = m_states[m_currentState];
        if (state != nullptr) {
            return VirtualSlot<uint8_t (*)(hsmState*, int32_t)>(state, 15)(state, stateId) != 0;
        }
    }
    return stateId == 1;
}

/**
 * gmLogicSwingPractice::AddToDrawBuckets  [slot 15] @ 0x82102BC0 | size: 0x2C
 *
 * While the target is enabled, tail-calls its slot 2 (gmPracticeTarget::
 * AddToDrawBucket).
 */
void gmLogicSwingPractice::AddToDrawBuckets() {
    if (m_targetEnabled == 0) {
        return;
    }
    gmPracticeTarget* target = m_pTarget;
    if (target == nullptr) {
        return;
    }
    VirtualSlot<void (*)(gmPracticeTarget*)>(target, 2)(target);
}

/**
 * gmLogicSwingPractice::OnMessage  [slot 18] @ 0x82102BF0 | size: 0x168
 *
 * 0x500C: with a child active, mark a confirmation pending and call own slot 3.
 * 0x500D: clear the pending confirmation.
 * Anything else goes to the current HSM state's OnMessage (slot 16) unless a
 * transition is pending, then to the active child's slot 8.
 */
void gmLogicSwingPractice::OnMessage(const gmMessage* msg) {
    hsmState* state = (m_currentState == -1) ? nullptr : m_states[m_currentState];

    if (msg->m_id == 0x500C) {
        if (HasActiveChild()) {
            m_awaitingConfirm = 1;
            VirtualSlot<void (*)(gmLogicSwingPractice*)>(this, 3)(this);
        }
        return;
    }

    if (msg->m_id == 0x500D) {
        m_awaitingConfirm = 0;
        return;
    }

    if (state != nullptr && m_nextState == -1) {
        VirtualSlot<void (*)(hsmState*, const gmMessage*)>(state, 16)(state, msg);
    }
    if (HasActiveChild()) {
        gmLogicChild* child = m_children[m_activeChild];
        VirtualSlot<void (*)(gmLogicChild*, const gmMessage*)>(child, 8)(child, msg);
    }
}

/**
 * gmLogicSwingPractice::stateAim::OnEnter  [slot 11] @ 0x82103878 | size: 0x15C
 *
 * Logs "gmLogicSwingPractice::stateAim::onEnterState", posts message 0x83C,
 * moves the target if g_swingPracticeMoveTarget asks for it, posts the aim
 * point (0x1017, "fff") when the logic has one and 0x29 ("ff", 1.0 and 0.0),
 * then calls the active child's slot 9 with 1.
 */
void gmLogicSwingPractice::stateAim::OnEnter() {
    const float zero = 0.0f;  // @ 0x8202D110
    const float one = 1.0f;   // @ 0x8202D108

    m_timeInState = zero;
    field_10 = 0;
    game_3860(g_game_state_ptr, 1, "gmLogicSwingPractice::stateAim::onEnterState");
    PostPageGroupMessage(0x83C, 0x40, 0, nullptr);

    if (g_swingPracticeMoveTarget != 0) {
        gmPracticeTarget* target = m_pLogic->m_pTarget;
        target->m_spinStopped = 0;
        target->field_17 = 1;
        gmPracticeTarget_PlaceRandomly(m_pLogic->m_pTarget, 1);
        g_swingPracticeMoveTarget = 0;
    }

    gmLogicSwingPractice* logic = m_pLogic;
    if (logic->m_hasAimPoint != 0) {
        PostPageGroupMessageFmt(0x1017, 1, "fff", FloatBits(logic->m_aimPoint[0]),
                                FloatBits(logic->m_aimPoint[1]), FloatBits(logic->m_aimPoint[2]));
    }

    PostPageGroupMessageFmt(0x29, 0x80, "ff", FloatBits(one), FloatBits(zero));

    logic = m_pLogic;
    if (logic->HasActiveChild()) {
        gmLogicChild* child = logic->m_children[logic->m_activeChild];
        VirtualSlot<void (*)(gmLogicChild*, int)>(child, 9)(child, 1);
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// gmPracticeTarget — the swing-practice target
//
// Bases rage::datBase (+0x00) and pongRenderable (+0x04); see pong_match.hpp.
// ═════════════════════════════════════════════════════════════════════════════

extern void* g_gmPracticeTarget_vtable[];             // @ 0x82032414
extern void* g_gmPracticeTarget_pongRenderable_vtable[];  // @ 0x82032428
extern void* g_pongRenderable_vtable[];               // @ 0x82032404

// The allocator sequence the 360 build inlines for `new`: 0x820C0038 makes sure
// the thread's allocator table exists, then the current allocator's slot 1
// (Allocate(size, align)) is called.
extern "C" void sysMemAllocator_InitMainThread();     // @ 0x820C0038
namespace rage { void* rage_alloc_aligned(unsigned long size, unsigned long alignment); }
// The matching inlined `delete`: pointers inside a resource are left alone,
// anything else goes back through the current allocator's slot 2.
namespace rage { uint8_t FindSingleton(void* ptr); }  // @ 0x820F90D0
extern "C" void sysMemAllocator_Free(void* ptr);
extern "C" void* xe_EC88(uint32_t size);              // @ 0x820DEC88, operator new

static void* AllocateAligned(uint32_t size, uint32_t alignment) {
    sysMemAllocator_InitMainThread();
    return rage::rage_alloc_aligned(size, alignment);
}

// @ 0x82112CC0 (rage_2CC0) — gmPracticeTarget's destructor body: restores both
// vtables, deletes the sets, zeroes the set count, frees the word array and
// the six Fx strings/colours, then stores datBase's vtable 0x820176C4.
extern void gmPracticeTarget_Destruct(gmPracticeTarget* target);
// @ 0x821132B0 (pongDrillCounterSpin_32B0_p46) — fills the table at 0x82617C90
// with points scaled by the table size (0x8271A304 +0x10/+0x18). Takes no
// arguments; the constructor still has `this` in r3 when it calls it.
extern void gmPracticeTarget_LayOutTableGrid();

/**
 * gmPracticeTargetFx::Construct @ 0x82113D10 | size: 0xE4
 *
 * No texture, height offset 0.001, and two zeroed 16-byte colours.
 */
gmPracticeTargetFx* gmPracticeTargetFx::Construct() {
    const float zero = 0.0f;  // @ 0x8202D110
    m_heightOffset = 0.001f;  // @ 0x8202D168
    m_textureName = nullptr;

    float* color = static_cast<float*>(AllocateAligned(16, 16));
    if (color != nullptr) {
        color[0] = zero;
        color[1] = zero;
        color[2] = zero;
        color[3] = zero;
    } else {
        color = nullptr;
    }
    m_color = color;

    float* altColor = static_cast<float*>(AllocateAligned(16, 16));
    if (altColor != nullptr) {
        altColor[0] = zero;
        altColor[1] = zero;
        altColor[2] = zero;
        altColor[3] = zero;
        m_altColor = altColor;
        return this;
    }
    m_altColor = nullptr;
    return this;
}

/**
 * gmPracticeTarget::Construct @ 0x82112B58 | size: 0x114
 *
 * Runs pongRenderable's part (vtable 0x82032404, then gmPracticeTarget's
 * 0x82032428), sets the flags, constructs both Fx members, puts the target at
 * the origin, allocates its word array and lays out the table grid.
 */
gmPracticeTarget* gmPracticeTarget::Construct() {
    const float zero = 0.0f;  // @ 0x8202D110
    const float one = 1.0f;   // @ 0x8202D108

    m_renderable.field_08 = zero;
    m_renderable.field_0C = 0;
    m_renderable.vtable = g_pongRenderable_vtable;
    m_renderable.field_10 = -1;
    vtable = g_gmPracticeTarget_vtable;
    field_16 = 0;
    field_1C = 0;
    m_renderable.vtable = g_gmPracticeTarget_pongRenderable_vtable;
    m_visible = 1;
    m_drawEnabled = 1;
    field_17 = 1;
    field_20 = 0;
    m_fx.Construct();
    m_fx2.Construct();

    m_spinAngle = zero;
    field_44 = 0;
    m_sets = nullptr;
    m_position[0] = zero;
    m_position[1] = zero;
    m_position[2] = zero;
    m_position[3] = one;

    // 0x14 bytes on the 360.
    gmPracticeTargetWordArray* wordArray = static_cast<gmPracticeTargetWordArray*>(
        AllocateAligned(sizeof(gmPracticeTargetWordArray), 16));
    if (wordArray != nullptr) {
        wordArray->m_data = nullptr;
        wordArray->m_count = 0;
        wordArray->m_capacity = 0;
        wordArray->field_0C = 0;
        wordArray->m_flags &= 0x3F;
    } else {
        wordArray = nullptr;
    }
    m_wordArray = wordArray;

    gmPracticeTarget_LayOutTableGrid();
    return this;
}

/**
 * gmPracticeTarget::ScalarDeletingDtor  [slot 0] @ 0x82112C70 | size: 0x50
 *
 * Runs the destructor body, then frees the object when bit 0 of flags is set.
 */
gmPracticeTarget* gmPracticeTarget::ScalarDeletingDtor(uint32_t flags) {
    gmPracticeTarget_Destruct(this);
    if (flags & 1) {
        rage_free(this);
    }
    return this;
}

// rage::fiAssetManager (rage::ASSET): a stack of 128-byte folder names at
// +0x180 with its depth at +0x600. The callers pop a folder inline.
struct fiAssetManagerView {
    uint8_t _pad000[0x600];
    int32_t m_folderDepth;  // +0x600
};
extern fiAssetManagerView g_fiAssetManager;  // @ 0x825D0080
struct fiStream;
// @ 0x822E2E60 — pushes a folder ("$/..." is taken as is).
extern void fiAssetManager_PushFolder(fiAssetManagerView* assets, const char* path);
// @ 0x822E3040 — opens name.ext in the current folder; the loaders pass 0, 1.
extern fiStream* fiAssetManager_Open(fiAssetManagerView* assets, const char* name, const char* ext,
                                     int arg3, int arg4);
// @ 0x822E3B38
extern void fiStream_Close(fiStream* stream);

// rage::fiTokenizer as the loaders build it on the stack (vtable 0x8205A594).
struct fiTokenizerView {
    void**      vtable;        // +0x00
    const char* m_name;        // +0x04  the file's name
    int32_t     field_08;      // +0x08  1
    fiStream*   m_stream;      // +0x0C
    int32_t     field_10;      // +0x10  0x20
    int32_t     field_14;      // +0x14  2
    int32_t     field_18;      // +0x18  0
    char        m_buffer[0x80];// +0x1C  first byte cleared
    int32_t     field_9C;      // +0x9C  0
    int32_t     field_A0;      // +0xA0  0
};
extern void* g_fiTokenizer_vtable[];  // @ 0x8205A594
// @ 0x822E5908 — reads a token; true when it equals `token`, otherwise puts it back.
extern bool fiTokenizer_CheckToken(fiTokenizerView* tokenizer, const char* token, bool consume);
// @ 0x822E5E88
extern int32_t fiTokenizer_GetInt(fiTokenizerView* tokenizer);
// @ 0x822E5F08
extern float fiTokenizer_GetFloat(fiTokenizerView* tokenizer);

// The tokenizer constructor every loader inlines.
static void fiTokenizer_Init(fiTokenizerView* tokenizer, const char* name, fiStream* stream) {
    tokenizer->field_A0 = 0;
    tokenizer->vtable = g_fiTokenizer_vtable;
    tokenizer->field_08 = 1;
    tokenizer->m_name = name;
    tokenizer->m_stream = stream;
    tokenizer->field_10 = 0x20;
    tokenizer->field_18 = 0;
    tokenizer->m_buffer[0] = 0;
    tokenizer->field_9C = 0;
    tokenizer->field_14 = 2;
}

// Slot 1 of the tokenizer: reads the next token into buffer (at most size bytes).
static void fiTokenizer_GetToken(fiTokenizerView* tokenizer, char* buffer, int size) {
    VirtualSlot<void (*)(fiTokenizerView*, char*, int)>(tokenizer, 1)(tokenizer, buffer, size);
}

// @ 0x82113DF8 (atSingleton_3DF8_h) — reads TextureName, Color, AltColor and
// HeightOffset, each only if its token is next.
extern void gmPracticeTargetFx_Load(gmPracticeTargetFx* fx, fiTokenizerView* tokenizer);
// @ 0x82113F20 (pongNetMessageHolder_3F20_w) — reads "NumTargets" and that many
// 0x44-byte targets (nine ints, then two groups of four floats).
extern void gmPracticeTargetSet_Load(gmPracticeTargetSet* set, fiTokenizerView* tokenizer);
// @ 0x821B2A58 (pg_2A58_g) — allocates `capacity` words; count = capacity.
extern void gmPracticeTargetWordArray_Init(gmPracticeTargetWordArray* array, int32_t capacity,
                                           bool flag6, bool flag7);

extern int32_t  g_practiceTargetNumSets;       // @ 0x826063AC (lbl_826063AC)
extern uint32_t g_practiceTargetDefaultColor;  // @ 0x825CA198, 0xAARRGGBB
extern uint32_t g_practiceTargetHitColor;      // @ 0x825CA19C, 0xAARRGGBB

// Reads four floats (R, G, B, A in 0..1) and packs them as 0xAARRGGBB; each
// channel is the low byte of the float times 255 truncated to an int.
static uint32_t ReadColor(fiTokenizerView* tokenizer) {
    const float scale = 255.0f;  // @ 0x82079BE0
    float r = fiTokenizer_GetFloat(tokenizer);
    float g = fiTokenizer_GetFloat(tokenizer);
    float b = fiTokenizer_GetFloat(tokenizer);
    float a = fiTokenizer_GetFloat(tokenizer);
    uint32_t alpha = static_cast<uint8_t>(static_cast<int32_t>(a * scale));
    uint32_t red = static_cast<uint8_t>(static_cast<int32_t>(r * scale));
    uint32_t green = static_cast<uint8_t>(static_cast<int32_t>(g * scale));
    uint32_t blue = static_cast<uint8_t>(static_cast<int32_t>(b * scale));
    return (alpha << 24) | (red << 16) | (green << 8) | blue;
}

// Opens name.fx and loads one Fx from it.
static void LoadFx(gmPracticeTargetFx* fx, const char* name) {
    fiStream* stream = fiAssetManager_Open(&g_fiAssetManager, name, "fx", 0, 1);
    if (stream == nullptr) {
        return;
    }
    fiTokenizerView tokenizer;
    fiTokenizer_Init(&tokenizer, name, stream);
    gmPracticeTargetFx_Load(fx, &tokenizer);
    fiStream_Close(stream);
}

/**
 * gmPracticeTarget::LoadData  [slot 1] @ 0x82112DF8 | size: 0x4B4
 *
 * From "$/fx": fx_target.fx into m_fx, fx_target2.fx into m_fx2, then
 * practice_targets.fx:
 *     NumSets n                      (also kept in g_practiceTargetNumSets)
 *     TargetDefaultColor r g b a     (0..1, packed into g_practiceTargetDefaultColor)
 *     TargetHitColor r g b a
 *     Set <token> NumTargets ... <token>   (n times)
 * The word array is sized for the largest set. Ends by popping "$/fx",
 * pushing "$/fx/tex" and popping it again.
 */
void gmPracticeTarget::LoadData() {
    fiAssetManager_PushFolder(&g_fiAssetManager, "$/fx");

    LoadFx(&m_fx, "fx_target");
    LoadFx(&m_fx2, "fx_target2");

    int32_t maxTargets = 0;
    fiStream* stream = fiAssetManager_Open(&g_fiAssetManager, "practice_targets", "fx", 0, 1);
    if (stream != nullptr) {
        fiTokenizerView tokenizer;
        fiTokenizer_Init(&tokenizer, "practice_targets", stream);

        if (fiTokenizer_CheckToken(&tokenizer, "NumSets", true)) {
            int32_t numSets = fiTokenizer_GetInt(&tokenizer);
            g_practiceTargetNumSets = numSets;

            // new gmPracticeTargetSet[numSets]; 0xFFFFFFFF bytes when the size overflows.
            const uint32_t header = offsetof(gmPracticeTargetSetBlock, m_sets);
            uint32_t count = static_cast<uint32_t>(numSets);
            uint32_t bytes = 0xFFFFFFFFu;
            if (count <= (0xFFFFFFFFu - header) / sizeof(gmPracticeTargetSet)) {
                bytes = header + count * static_cast<uint32_t>(sizeof(gmPracticeTargetSet));
            }
            gmPracticeTargetSetBlock* block = static_cast<gmPracticeTargetSetBlock*>(xe_EC88(bytes));
            gmPracticeTargetSet* sets;
            if (block != nullptr) {
                block->m_count = numSets;
                gmPracticeTargetSet* set = block->m_sets;
                for (int32_t i = numSets - 1; i >= 0; --i) {
                    set->m_numTargets = 0;
                    set->m_targets = nullptr;
                    ++set;
                }
                sets = block->m_sets;
            } else {
                sets = nullptr;
            }
            m_sets = sets;

            if (fiTokenizer_CheckToken(&tokenizer, "TargetDefaultColor", true)) {
                g_practiceTargetDefaultColor = ReadColor(&tokenizer);
            }
            if (fiTokenizer_CheckToken(&tokenizer, "TargetHitColor", true)) {
                g_practiceTargetHitColor = ReadColor(&tokenizer);
            }

            for (int32_t i = 0; i < g_practiceTargetNumSets; ++i) {
                if (!fiTokenizer_CheckToken(&tokenizer, "Set", true)) {
                    continue;
                }
                char token[0x40];
                token[0] = 0;
                fiTokenizer_GetToken(&tokenizer, token, 0x40);
                gmPracticeTargetSet_Load(&m_sets[i], &tokenizer);
                token[0] = 0;
                fiTokenizer_GetToken(&tokenizer, token, 0x40);
                if (maxTargets < m_sets[i].m_numTargets) {
                    maxTargets = m_sets[i].m_numTargets;
                }
            }
        }
        fiStream_Close(stream);
    }

    gmPracticeTargetWordArray_Init(m_wordArray, maxTargets, false, true);

    g_fiAssetManager.m_folderDepth--;
    fiAssetManager_PushFolder(&g_fiAssetManager, "$/fx/tex");
    g_fiAssetManager.m_folderDepth--;
}

struct pongDrawBucket;
extern pongDrawBucket* g_drawBucket;  // @ 0x826064F4
void pongDrawBucket_AddEntry(pongDrawBucket* bucket, void* renderable, uint32_t bucketMask);  // @ 0x822278D8

/**
 * gmPracticeTarget::AddToDrawBucket  [slot 2] @ 0x82113448 | size: 0x48
 *
 * While both draw flags are set, resets the renderable's two per-draw fields
 * and adds it to layer 2 (mask 4) of the draw bucket.
 */
void gmPracticeTarget::AddToDrawBucket() {
    if (m_visible == 0) {
        return;
    }
    if (m_drawEnabled == 0) {
        return;
    }
    m_renderable.field_08 = 0.0f;  // @ 0x8202D110
    m_renderable.field_0C = 0;
    pongDrawBucket_AddEntry(g_drawBucket, &m_renderable, 4);
}

// ═════════════════════════════════════════════════════════════════════════════
// gdaiMeterLogic / gdaiComeBackLogic — AI nodes from shots.xml
//
// gdaiMeterLogic slot 20 (0x821E91C0) is lifted in gd_data.cpp as
// gdaiMeterLogic::ValidateTypeId; that one matches the asm.
// ═════════════════════════════════════════════════════════════════════════════

namespace rage { struct xmlNodeStructFloat; }
extern rage::xmlNodeStructFloat g_xmlNodeStructFloat;  // @ 0x825CAF94 (vtable 0x8203AA74)
extern "C" void RegisterSerializationField(void* obj, const char* name, void* fieldPtr,
                                           void* typeDesc, int flags);  // @ 0x821A8F58

// gdaiMeterLogic fields registered by slot 21.
struct gdaiMeterLogicView {
    uint8_t _pad00[0x10];
    float   m_awareness;         // +0x10  "Awareness"
    float   m_chargeMeter;       // +0x14  "ChargeMeter"
    float   m_conserveMeter;     // +0x18  "ConserveMeter"
    float   m_doFocusShot;       // +0x1C  "DoFocusShot"
    float   m_learningModifier;  // +0x20  "LearningModifier"
};

/**
 * gdaiMeterLogic::RegisterSerializationFields  [slot 21] @ 0x821E92B0 | size: 0xC0
 *
 * Registers its five float members with rage::xmlNodeStructFloat.
 */
void gdaiMeterLogic_RegisterSerializationFields(void* self) {
    gdaiMeterLogicView* logic = static_cast<gdaiMeterLogicView*>(self);
    void* floatType = &g_xmlNodeStructFloat;
    RegisterSerializationField(self, "Awareness", &logic->m_awareness, floatType, 0);
    RegisterSerializationField(self, "ChargeMeter", &logic->m_chargeMeter, floatType, 0);
    RegisterSerializationField(self, "ConserveMeter", &logic->m_conserveMeter, floatType, 0);
    RegisterSerializationField(self, "DoFocusShot", &logic->m_doFocusShot, floatType, 0);
    RegisterSerializationField(self, "LearningModifier", &logic->m_learningModifier, floatType, 0);
}

// A child node of gdaiComeBackLogic (siblings linked through +0x08).
struct gdaiNode {
    void**    vtable;     // +0x00  slot 19 = name, slot 20 = IsA(typeId)
    uint8_t   _pad04[4];
    gdaiNode* m_next;     // +0x08
    uint8_t   _pad0C[0x10];
    int32_t   m_index;    // +0x1C  position in the list it was sorted into
};

// atArray<gdaiNode*>: data, count, capacity.
struct gdaiNodeArray {
    gdaiNode** m_data;      // +0x00
    uint16_t   m_count;     // +0x04
    uint16_t   m_capacity;  // +0x06
};

struct gdaiComeBackLogicView {
    uint8_t       _pad00[0x0C];
    gdaiNode*     m_firstChild;  // +0x0C
    gdaiNodeArray m_leads;       // +0x10  children that are gdaiLead
    gdaiNodeArray m_deficits;    // +0x18  children that are gdaiDeficit
};

// Each class's type id is a word holding its own address; slot 20 compares it.
extern void* g_gdaiDeficitTypeId;  // @ 0x825C60CC
extern void* g_gdaiLeadTypeId;     // @ 0x825C60D0
extern void nop_8240E6D0(const char* format, ...);       // @ 0x8240E6D0, debug log (empty)
extern void game_DB80(gdaiNodeArray* array, uint32_t capacity);  // @ 0x821EDB80, atArray::Reserve

static bool gdaiNode_IsA(gdaiNode* node, void* typeId) {
    return VirtualSlot<uint8_t (*)(gdaiNode*, void*)>(node, 20)(node, typeId) != 0;
}

static void ReserveOrClear(gdaiNodeArray* array, uint32_t count) {
    if (count != 0) {
        game_DB80(array, count);
    } else {
        array->m_data = nullptr;
        array->m_capacity = 0;
    }
}

/**
 * gdaiComeBackLogic::SplitLeadAndDeficit  [slot 3] @ 0x821EA1B8 | size: 0x1B0
 *
 * Counts the children that are gdaiDeficit or gdaiLead (logging any other as
 * "unknown node type found in shots.xml: %s"), sizes the two arrays, then
 * appends each child to its array and stores its index there in the child.
 */
void gdaiComeBackLogic_SplitLeadAndDeficit(void* self) {
    gdaiComeBackLogicView* logic = static_cast<gdaiComeBackLogicView*>(self);
    uint32_t numDeficits = 0;
    uint32_t numLeads = 0;

    for (gdaiNode* node = logic->m_firstChild; node != nullptr; node = node->m_next) {
        if (gdaiNode_IsA(node, g_gdaiDeficitTypeId)) {
            numDeficits++;
        } else if (gdaiNode_IsA(node, g_gdaiLeadTypeId)) {
            numLeads++;
        } else {
            const char* name = VirtualSlot<const char* (*)(gdaiNode*)>(node, 19)(node);
            nop_8240E6D0("unknown node type found in shots.xml: %s", name);
        }
    }

    ReserveOrClear(&logic->m_leads, numLeads);
    ReserveOrClear(&logic->m_deficits, numDeficits);

    int32_t leadIndex = 0;
    int32_t deficitIndex = 0;
    for (gdaiNode* node = logic->m_firstChild; node != nullptr; node = node->m_next) {
        if (gdaiNode_IsA(node, g_gdaiDeficitTypeId)) {
            gdaiNodeArray* list = &logic->m_deficits;
            list->m_data[list->m_count++] = node;
            node->m_index = deficitIndex++;
        } else if (gdaiNode_IsA(node, g_gdaiLeadTypeId)) {
            gdaiNodeArray* list = &logic->m_leads;
            list->m_data[list->m_count++] = node;
            node->m_index = leadIndex++;
        }
    }
}

// ═════════════════════════════════════════════════════════════════════════════
// game_3860 @ 0x821D3860 | size: 0x84
// ═════════════════════════════════════════════════════════════════════════════

// The 16-byte callback shape pong_player.cpp documents (rage::datCallback-like).
typedef void (*pongCallbackFn)();
struct pongCallback {
    void*          target;    // +0x00
    pongCallbackFn function;  // +0x04
    void*          data;      // +0x08
    int32_t        kind;      // +0x0C  1: function(target); 4: function(target, int* answer)
};

// The object at gameState+0x14: 0x821D7750 logs
// "%s called BallPredictData::Reset() %s" and clears it.
struct BallPredictData {
    uint8_t      _pad00[0x27E8];
    pongCallback m_callback;  // +0x27E8
};

struct pongGameStatePredictView {
    uint8_t          _pad00[0x14];
    BallPredictData* m_pBallPredict;  // +0x14
};

// @ 0x821D7750 (game_7750) — BallPredictData::Reset(caller name).
extern void BallPredictData_Reset(BallPredictData* data, const char* caller);

/**
 * game_3860 @ 0x821D3860 | size: 0x84
 *
 * Resets the ball prediction on behalf of `name`, then points its callback at
 * the empty logger with gameState as target (kind 4). `kind` is never read.
 */
void game_3860(void* gameState, int /*kind*/, const char* name) {
    pongGameStatePredictView* state = static_cast<pongGameStatePredictView*>(gameState);
    BallPredictData_Reset(state->m_pBallPredict, name);

    pongCallback callback;
    callback.target = gameState;
    callback.function = reinterpret_cast<pongCallbackFn>(&nop_8240E6D0);  // the empty logger
    callback.data = nullptr;
    callback.kind = 4;
    state->m_pBallPredict->m_callback = callback;
}
