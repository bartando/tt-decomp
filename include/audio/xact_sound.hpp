#pragma once

// Descriptive names for the statically linked XACT runtime's workers.
void xactSound_Update(void* sound); // @ 0x82455148
void xactWave_Update(void* wave); // @ 0x8244AAE8

void xactWave_Finalize(void* wave); // @ 0x8244A670
