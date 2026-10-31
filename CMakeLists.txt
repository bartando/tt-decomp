cmake_minimum_required(VERSION 3.10)
project(RockstarTableTennis VERSION 1.0.0 LANGUAGES C CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Compiler-specific options
if(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /Od /Zi")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /O2")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
    set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0")
    set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")
endif()

# Find required packages
if(TT_WINDOWS_X86)
    set(SDL2_NO_MWINDOWS ON)
endif()
find_package(SDL2 REQUIRED)
if(TT_WINDOWS_X86)
    # We use the host CRT's console entry, not SDL's WinMain adapter.
    set(SDL2_LIBRARIES SDL2::SDL2)
endif()
find_package(OpenGL REQUIRED)
if(TT_WINDOWS_X86 AND EXISTS "${GLEW_ROOT}/src/glew.c")
    add_library(tt_glew STATIC "${GLEW_ROOT}/src/glew.c")
    target_include_directories(tt_glew PUBLIC "${GLEW_ROOT}/include")
    target_compile_definitions(tt_glew PUBLIC GLEW_STATIC)
    add_library(GLEW::GLEW ALIAS tt_glew)
else()
    find_package(GLEW REQUIRED)
endif()

# Include directories
include_directories(${SDL2_INCLUDE_DIRS})
include_directories(${OPENGL_INCLUDE_DIRS})
include_directories(${GLEW_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Add definitions
add_definitions(${SDL2_DEFINITIONS})
add_definitions(-DTT_PLATFORM_PC=1)

# Source files
set(SOURCES
    # CRT layer
    src/crt/crt_init.c
    src/crt/ctrlfp.cpp
    src/crt/fp_helpers.cpp
    src/crt/entry.c
    src/crt/exit.c
    src/crt/fmod.cpp
    src/crt/heap.c
    src/crt/host_format.cpp
    src/crt/memory.c
    src/crt/rtti.cpp
    src/crt/startup.c
    src/crt/version.c
    src/crt/string.c
    src/crt/xe_thread.c
    src/crt/xe_tls.c
    src/globals.c

    # XAM (Xbox Application Model)
    src/xam/audio.c
    src/xam/input.c
    src/platform/time_stamp.cpp
    src/xam/time_stamp.cpp
    src/platform/host_imports.cpp
    src/platform/audio_frame.cpp
    src/platform/host_xma.cpp
    src/platform/host_memory.cpp
    src/xam/kernel_common.c
    src/xam/thread_sync.cpp
    src/xam/kernel_shims.c
    src/xam/network.c
    src/xam/static_init.c
    src/xam/video.c
    src/xam/voice.c
    src/xam/xam_shims.c
    src/xam/xam_stubs.c
    src/xam/xam_utils.c
    src/xam/xe_buffers.c
    src/xam/xe_graphics.c
    
    # RAGE engine
    src/rage/animation/rage_anim.cpp
    src/rage/audio/audio_control_wrappers.cpp
    src/rage/audio/aud_channel_mixer.cpp
    src/rage/audio/aud_instance_update.cpp
    src/rage/audio/rage_audio.cpp
    src/rage/audio/xma_source.cpp
    src/rage/audio/ld_xaudio_data.cpp
    src/rage/audio/xact_fade.cpp
    src/rage/audio/xact_sound.cpp
    src/rage/audio/xaudio_effect_buffer.cpp
    src/rage/audio/xaudio_effect.cpp
    src/rage/audio/xaudio_resampler.cpp
    src/rage/core/fsmMachine.cpp
    src/rage/core/app_init.c
    src/rage/core/game_loop.c
    src/rage/core/hsm.cpp
    src/rage/core/indexed_registry.cpp
    src/rage/core/io_input.cpp
    src/rage/core/main.c
    src/rage/rage_grm.cpp
    src/rage/data/rage_dat.cpp
    src/rage/data/rage_xml.cpp
    src/rage/data/at_types.cpp
    src/rage/data/par_xml_types.cpp
    src/rage/memory/rage_memory.cpp
    src/rage/memory/singleton_array.cpp
    src/rage/memory/sysMemSimpleAllocator.cpp
    src/rage/data/localized_text.cpp
    src/rage/data/localized_text_data.cpp
    src/rage/data/parameter_node.cpp
    src/rage/io/rage_par.cpp
    src/rage/io/rage_stream_manager.cpp
    src/rage/io/fiDevice.cpp
    src/rage/io/fiAsciiTokenizer.cpp
    src/rage/io/fiStreamBuf.cpp
    src/rage/render_loop.c
    src/rage/scene_render.c
    src/rage/network/session_events.cpp
    src/rage/network/snSessionStates.cpp
    src/rage/core/subsystem_init.c
    src/rage/swf.cpp
    src/rage/swf_image_data.cpp
    src/rage/hud_page_group.cpp
    src/rage/swf_page_group.cpp
    src/rage/swf_vm.cpp
    src/rage/swf_value_helpers.cpp
    src/rage/swf_text.cpp
    src/rage/swf_bounds.cpp
    src/rage/swf_action_copy.cpp
    src/rage/swf_paint.cpp
    src/rage/localized_font.cpp
    src/rage/localized_font_lifecycle.cpp
    src/rage/localized_font_effect.cpp
    src/rage/swf_clip_events.cpp
    src/rage/core/timer.cpp
    src/rage/core/rage_core_utils.cpp
    src/rage/misc/rage_cm.cpp
    src/rage/animation/cm_shims.cpp
    src/rage/misc/rage_globals.cpp
    src/rage/misc/rage_misc.cpp
    src/rage/rage_engine_dtors.cpp

    # Game logic
    src/game/char_view/char_view.cpp
    src/game/char_view/pong_attract_state_shims.cpp
    src/game/cutscene/gd_cutscene_strings.cpp
    src/game/cutscene/pong_cutscene.cpp
    src/game/data/gd_data.cpp
    src/game/template_registry.cpp
    src/game/game_message.cpp
    src/game/game_message_data.cpp
    src/game/data/gd_data_strings.cpp
    src/game/data/gd_logic_strings.cpp
    src/game/data/gd_vib_event.cpp
    src/game/debug_strings.cpp
    src/game/dialog_strings.cpp
    src/game/pong_logos_strings.cpp
    src/game/pong_strings.cpp
    src/game/save/mc_memcard.cpp
    src/game/audio/pong_audio.cpp
    src/game/audio/pong_audio_effects.cpp
    src/game/ball/pong_ball.cpp
    src/game/ball/ball_splash.cpp
    src/game/ball/ball_audio_emitters.cpp
    src/game/ball/ball_audio_envelope.cpp
    src/game/ball/ball_audio_impact.cpp
    src/game/ball/ball_flight.cpp
    src/game/ball/ball_shot_initialize.cpp
    src/game/ball/ball_shot.cpp
    src/game/ball/ball_shot_solve.cpp
    src/game/ball/ball_shot_trajectory.cpp
    src/game/ball/ball_shot_simulation.cpp
    src/game/ball/ball_process_hit.cpp
    src/game/ball/ball_prediction_copy_locked.cpp
    src/game/ball/ball_playback.cpp
    src/game/ball/ball_visual_spin.cpp
    src/game/ball/ball_prediction_stream.cpp
    src/game/ball/ball_prediction_step.cpp
    src/game/ball/ball_prediction_queries.cpp
    src/game/ball/ball_prediction_hit_ids.cpp
    src/game/ball/ball_prediction_hit_queries.cpp
    src/game/ball/ball_prediction_outcome_helpers.cpp
    src/game/ball/ball_replay.cpp
    src/game/ball/ball_replay_update.cpp
    src/game/ball/ball_prediction_postprocess.cpp
    src/game/ball/ball_prediction_quaternion.cpp
    src/game/camera/pong_camera.cpp
    src/game/camera/pong_camera_helpers.cpp
    src/game/camera/camera_transition_queries.cpp
    src/game/camera/cm_cam_actions.cpp
    src/game/camera/dcam_polar_cam.cpp
    src/game/creature/pong_creature.cpp
    src/game/creature/mover_input_speed.cpp
    src/game/creature/creature_pose.cpp
    src/game/drill/pong_drill.cpp
    src/game/input/button_edges.cpp
    src/game/input/analog_axis.cpp
    src/game/input/input_sequence.cpp
    src/game/misc/cm_operators.cpp
    src/game/misc/movie_worker_helpers.cpp
    src/game/misc/pong_misc.cpp
    src/game/network/pong_network.cpp
    src/game/network/pong_network_classes.cpp
    src/game/network/pong_network_io.cpp
    src/game/network/network_timestamp.cpp
    src/game/network/round_robin_state.cpp
    src/game/network/score_payload.cpp
    src/game/network/network_context.cpp
    src/game/network/msg_msg_sink.cpp
    src/game/network/xonline_strings.cpp
    src/game/player/pong_player.cpp
    src/game/player/pong_player_swing.cpp
    src/game/player/player_swing_phase.cpp
    src/game/player/player_shot_interpolation.cpp
    src/game/player/player_move_mode.cpp
    src/game/player/creature_move_mode.cpp
    src/game/player/player_action_groups.cpp
    src/game/player/player_control_queries.cpp
    src/game/player/player_control_queries_data.cpp
    src/game/player/player_mode_data.cpp
    src/game/player/player_mode_animation.cpp
    src/game/player/player_animation_reset_helpers.cpp
    src/game/player/player_auxiliary_pose.cpp
    src/game/player/player_auxiliary_animation_helpers.cpp
    src/game/player/player_animation_clock.cpp
    src/game/player/player_swing_pose_helpers.cpp
    src/game/player/player_apply_movement_target.cpp
    src/game/player/player_pose_easing.cpp
    src/game/player/player_serve_callbacks.cpp
    src/game/player/player_serve_hit_point.cpp
    src/game/player/player_serve_hit_point_data.cpp
    src/game/player/player_shot_target_setup.cpp
    src/game/player/player_spin_helpers.cpp
    src/game/player/camera_node_cast.cpp
    src/game/player/player_camera_side.cpp
    src/game/player/player_camera_side_data.cpp
    src/game/player/player_animation_state.cpp
    src/game/player/pong_gameplay_queries.cpp
    src/game/pong_render.cpp
    src/game/match/hsm_log_strings.cpp
    src/game/match/pong_match.cpp
    src/game/match/match_ai_array.cpp
    src/game/match/replay_state_publish.cpp
    src/game/match/lvl_table.cpp
    src/game/match/pong_states.cpp
    src/game/match/match_rtti_strings.cpp
    src/rage/rtti_class_strings.cpp
    
    # Animation
    src/anim/anim_blender_state.cpp
    src/anim/root_motion_blend.cpp
    src/anim/clip_mover_displacement.cpp
    src/anim/clip_mover_delta.cpp
    src/anim/bone_matrix_lookup.cpp
    src/anim/bone_transform_lookup.cpp
    src/anim/motion_lookup_data.cpp
    src/anim/pcr_anim_blenders.cpp
    src/anim/look_at_controller.cpp
    src/anim/locomotion.cpp
    src/anim/angle_helpers.cpp
    src/anim/animation_timing.cpp

    # Physics
    src/physics/collider_velocity.cpp
    src/physics/ph_float_property.cpp
    src/physics/ph_physics.cpp
    src/physics/bound_lookup.cpp
    src/physics/articulated_constraints.cpp
    src/physics/ph_update_object.cpp
    
    # Graphics
    src/graphics/fx_crowd.cpp
    src/graphics/tri_strip_list.cpp
    src/graphics/grc_debug_strings.cpp
    src/graphics/grc_gpu_hang.cpp
    src/graphics/grc_cache.cpp
    src/graphics/grc_state_helpers.cpp
    src/graphics/grc_command_stream.cpp
    src/graphics/grc_device.cpp
    src/graphics/grc_gpu_resources.cpp
    src/graphics/fx_billboard.cpp
    src/graphics/grc_vertex_buffer.cpp
    src/graphics/grc_render.cpp
    src/graphics/texture_reference.cpp
    src/graphics/grc_viewport_cull.cpp
    
    # Scene Graph
    src/scene/sg_node.cpp
    src/scene/sg_drawable.cpp
    src/scene/sg_physical.cpp
    src/scene/sg_scene_graph.cpp

    # Definitions the link was missing: data from the image, small lifts,
    # and bridges between spellings of one symbol
    src/game/ball/ball_data.cpp
    src/game/ball/ball_predict.cpp
    src/game/ld_game_data.cpp
    src/game/camera/camera_data.cpp
    src/game/camera/ld_cam_data.cpp
    src/game/char_view/char_view_data.cpp
    src/game/creature/creature_data.cpp
    src/game/match/match_data.cpp
    src/game/misc/misc_data.cpp
    src/game/network/net_data.cpp
    src/game/network/image_data.cpp
    src/game/network/ld_net_data.cpp
    src/game/player/player_data.cpp
    src/graphics/grc_data.cpp
    src/graphics/image_data.cpp
    src/physics/ph_data.cpp
    src/physics/ld_ph_data.cpp
    src/rage/animation/anim_data.cpp
    src/rage/animation/float_channel_vtables.cpp
    src/rage/audio/aud_data.cpp
    src/rage/audio/image_data.cpp
    src/rage/network/sn_data.cpp
    src/rage/rage_data.cpp
    src/rage/time_state_data.cpp
    src/rage/ld_rage_data.cpp
    src/xam/xam_data.cpp
    src/link/linkage_bridges.cpp
    src/rage/net/dat_bit_buffer.cpp
    src/rage/core/debug_print_nops.cpp
    src/rage/data/dat_parser_fields.cpp
    src/rage/data/dat_resource_fixup.cpp
    src/rage/network/sn_event.cpp
    src/xam/kernel_import_thunks.c
    src/rage/math/float_approach.cpp
    src/rage/math/ph_math.cpp
    src/rage/math/polygon_clip.cpp
    src/rage/math/swf_matrix.cpp
    src/rage/math/mat44.cpp
    src/rage/math/mat33.cpp
    src/rage/math/mat33_orthonormalize.cpp
    src/rage/math/mat34_transform.cpp
    src/game/player/player_state_queries.cpp
    src/game/misc/ccal_ring_buffer.cpp
    src/game/misc/ccal_movie_player.cpp
    src/game/network/xact_sink_forwards.cpp
)

# Create executable
if(WIN32)
    list(APPEND SOURCES src/xam/kernel_win32.c src/xam/kernel_critical_section.c src/platform/win32.c)
else()
    list(APPEND SOURCES src/xam/kernel.c src/platform/host_sync.cpp src/platform/posix_sync.c)
endif()
add_executable(${PROJECT_NAME} ${SOURCES})

if(TT_WINDOWS_X86)
    if(NOT CMAKE_SIZEOF_VOID_P EQUAL 4)
        message(FATAL_ERROR "TT_WINDOWS_X86 requires a 32-bit compiler and dependencies")
    endif()
    target_compile_definitions(${PROJECT_NAME} PRIVATE TT_WINDOWS_X86=1 SDL_MAIN_HANDLED)
    target_compile_options(${PROJECT_NAME} PRIVATE -include "${CMAKE_CURRENT_SOURCE_DIR}/include/platform/layout.h")
    # Keep the full missing-lift inventory in one link attempt.
    target_link_options(${PROJECT_NAME} PRIVATE -Wl,--error-limit=0)
    # Homebrew's mingw libstdc++ / SJLJ runtime uses winpthreads internally.
    # Keep that runtime static so the offline Windows PC needs no extra DLL.
    find_library(TT_WINPTHREAD_STATIC NAMES libwinpthread.a winpthread
        HINTS ${CMAKE_CXX_IMPLICIT_LINK_DIRECTORIES} "${TT_MINGW_ROOT}/i686-w64-mingw32/lib"
        NO_CMAKE_FIND_ROOT_PATH REQUIRED)
    target_link_libraries(${PROJECT_NAME} "${TT_WINPTHREAD_STATIC}")
endif()

# Link libraries
target_link_libraries(${PROJECT_NAME}
    ${SDL2_LIBRARIES}
    ${OPENGL_LIBRARIES}
    GLEW::GLEW
)

# Platform-specific linking
if(WIN32)
    # Windows-specific libraries
    target_link_libraries(${PROJECT_NAME}
        opengl32
        ws2_32
        ntdll
    )
elseif(APPLE)
    target_link_libraries(${PROJECT_NAME} pthread)
    # macOS-specific libraries
    find_library(COCOA_LIBRARY Cocoa)
    find_library(IOKIT_LIBRARY IOKit)
    find_library(COREVIDEO_LIBRARY CoreVideo)
    target_link_libraries(${PROJECT_NAME}
        ${COCOA_LIBRARY}
        ${IOKIT_LIBRARY}
        ${COREVIDEO_LIBRARY}
    )
elseif(UNIX)
    target_link_libraries(${PROJECT_NAME} pthread)
    # Linux-specific libraries
    target_link_libraries(${PROJECT_NAME}
        GL
        dl
        X11
    )
endif()

# Set output directory
set_target_properties(${PROJECT_NAME} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

# Copy SDL2 DLLs on Windows
if(WIN32 AND TARGET SDL2::SDL2)
    add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:SDL2::SDL2>
        $<TARGET_FILE_DIR:${PROJECT_NAME}>
    )
endif()

# Install rules
option(TT_BUILD_PLATFORM_TESTS "Build standalone host synchronization tests" OFF)
if(TT_BUILD_PLATFORM_TESTS)
    enable_testing()
    if(WIN32)
        add_executable(tt_platform_test tests/win32_kernel_test.c
            src/xam/kernel_win32.c src/xam/kernel_common.c src/xam/thread_sync.cpp
            src/xam/kernel_critical_section.c src/platform/win32.c
            src/platform/host_memory.cpp src/platform/host_imports.cpp)
        target_link_libraries(tt_platform_test ntdll "${TT_WINPTHREAD_STATIC}")
    else()
        add_executable(tt_platform_test tests/host_critical_section_test.c
            src/platform/host_sync.cpp src/platform/posix_sync.c)
        target_link_libraries(tt_platform_test pthread)
        add_executable(tt_host_contract_test tools/host-tests/sync.cpp
            src/xam/kernel.c src/xam/kernel_common.c src/xam/thread_sync.cpp
            src/platform/host_sync.cpp src/platform/host_memory.cpp src/platform/host_imports.cpp)
        target_compile_options(tt_host_contract_test PRIVATE -UNDEBUG)
        target_link_libraries(tt_host_contract_test pthread)
        add_test(NAME host_sdk_contracts COMMAND tt_host_contract_test)
    endif()
    add_executable(tt_timestamp_test tests/host_timestamp_test.cpp
        src/platform/time_stamp.cpp src/xam/time_stamp.cpp)
    target_compile_options(tt_timestamp_test PRIVATE -UNDEBUG)
    if(WIN32)
        target_sources(tt_timestamp_test PRIVATE src/platform/win32.c)
        target_link_libraries(tt_timestamp_test ntdll "${TT_WINPTHREAD_STATIC}")
    else()
        target_sources(tt_timestamp_test PRIVATE src/platform/posix_sync.c)
        target_link_libraries(tt_timestamp_test pthread)
    endif()
    add_test(NAME host_timestamp COMMAND tt_timestamp_test)
    add_test(NAME host_synchronization COMMAND tt_platform_test)
endif()
install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION bin
)

# Print configuration info
message(STATUS "Rockstar Presents Table Tennis - Cross-Platform Rewrite")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "SDL2 version: ${SDL2_VERSION}")
message(STATUS "OpenGL found: ${OPENGL_FOUND}")
message(STATUS "GLEW found: ${GLEW_FOUND}")
