// GPU/D3D debug name strings extracted from the Xbox 360 binary.
//
// These are Xenos GPU register/block identifiers and D3D hang-diagnostic
// messages referenced by the graphics subsystem when reporting GPU faults
// or dumping register state for postmortem debugging.
//
// Xenos block glossary:
//   RBBM   - Register Block-Bus Manager
//   VGT    - Vertex Grouper / Tessellator
//   PA_SU  - Primitive Assembler, Setup unit
//   PA_SC  - Primitive Assembler, Scan converter
//   CP     - Command Processor
//   RB     - Render Backend

namespace rage {

// 0x82065F26
extern const char k_str_for_postmortem_debugging[] =
    "for postmortem debugging.\n"
    "\n";

// 0x82065FA8 - Vertex Grouper/Tessellator debug block
extern const char k_str_vgt_debug[] = "VGT_DEBUG";

// 0x82065FB4 - Primitive Assembler Setup debug block
extern const char k_str_pa_su_debug[] = "PA_SU_DEBUG";

// 0x82065FC0 - Primitive Assembler Scan debug block
extern const char k_str_pa_sc_debug[] = "PA_SC_DEBUG";

// 0x82065FCC - Register Block-Bus Manager debug block
extern const char k_str_rbbm_debug[] = "RBBM DEBUG";

// 0x82065FD8 - Command Processor debug block (label form)
extern const char k_str_cp_debug_label[] = "CP DEBUG";

// 0x8206602C - Render Backend debug register 0
extern const char k_str_rb_debug_0[] = "RB_DEBUG_0";

// 0x82066150 - Command Processor debug register (identifier form)
extern const char k_str_cp_debug[] = "CP_DEBUG";

// 0x82066510
extern const char k_str_d3d_hang_try_instrumented[] =
    "ERR[D3D]: Try reproducing the hang with the debug or instrumented\n"
    "          versions of D3D (D3D9D.LIB or D3D9I.LIB) to capture a\n"
    "          crash-dump PIX file that can be sent to Xbox developer\n"
    "          support.\n"
    "\n";

// 0x820665E8
extern const char k_str_d3d_hang_breaking_into_debugger[] =
    "Breaking into the debugger.  The GPU is hung and can't be recovered\n"
    "without doing a cold boot.\n";

}  // namespace rage

// @ 0x820661FC
extern const char k_str_gpu_appears_to_be_hung[] = "The GPU appears to be hung!  Specifically: ";

// @ 0x8206622C
extern const char k_str_cpu_synchronization[] = "CPU Synchronization";

// @ 0x8206626C
extern const char k_str_ltcg[] = "LTCG";

// @ 0x82066274
extern const char k_str_d3d_version_banner[] = "\nD3D version is %i.%i %s, kernel is %i, frame is %i.\n\n";

// @ 0x82066450
extern const char k_str_hang_unknown_state[] = "The GPU state doesn't match any known hangs.  Please send a repro\nscenario to xboxds@xbox.com so that we can supply a workaround.\n\n";
