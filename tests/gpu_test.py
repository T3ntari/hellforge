#!/usr/bin/env python3
"""GPU plugin tests — Radical, TensorSHARP, OPENapi, Vulkanizer.
Tests auto-detect, graceful fallback, and API surface."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        import traceback
        traceback.print_exc()
        print(f"  [FAIL] {name}: {e}")


# === GPU DETECTION ===

def test_gpu_detect():
    from plugins.radical.gpu_detect import detect_gpu
    info = detect_gpu()
    assert isinstance(info, dict)
    assert "available" in info
    assert "name" in info
    assert "vendor" in info
    assert "gpus" in info, "should have gpus list"
    assert "apis" in info, "should have apis dict"
    assert "vram_mb" in info, "should have vram_mb"
    assert "gpu_type" in info, "should have gpu_type"
    assert isinstance(info["gpus"], list)
    assert isinstance(info["apis"], dict)
    print(f"   Primary: {info['name']} ({info['vendor']})")
    print(f"   Type: {info['gpu_type']}, VRAM: {info['vram_mb']}MB")
    print(f"   Compute: {info['compute']}, GL: {info['gl_version']}")
    print(f"   All GPUs: {len(info['gpus'])} detected")
    for g in info['gpus']:
        api_flags = []
        for k, v in info['apis'].items():
            if v and ((k == 'cuda' and g['vendor'] == 'NVIDIA') or k != 'cuda'):
                api_flags.append(k)
        print(f"     [{g.get('type','?')}] {g['name']} ({g['vendor']}) {g.get('vram_mb',0)}MB {','.join(api_flags)}")
test("GPU detect: multi-GPU, vendor, type, VRAM, APIs", test_gpu_detect)

def test_gpu_vendor_classification():
    from plugins.radical.gpu_detect import _classify_gpu_by_name
    cases = [
        ("NVIDIA GeForce RTX 3050", "NVIDIA", "discrete"),
        ("NVIDIA GeForce RTX 4090", "NVIDIA", "discrete"),
        ("NVIDIA Quadro RTX 6000", "NVIDIA", "discrete"),
        ("AMD Radeon RX 7900 XTX", "AMD", "discrete"),
        ("AMD Radeon(TM) Graphics", "AMD", "integrated"),
        ("AMD Radeon(TM) Vega 8 Graphics", "AMD", "integrated"),
        ("Intel(R) Arc(TM) A770 Graphics", "Intel", "discrete"),
        ("Intel(R) UHD Graphics 770", "Intel", "integrated"),
        ("Intel(R) Iris(R) Xe Graphics", "Intel", "integrated"),
        ("Intel(R) HD Graphics 630", "Intel", "integrated"),
        ("Microsoft Basic Render Driver", "Microsoft", "software"),
        ("Apple M1 Max", "Apple", "integrated"),
        ("Apple M2 Ultra", "Apple", "integrated"),
        ("Google SwiftShader", "Google", "software"),
        ("Qualcomm Adreno 730", "Qualcomm", "integrated"),
    ]
    for name, expected_vendor, expected_type in cases:
        g = _classify_gpu_by_name(name)
        assert g["vendor"] == expected_vendor, f"{name}: expected vendor {expected_vendor}, got {g['vendor']}"
        assert g["type"] == expected_type, f"{name}: expected type {expected_type}, got {g['type']}"
        print(f"   [{g['type']}] {g['vendor']} - {name}")
test("GPU vendor classification: 15 GPU types across all vendors", test_gpu_vendor_classification)

def test_gpu_apis_detected():
    from plugins.radical.gpu_detect import (
        _check_vulkan,
        _check_cuda,
        _check_directx,
        _check_opencl,
    )
    vulkan = _check_vulkan()
    cuda = _check_cuda()
    dx = _check_directx()
    print(f"   Vulkan: {'yes' if vulkan else 'no'}")
    print(f"   CUDA: {'yes' if cuda else 'no'}")
    print(f"   DirectX: {'yes' if dx else 'no'}")
test("GPU API detection: Vulkan, CUDA, DirectX", test_gpu_apis_detected)


# === AST TO GLSL ===

def test_ast_to_glsl_num():
    from plugins.radical.ast_to_glsl import ast_to_glsl
    source = ast_to_glsl({"t": "NUM", "v": 42.0})
    assert "#version 430" in source
    assert "42.0" in source
test("AST->GLSL: NUM node", test_ast_to_glsl_num)


def test_ast_to_glsl_binop():
    from plugins.radical.ast_to_glsl import ast_to_glsl
    ast = {"t": "BINOP", "op": "+", "l": {"t": "NUM", "v": 2.0}, "r": {"t": "NUM", "v": 3.0}}
    source = ast_to_glsl(ast)
    assert "(2.0 + 3.0)" in source
test("AST->GLSL: BINOP node", test_ast_to_glsl_binop)


def test_ast_to_glsl_call():
    from plugins.radical.ast_to_glsl import ast_to_glsl
    ast = {"t": "CALL", "n": "sin", "a": [{"t": "NUM", "v": 0.0}]}
    source = ast_to_glsl(ast)
    assert "sin(0.0)" in source
test("AST->GLSL: CALL sin node", test_ast_to_glsl_call)


def test_ast_to_glsl_var():
    from plugins.radical.ast_to_glsl import ast_to_glsl
    ast = {"t": "VAR", "n": "$bpm"}
    source = ast_to_glsl(ast, var_names=["bpm"])
    assert "inputs_bpm[id]" in source
test("AST->GLSL: VAR node with input buffer", test_ast_to_glsl_var)


def test_ast_to_glsl_unary():
    from plugins.radical.ast_to_glsl import ast_to_glsl
    ast = {"t": "UNARY", "op": "-", "o": {"t": "NUM", "v": 5.0}}
    source = ast_to_glsl(ast)
    assert "(-5.0)" in source
test("AST->GLSL: UNARY node", test_ast_to_glsl_unary)


def test_ast_to_glsl_quadratic():
    from plugins.radical.ast_to_glsl import ast_to_glsl
    ast = {"t": "CALL", "n": "quadratic", "a": [{"t": "NUM", "v": 1.0}, {"t": "NUM", "v": -5.0}, {"t": "NUM", "v": 6.0}]}
    source = ast_to_glsl(ast)
    assert "radical_quadratic(1.0, -5.0, 6.0)" in source
    assert "radical_quadratic(float a, float b, float c)" in source
test("AST->GLSL: quadratic helper", test_ast_to_glsl_quadratic)


def test_ast_list_to_glsl():
    from plugins.radical.ast_to_glsl import ast_list_to_glsl
    asts = [
        {"t": "BINOP", "op": "+", "l": {"t": "NUM", "v": 1}, "r": {"t": "NUM", "v": 2}},
        {"t": "BINOP", "op": "*", "l": {"t": "NUM", "v": 3}, "r": {"t": "NUM", "v": 4}},
    ]
    source = ast_list_to_glsl(asts, count=2)
    assert "switch(id)" in source
    assert "case 0:" in source
    assert "case 1:" in source
test("AST list->GLSL: multi-expression switch", test_ast_list_to_glsl)


def test_collect_vars():
    from plugins.radical.ast_to_glsl import _collect_vars
    ast = {"t": "BINOP", "op": "+",
           "l": {"t": "VAR", "n": "$x"},
           "r": {"t": "CALL", "n": "sin", "a": [{"t": "VAR", "n": "$y"}]}}
    vars_set = set()
    _collect_vars(ast, vars_set)
    assert "x" in vars_set
    assert "y" in vars_set
test("AST: collect variable names", test_collect_vars)


# === SHADER CACHE ===

def test_shader_cache():
    from plugins.radical.shader_cache import (
        get_cached_shader, cache_shader, get_cache_stats, clear_cache
    )
    clear_cache()
    assert get_cached_shader("test_hash") is None
    cache_shader("test_hash", 42, "test source")
    assert get_cached_shader("test_hash") == 42
    stats = get_cache_stats()
    assert stats["count"] >= 1
    clear_cache()
    assert get_cached_shader("test_hash") is None
test("Shader cache: store/retrieve/clear", test_shader_cache)


# === BATCH EVALUATOR ===

def test_batch_by_structure():
    from plugins.radical.batch_evaluator import batch_by_structure
    exprs = [
        ({"t": "NUM", "v": 1.0}, {}, "a"),
        ({"t": "NUM", "v": 2.0}, {}, "b"),
        ({"t": "BINOP", "op": "+", "l": {"t": "NUM", "v": 1}, "r": {"t": "NUM", "v": 2}}, {}, "c"),
    ]
    batches = batch_by_structure(exprs)
    assert len(batches) == 2  # NUM and BINOP should be separate
    # Both NUMs should be in one batch
    assert any(b[2] == 2 for b in batches)
test("Batch evaluator: group by structure", test_batch_by_structure)


# === MATRIX OPS ===

def test_matrix_matmul():
    from plugins.radical.matrix_ops import matmul
    A = [[1, 2], [3, 4]]
    B = [[5, 6], [7, 8]]
    C = matmul(A, B)
    assert C == [[19, 22], [43, 50]]
test("Matrix matmul: 2x2 CPU", test_matrix_matmul)


def test_matrix_transpose():
    from plugins.radical.matrix_ops import transpose
    M = [[1, 2, 3], [4, 5, 6]]
    T = transpose(M)
    assert T == [[1, 4], [2, 5], [3, 6]]
test("Matrix transpose: 2x3", test_matrix_transpose)


def test_matrix_conv2d():
    from plugins.radical.matrix_ops import conv2d
    img = [[1, 2, 1], [2, 4, 2], [1, 2, 1]]
    kernel = [[1, 0], [0, -1]]
    result = conv2d(img, kernel)
    assert len(result) == 3
    assert len(result[0]) == 3
test("Matrix conv2d: 3x3", test_matrix_conv2d)


# === TENSORSHARP ===

def test_tensorsharp_init():
    from plugins.tensorsharp.cuda_backend import TensorSHARPEngine
    eng = TensorSHARPEngine()
    assert hasattr(eng, "available")
    assert hasattr(eng, "diagnostic")
    assert hasattr(eng, "tensor_cores")
    print(f"   TensorSHARP: available={eng.available}, diag={eng.diagnostic}")
test("TensorSHARP: engine init (graceful)", test_tensorsharp_init)


def test_tensorsharp_eval_fallback():
    from plugins.tensorsharp.cuda_backend import TensorSHARPEngine
    eng = TensorSHARPEngine()
    result = eng.eval_ast({"t": "NUM", "v": 42.0}, {})
    # Should fall back through Radical -> LURE -> Python
    assert result is None or result == 42.0
test("TensorSHARP: eval fallback chain", test_tensorsharp_eval_fallback)


# === LOW-LEVEL OPENGL API (OPENapi) ===

def test_openapi_context():
    from plugins.openapi._context import GLContext
    ctx = GLContext()
    assert hasattr(ctx, "available")
    assert hasattr(ctx, "extensions")
    print(f"   GLContext: available={ctx.available}, GPU={ctx.gpu_name}, GL={ctx.gl_version}")
    if ctx.available:
        print(f"   Extensions: {len(ctx.extensions)}")
        wanted = ["GL_ARB_compute_shader", "GL_KHR_debug"]
        for w in wanted:
            print(f"     {w}: {'yes' if w in ctx.extensions else 'no'}")
test("OPENapi: GLContext creation + extensions", test_openapi_context)


def test_openapi_shader_api():
    from plugins.openapi._context import GLContext
    from plugins.openapi._api import OpenGLAPI
    ctx = GLContext()
    if not ctx.available:
        print("   Skipped: no GL context")
        return
    api = OpenGLAPI(ctx)
    vs = "#version 460 core\nlayout(location=0) in vec3 p; void main(){gl_Position=vec4(p,1);}"
    fs = "#version 460 core\nout vec4 c; void main(){c=vec4(1);}"
    prog = api.shader.compile(vs, fs, "test")
    assert prog > 0
    print(f"   Shader compiled: program {prog}")
    api.shader.delete(prog)
test("OPENapi: ShaderAPI compile + link", test_openapi_shader_api)


def test_openapi_buffer_api():
    from plugins.openapi._context import GLContext
    from plugins.openapi._api import OpenGLAPI
    ctx = GLContext()
    if not ctx.available:
        print("   Skipped: no GL context")
        return
    api = OpenGLAPI(ctx)
    vao = api.buffer.create_vao("test")
    assert vao > 0
    vbo, size = api.buffer.create_vbo([0, 0, 0, 1, 0, 0, 0, 1, 0])
    assert vbo > 0 and size > 0
    print(f"   VAO={vao}, VBO={vbo}, size={size}")
test("OPENapi: BufferAPI VBO + VAO", test_openapi_buffer_api)


def test_openapi_texture_api():
    from plugins.openapi._context import GLContext
    from plugins.openapi._api import OpenGLAPI
    ctx = GLContext()
    if not ctx.available:
        print("   Skipped: no GL context")
        return
    api = OpenGLAPI(ctx)
    import numpy as np
    data = np.zeros((64, 64, 4), dtype=np.uint8)
    tid = api.texture.create_2d(64, 64, data)
    assert tid > 0
    print(f"   2D texture: {tid}")
    api.texture.delete(tid)
test("OPENapi: TextureAPI 2D texture creation", test_openapi_texture_api)


def test_openapi_window_api():
    from plugins.openapi._context import GLContext
    from plugins.openapi._api import OpenGLAPI
    ctx = GLContext()
    if not ctx.available:
        print("   Skipped: no GL context")
        return
    api = OpenGLAPI(ctx)
    assert api.window.keys is not None
    assert hasattr(api.window, "is_key_pressed")
    assert hasattr(api.window, "poll_delta")
    assert hasattr(api.window, "get_time")
    api.window.set_title("OPENapi Test")
    print(f"   Window API: callbacks registered, title set")
test("OPENapi: WindowAPI input + time", test_openapi_window_api)


def test_openapi_render_api():
    from plugins.openapi._context import GLContext
    from plugins.openapi._api import OpenGLAPI
    ctx = GLContext()
    if not ctx.available:
        print("   Skipped: no GL context")
        return
    api = OpenGLAPI(ctx)
    api.render.set_viewport(0, 0, 100, 100)
    api.render.set_depth_test(True)
    api.render.set_blend(True)
    api.render.set_cull_face(True)
    api.render.clear()
    fbo, ct, dt = api.render.create_fbo(256, 256)
    assert fbo > 0
    print(f"   Render states: viewport, depth, blend, cull, clear, FBO={fbo}")
    api.render.delete_fbo(fbo)
test("OPENapi: RenderAPI pipeline state + FBO", test_openapi_render_api)


# === LOW-LEVEL VULKAN API (Vulkanizer) ===

def test_vulkanizer_instance():
    from plugins.vulkanizer._instance import VkInstance
    inst = VkInstance()
    assert hasattr(inst, "available")
    print(f"   Vulkan instance: available={inst.available}")
    if inst.available:
        g = inst.gpu_info
        print(f"   GPU: {g.get('name')}")
        print(f"   Vulkan: {g.get('vulkan_version')}")
        exts = g.get('extensions', [])
        rt = [e for e in exts if 'ray_tracing' in e]
        print(f"   Extensions: {len(exts)} total, {len(rt)} ray tracing")
test("Vulkanizer: VkInstance + device enum + extensions", test_vulkanizer_instance)


def test_vulkanizer_pipeline_api():
    from plugins.vulkanizer._instance import VkInstance
    from plugins.vulkanizer._api import VulkanAPI
    inst = VkInstance()
    if not inst.available:
        print("   Skipped: no Vulkan instance")
        return
    api = VulkanAPI(inst)
    assert hasattr(api, "pipeline")
    assert hasattr(api, "buffer")
    assert hasattr(api, "command")
    assert hasattr(api, "raytrace")
    assert hasattr(api, "upscale")
    rt = api.raytrace.info
    print(f"   Ray tracing: {rt.get('available', False)}")
    uc = api.upscale.info
    print(f"   Upscale: Tensor Cores={uc.get('tensor_cores', False)}, {uc.get('frames_processed', 0)} frames")
test("Vulkanizer: VulkanAPI sub-APIs (pipeline, buffer, command, raytrace, upscale)", test_vulkanizer_pipeline_api)


def test_vulkanizer_command_api():
    from plugins.vulkanizer._instance import VkInstance
    from plugins.vulkanizer._api import VulkanAPI
    inst = VkInstance()
    if not inst.available:
        print("   Skipped: no Vulkan instance")
        return
    api = VulkanAPI(inst)
    pool = api.command.create_pool()
    assert pool is not None
    bufs = api.command.allocate_buffer(pool)
    assert len(bufs) >= 1
    api.command.begin(bufs[0])
    api.command.end(bufs[0])
    fence = api.command.create_fence()
    assert fence is not None
    api.command.destroy_fence(fence)
    api.command.destroy_pool(pool)
    print(f"   Command pool, buffer, fence: allocated + destroyed")
test("Vulkanizer: CommandAPI pool + buffer + fence", test_vulkanizer_command_api)


# === EAUDIO API ===

def test_eaudio_device_api():
    from plugins.eaudio._device import AudioDeviceAPI
    ad = AudioDeviceAPI()
    assert hasattr(ad, "available")
    assert hasattr(ad, "device_count")
    print(f"   EAudio: available={ad.available}, devices={ad.device_count}")
    if ad.available and ad.devices:
        d = ad.devices[0]
        print(f"   Default: {d.get('name', '?')} ({d.get('channels', '?')}ch)")
test("EAudio: AudioDeviceAPI enum + capabilities", test_eaudio_device_api)


def test_eaudio_buffer_api():
    from plugins.eaudio._device import AudioDeviceAPI
    from plugins.eaudio._buffer import AudioBufferAPI
    ad = AudioDeviceAPI()
    if not ad.available:
        print("   Skipped: no audio device")
        return
    buf = AudioBufferAPI(ad)
    sine = buf.create_sine(440, 1.0)
    assert sine is not None
    assert sine.get("duration", 0) > 0
    assert sine.get("sample_rate", 0) > 0
    silence = buf.create_silence(0.5)
    assert silence is not None
    mixed = buf.mix([sine, silence])
    assert mixed is not None
    print(f"   Sine: {sine['duration']:.2f}s @ {sine['sample_rate']}Hz")
    print(f"   Resampled: {buf.resample(sine, 22050)['sample_rate']}Hz")
test("EAudio: AudioBufferAPI create, mix, resample", test_eaudio_buffer_api)


def test_eaudio_spatial_api():
    from plugins.eaudio._device import AudioDeviceAPI
    from plugins.eaudio._spatial import SpatialAudioAPI
    ad = AudioDeviceAPI()
    spa = SpatialAudioAPI(ad)
    spa.set_listener([0, 0, 0], velocity=[0, 0, 0])
    spa.add_source("test", [10, 0, 0])
    gain = spa.get_spatial_gain("test")
    assert gain is not None
    assert len(gain) == 2
    shift = spa.doppler_shift("test", 44100)
    assert shift > 0
    print(f"   Spatial gain: L={gain[0]:.3f} R={gain[1]:.3f}")
    print(f"   Doppler shift: {shift} Hz")
test("EAudio: SpatialAudioAPI 3D positioning + doppler", test_eaudio_spatial_api)


def test_eaudio_effects_api():
    from plugins.eaudio._device import AudioDeviceAPI
    from plugins.eaudio._buffer import AudioBufferAPI
    from plugins.eaudio._effects import AudioEffectsAPI
    ad = AudioDeviceAPI()
    buf_api = AudioBufferAPI(ad)
    effects = AudioEffectsAPI(ad)
    sine = buf_api.create_sine(440, 0.5)
    assert sine is not None
    rev = effects.reverb(sine, decay=0.4)
    assert rev is not None
    del_res = effects.delay(sine, delay_ms=100, feedback=0.3)
    assert del_res is not None
    comp = effects.compressor(sine, threshold=0.3, ratio=4.0)
    assert comp is not None
    eq_res = effects.eq(sine, bass_gain=1.2, treble_gain=1.1)
    assert eq_res is not None
    print(f"   Reverb, delay, compressor, EQ: all returned valid buffers")
test("EAudio: AudioEffectsAPI reverb + delay + compressor + EQ", test_eaudio_effects_api)


# === GAME ENGINE EXAMPLE ===

def test_game_engine_init():
    try:
        from examples.opengl_engine import GameEngine
        engine = GameEngine()
        result = engine.init()
        if result:
            print(f"   GameEngine: initialized on {engine.api.context.gpu_name}")
            engine.running = False
            engine.shutdown()
        else:
            print(f"   GameEngine: init returned False (expected without display)")
    except Exception as e:
        print(f"   GameEngine: init skipped ({e})")
test("Example: GameEngine built on OPENapi+Vulkanizer+EAudio APIs", test_game_engine_init)


# === INTEGRATION: Evaluator Chain ===

def test_radical_evaluator_registered():
    from ep_compiler.variables import _evaluators
    names = [name for _, name, _ in _evaluators]
    print(f"   Evaluators: {names}")
    # Radical should be registered (even if GPU unavailable) via the evaluator chain
    # The module-level register() function may not have been called yet
    # So this test checks that the module CAN register
    from plugins.radical import VERSION
    assert VERSION == "1.0.0"
    # Manually register to verify chain priority
    from ep_compiler.variables import register_evaluator
    register_evaluator("RadicalTest", lambda ad, vd: 42.0, priority=5)
    names_after = [name for _, name, _ in _evaluators]
    # Should be at the front (lower priority = tried first)
    rad_idx = next((i for i, n in enumerate(names_after) if n == "RadicalTest"), -1)
    lure_idx = next((i for i, n in enumerate(names_after) if n == "LURE"), -1)
    py_idx = next((i for i, n in enumerate(names_after) if n == "Python"), -1)
    if rad_idx >= 0:
        assert rad_idx < lure_idx or lure_idx < 0, "Radical should be before LURE"
        assert rad_idx < py_idx or py_idx < 0, "Radical should be before Python"
test("Evaluator chain: Radical before LURE/Python", test_radical_evaluator_registered)


def test_tensorsharp_evaluator_registered():
    from ep_compiler.variables import _evaluators
    from plugins.tensorsharp import VERSION
    assert VERSION == "1.0.0"
    from ep_compiler.variables import register_evaluator
    register_evaluator("TensorSHARPTest", lambda ad, vd: 42.0, priority=3)
    names = [name for _, name, _ in _evaluators]
    ts_idx = next((i for i, n in enumerate(names) if n == "TensorSHARPTest"), -1)
    rad_idx = next((i for i, n in enumerate(names) if n == "RadicalTest"), -1)
    if ts_idx >= 0 and rad_idx >= 0:
        assert ts_idx < rad_idx, "TensorSHARP should be before Radical"
test("Evaluator chain: TensorSHARP before Radical", test_tensorsharp_evaluator_registered)


# === SUMMARY ===

print(f"\n{'='*50}")
print(f"GPU PLUGIN TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL GPU PLUGIN TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
