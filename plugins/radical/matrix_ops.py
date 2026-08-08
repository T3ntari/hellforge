"""Matrix Operations — shader-core matrix multiply, transpose, convolution.
Used by Tensorsharp for Tensor Core operations.
Falls back to CPU numpy if GPU unavailable."""

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False


def matmul(A, B, engine=None):
    """Matrix multiply A @ B.
    engine: optional RadicalEngine for GPU dispatch.
    Returns numpy array or list of lists."""
    if engine and engine.available:
        try:
            return _gpu_matmul(A, B, engine)
        except Exception:
            pass
    if _HAS_NUMPY:
        return np.dot(np.array(A), np.array(B)).tolist()
    return _cpu_matmul(A, B)


def transpose(M, engine=None):
    """Matrix transpose."""
    if _HAS_NUMPY:
        return np.array(M).T.tolist()
    return [list(col) for col in zip(*M)]


def conv2d(image, kernel, engine=None):
    """2D convolution. image and kernel are 2D lists."""
    if engine and engine.available:
        try:
            return _gpu_conv2d(image, kernel, engine)
        except Exception:
            pass
    if _HAS_NUMPY:
        from scipy import signal
        img_a = np.asarray(image, dtype=float)
        ker_a = np.asarray(kernel, dtype=float)
        ph, pw = ker_a.shape[0] // 2, ker_a.shape[1] // 2
        padded = np.pad(img_a, ((ph, ph), (pw, pw)))
        full = signal.correlate2d(padded, ker_a, mode="valid")
        return full[:img_a.shape[0], :img_a.shape[1]].tolist()
    return _cpu_conv2d(image, kernel)


def _gpu_matmul(A, B, engine):
    """GPU matrix multiply via compute shader."""
    import ctypes
    from OpenGL.GL import (
        glUseProgram, glGenBuffers, glBindBuffer, glBufferData,
        glGetBufferSubData, glDispatchCompute, glMemoryBarrier,
        glFinish, glBindBufferBase, glDeleteBuffers,
        GL_SHADER_STORAGE_BUFFER, GL_ALL_BARRIER_BITS,
    )

    A = np.array(A, dtype=np.float32)
    B = np.array(B, dtype=np.float32)
    M, K = A.shape
    K2, N = B.shape
    assert K == K2, f"Matrix dim mismatch: {K} vs {K2}"

    source = _MATMUL_GLSL.format(M=M, N=N, K=K)
    from .shader_compiler import compile_glsl
    program, err = compile_glsl(source)
    if program is None:
        return _cpu_matmul(A.tolist(), B.tolist())

    glUseProgram(program)

    # Buffers
    buf_A = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_A)
    glBufferData(GL_SHADER_STORAGE_BUFFER, A.nbytes, A.ctypes.data, GL_MAP_READ_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, buf_A)

    buf_B = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_B)
    glBufferData(GL_SHADER_STORAGE_BUFFER, B.nbytes, B.ctypes.data, GL_MAP_READ_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, buf_B)

    C = np.zeros((M, N), dtype=np.float32)
    buf_C = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_C)
    glBufferData(GL_SHADER_STORAGE_BUFFER, C.nbytes, None, GL_MAP_READ_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, buf_C)

    # Dispatch
    groups_x = (M + 7) // 8
    groups_y = (N + 7) // 8
    glDispatchCompute(groups_x, groups_y, 1)
    glMemoryBarrier(GL_ALL_BARRIER_BITS)
    glFinish()

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_C)
    glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, C.nbytes, C.ctypes.data)

    for b in (buf_A, buf_B, buf_C):
        glDeleteBuffers(1, [b])

    return C.tolist()


_MATMUL_GLSL = """#version 430 core
layout(local_size_x = 8, local_size_y = 8) in;

layout(std430, binding = 0) buffer A {{ float a[]; }};
layout(std430, binding = 1) buffer B {{ float b[]; }};
layout(std430, binding = 2) buffer C {{ float c[]; }};

void main() {{
    uint row = gl_GlobalInvocationID.x;
    uint col = gl_GlobalInvocationID.y;
    if (row >= {M} || col >= {N}) return;
    float sum = 0.0;
    for (uint k = 0; k < {K}; k++) {{
        sum += a[row * {K} + k] * b[k * {N} + col];
    }}
    c[row * {N} + col] = sum;
}}
"""


