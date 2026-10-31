from specs._fi_stream_open_inputs import pool_input as inputs, POOL_CALLS as CALLS
FUNCTION = "fiStreamBuf_Attach"
ADDRESS = 0x822e3378
SOURCE = "src/rage/io/fiStreamOpen.cpp"
TRIALS = 1000
EXTERNS = {"g_fiStreamBuffers": 0x825F5E50}
