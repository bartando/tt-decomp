#pragma once
#include <stdint.h>

extern "C" {
void CCalRingBuffer_CommitWrite(void* ring) __asm__("_CCalMoviePlayer_DCC8"); // @ 0x8248DCC8
void CCalRingBuffer_ReleaseRead(void* ring) __asm__("_CCalMoviePlayer_DD30"); // @ 0x8248DD30
uint32_t CCalMoviePlayer_AcquireFiberContext(void* object) __asm__("_CCalMoviePlayer_EB30"); // @ 0x8235EB30
int32_t CCalMoviePlayer_EC88_p33(void* object); // @ 0x8248EC88
int32_t CCalMoviePlayer_ECB8_p33(void* object); // @ 0x8248ECB8
int32_t CCalMoviePlayer_ECE8_p33(void* object); // @ 0x8248ECE8
int32_t CCalMoviePlayer_ED18_p33(void* object); // @ 0x8248ED18
}
