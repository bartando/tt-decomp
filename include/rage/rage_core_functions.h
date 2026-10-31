/**
 * rage_core_functions.h — RAGE Engine Core Function Declarations
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 * 
 * This header provides clean, human-readable declarations for core RAGE
 * engine functions that were previously identified by hex addresses.
 */

#pragma once

#include <stdint.h>
#include <stddef.h>
#include "rage/fi_stream.hpp"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// String Utilities
// ============================================================================

/**
 * rage_strcat_bounded @ 0x820F0888 | size: 0x7C
 * 
 * Safe string concatenation with length limit.
 * Appends src to dst, respecting maxLen total buffer size.
 * Always null-terminates the result.
 * 
 * Parameters:
 *   dst    - Destination buffer (modified in place)
 *   src    - Source string to append
 *   maxLen - Maximum total length of dst buffer
 */
void rage_strcat_bounded(char* dst, const char* src, int32_t maxLen);

/**
 * rage_stricmp @ 0x82186358 | size: 0xC0
 * 
 * Case-insensitive string comparison.
 * 
 * Returns:
 *   < 0 if s1 < s2
 *   = 0 if s1 == s2
 *   > 0 if s1 > s2
 */
int rage_stricmp(const char* s1, const char* s2);

/**
 * rage_GetExecutableName @ 0x82186628 | size: 0x68
 * 
 * Get the executable name or path.
 * 
 * Returns:
 *   Pointer to executable name string
 */
const char* rage_GetExecutableName(void);

// ============================================================================
// File Stream Buffer Management
// ============================================================================

// ============================================================================
// Graphics Device Management
// ============================================================================

/**
 * grcDevice_ConfigureRenderTargets @ 0x82366530 | size: 0x1BC
 * 
 * Configure render targets for graphics device.
 * Sets up framebuffers and render target attachments.
 * 
 * Parameters:
 *   pDevice - Graphics device object
 *   pConfig - Render target configuration
 * 
 * Returns:
 *   0 on success, non-zero on failure
 */
int grcDevice_ConfigureRenderTargets(void* pDevice, void* pConfig);

/**
 * grcDevice_CleanupRenderTargets @ 0x823666F0 | size: 0x94
 * 
 * Cleanup render targets for graphics device.
 * Releases framebuffers and render target resources.
 */
void grcDevice_CleanupRenderTargets(void* pDevice);

/**
 * grcDevice_SetupRenderFiber @ 0x8235AD98 | size: 0x88
 * 
 * Setup render fiber for graphics device.
 * Initializes rendering fiber/thread context.
 */
void grcDevice_SetupRenderFiber(void* pDevice);

/**
 * grcDevice_FinalizeRenderSetup @ 0x820F0F248 | size: 0xF0
 * 
 * Finalize render setup for graphics device.
 * Completes initialization of rendering subsystem.
 */
void grcDevice_FinalizeRenderSetup(void* pDevice);

/**
 * grcDevice_BeginRenderConfig @ 0x820F0F338 | size: 0xC8
 * 
 * Begin render configuration for graphics device.
 * Starts configuration phase for rendering setup.
 */
void grcDevice_BeginRenderConfig(void* pDevice);

/**
 * grcDevice_InitializeRenderConfig @ 0x820F0F400 | size: 0x48
 * 
 * Initialize render configuration for graphics device.
 * Sets up initial rendering configuration state.
 */
void grcDevice_InitializeRenderConfig(void* pDevice);

// ============================================================================
// Array Container Management
// ============================================================================

struct atArrayElement;

/**
 * atArray_Destructor @ 0x82177630 | size: 0x58
 * 
 * Destructor for atArray container.
 * Destroys all elements and frees array memory.
 * 
 * Parameters:
 *   pArray - Pointer to first element (NOT the header)
 * 
 * Returns:
 *   Pointer to freed memory block
 */
void* atArray_Destructor(void* pArray);

/**
 * atArray_Clear @ 0x821A8070 | size: 0xA4
 * 
 * Clear all elements from atArray.
 * Destroys elements but keeps array allocation.
 */
void atArray_Clear(void* pArray);

/**
 * atArrayElement_Destroy @ 0x821A8118 | size: 0x68
 * 
 * Destroy single atArray element.
 * Recursively destroys element and its children.
 */
void atArrayElement_Destroy(struct atArrayElement* pElement);

// ============================================================================
// Animation System
// ============================================================================

/**
 * pcrAnimBlender_Initialize @ 0x820C1188 | size: 0x730
 * 
 * Initialize PCR animation blender system.
 * Sets up animation blending subsystem.
 */
void pcrAnimBlender_Initialize(void* pBlender);

// ============================================================================
// Thread Management
// ============================================================================

/**
 * rage_RegisterThread @ 0x82187FD0 | size: 0x1C0
 * 
 * Register thread with RAGE scheduler.
 * Creates and registers a new thread with the engine.
 * 
 * Parameters:
 *   func      - Thread entry function
 *   param     - Startup parameter
 *   stackSize - Stack size in bytes
 *   priority  - Base priority delta
 *   name      - Thread name format string
 *   suspended - Start suspended flag (1 = suspended)
 *   affinity  - Processor affinity mask
 * 
 * Returns:
 *   Thread handle, or 0 on failure
 */
uint32_t rage_RegisterThread(void* func, void* param, uint32_t stackSize,
                             uint32_t priority, void* name,
                             uint32_t suspended, uint32_t affinity);

/**
 * rage_ThreadPool_Cleanup @ 0x82186878 | size: 0x80
 * 
 * Cleanup thread pool resources.
 * Shuts down and releases thread pool.
 */
void rage_ThreadPool_Cleanup(void* pThreadPool);

// ============================================================================
// Object Factory
// ============================================================================

// ============================================================================
// Resource Loading
// ============================================================================

/**
 * rage_LoadTexture @ 0x820F9380 | size: 0x16C
 * 
 * Load texture from file.
 * Loads and initializes a texture resource.
 * 
 * Returns:
 *   Pointer to loaded texture, or NULL on failure
 */
void* rage_LoadTexture(const char* path);

// ============================================================================
// Network/Socket
// ============================================================================

/**
 * rage_WSockErrorHandler @ 0x82481B08 | size: 0x8
 * 
 * Windows Socket error handler.
 * Handles Winsock initialization errors.
 */
void rage_WSockErrorHandler(void);

#ifdef __cplusplus
}
#endif