_CONV2D_GLSL = """#version 430 core
layout(local_size_x = 8, local_size_y = 8) in;

layout(std430, binding = 0) buffer Img {{ float img[]; }};
layout(std430, binding = 1) buffer Ker {{ float ker[]; }};
layout(std430, binding = 2) buffer Out {{ float out[]; }};

void main() {{
    uint x = gl_GlobalInvocationID.x;
    uint y = gl_GlobalInvocationID.y;
    if (x >= {W} || y >= {H}) return;
    float s = 0.0;
    for (uint ki = 0; ki < {KH}; ki++) {{
        int ii = int(y) + int(ki) - {PH};
        for (uint kj = 0; kj < {KW}; kj++) {{
            int jj = int(x) + int(kj) - {PW};
            if (ii >= 0 && ii < {H} && jj >= 0 && jj < {W}) {{
                s += img[ii * {W} + jj] * ker[ki * {KW} + kj];
            }}
        }}
    }}
    out[y * {W} + x] = s;
}}
"""


def _gpu_conv2d(image, kernel, engine):
    """GPU 2D convolution via compute shader (same-shape zero-padded)."""
    import ctypes
    from OpenGL.GL import (
        glUseProgram, glGenBuffers, glBindBuffer, glBufferData,
        glGetBufferSubData, glDispatchCompute, glMemoryBarrier,
        glFinish, glBindBufferBase, glDeleteBuffers,
        GL_SHADER_STORAGE_BUFFER, GL_ALL_BARRIER_BITS,
    )

    image = np.array(image, dtype=np.float32)
    kernel = np.array(kernel, dtype=np.float32)
    H, W = image.shape
    KH, KW = kernel.shape
    pad_h, pad_w = KH // 2, KW // 2

    source = _CONV2D_GLSL.format(H=H, W=W, KH=KH, KW=KW, PH=pad_h, PW=pad_w)
    from .shader_compiler import compile_glsl
    program, err = compile_glsl(source)
    if program is None:
        return _cpu_conv2d(image.tolist(), kernel.tolist())

    glUseProgram(program)

    buf_img = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_img)
    glBufferData(GL_SHADER_STORAGE_BUFFER, image.nbytes, image.ctypes.data, GL_MAP_READ_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, buf_img)

    buf_ker = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_ker)
    glBufferData(GL_SHADER_STORAGE_BUFFER, kernel.nbytes, kernel.ctypes.data, GL_MAP_READ_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1, buf_ker)

    out = np.zeros((H, W), dtype=np.float32)
    buf_out = glGenBuffers(1)
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_out)
    glBufferData(GL_SHADER_STORAGE_BUFFER, out.nbytes, None, GL_MAP_READ_BIT)
    glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 2, buf_out)

    glDispatchCompute((W + 7) // 8, (H + 7) // 8, 1)
    glMemoryBarrier(GL_ALL_BARRIER_BITS)
    glFinish()

    glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf_out)
    glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, out.nbytes, out.ctypes.data)

    for b in (buf_img, buf_ker, buf_out):
        glDeleteBuffers(1, [b])

    return out.tolist()


def _cpu_matmul(A, B):
    """Pure Python matrix multiply."""
    M = len(A)
    N = len(B[0]) if B else 0
    K = len(A[0]) if A else 0
    result = [[0.0] * N for _ in range(M)]
    for i in range(M):
        for j in range(N):
            s = 0.0
            for k in range(K):
                s += A[i][k] * B[k][j]
            result[i][j] = s
    return result


def _cpu_conv2d(image, kernel):
    """Pure Python 2D convolution."""
    H, W = len(image), len(image[0])
    KH, KW = len(kernel), len(kernel[0])
    pad_h, pad_w = KH // 2, KW // 2
    result = [[0.0] * W for _ in range(H)]

    for i in range(H):
        for j in range(W):
            s = 0.0
            for ki in range(KH):
                for kj in range(KW):
                    ii = i + ki - pad_h
                    jj = j + kj - pad_w
                    if 0 <= ii < H and 0 <= jj < W:
                        s += image[ii][jj] * kernel[ki][kj]
            result[i][j] = s
    return result
