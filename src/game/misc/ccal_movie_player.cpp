/**
 * ccal_movie_player.cpp — small movie player helpers
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * pong_misc.cpp calls these through __asm__ labels with their map names.
 */

#include <cstdint>

// @ 0x8235EAC0 — rage_EAC0: AddRef on the video callback object; the
// reference count is at +0x0C. Returns the new count.
extern "C" uint32_t rage_EAC0(void* obj) {
    uint32_t* count = reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(obj) + 0x0C);
    return ++*count;
}

// @ 0x8235EB70 — CCalMoviePlayer_EB70: after an eieio, clears the fiber flag
// at +0x2888.
extern "C" void CCalMoviePlayer_EB70(void* player) {
    __atomic_thread_fence(__ATOMIC_SEQ_CST);
    *reinterpret_cast<uint32_t*>(static_cast<uint8_t*>(player) + 0x2888) = 0;
}
