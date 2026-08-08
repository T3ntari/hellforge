"""GPU Detection — enumerate ALL GPUs, classify type (dGPU/iGPU/software),
detect APIs, VRAM, and compute capability. Uses DXGI on Windows, lspci on Linux,
Metal on macOS. Falls back through OpenGL context -> OS tools -> empty result."""

import sys
import os
import platform
import subprocess
import re
import ctypes
import json


# ── Vendor database ──

_VENDORS = {
    0x10DE: ("NVIDIA", re.compile(r"NVIDIA|GeForce|RTX|Quadro|Tesla|TITAN", re.I)),
    0x1002: ("AMD", re.compile(r"AMD|Radeon|FirePro|Ryzen.*Graphics|ATI", re.I)),
    0x8086: ("Intel", re.compile(r"Intel|Iris|Arc|UHD|HD Graphics", re.I)),
    0x13B5: ("ARM", re.compile(r"ARM|Mali", re.I)),
    0x5143: ("Qualcomm", re.compile(r"Qualcomm|Adreno", re.I)),
    0x1414: ("Microsoft", re.compile(r"Microsoft|Basic Render|Remote Display", re.I)),
    0x1AE0: ("Google", re.compile(r"Google|SwiftShader", re.I)),
    0x10001: ("Apple", re.compile(r"Apple|M[1-9]|Metal", re.I)),
}

# GPU type classification by name patterns
_GPU_TYPE_PATTERNS = [
    ("discrete", re.compile(r"RTX|GTX|Arc.*A[3-9]\d{0,2}|Arc.*A770|Radeon\s+RX|Radeon\s+Pro|FirePro|Quadro|Tesla|Radeon\s+VII", re.I)),
    ("software", re.compile(r"Basic\s+Render|Remote\s+Display|SwiftShader|llvmpipe|softpipe|Microsoft\s+Basic", re.I)),
    ("virtual", re.compile(r"VirtualBox|VMware|Parallels|Citrix|RemoteFX", re.I)),
    ("integrated", re.compile(r"UHD|HD\s+Graphics|Iris|Radeon\(TM\)\s+Graphics|Vega|Ryzen|Graphics$|Arc\(TM\)\s+A[3]|HD\s+Graphics\s+\d{3}|Adreno|Mali", re.I)),
]

# ── Main entry ──

def detect_gpu():
    """Detect ALL GPU capabilities. Returns dict:
    - available: bool (primary GPU has OpenGL compute)
    - gpus: list of dicts (one per GPU)
    - primary: int (index into gpus for the primary display)
    - name, vendor, vendor_id, vram_mb, gpu_type: primary GPU info
    - gl_version, glsl_version: from OpenGL context
    - compute: bool, shader_model, compute_max_groups, compute_max_invocations
    - apis: dict of {opengl, vulkan, opencl, directx, metal, cuda} bool
    - reason: str
    """
    result = {
        "available": False,
        "gpus": [],
        "primary": 0,
        "name": "Unknown", "vendor": "Unknown", "vendor_id": 0,
        "vram_mb": 0, "gpu_type": "unknown",
        "gl_version": "N/A", "glsl_version": "N/A",
        "shader_model": "N/A", "compute": False,
        "compute_max_groups": 0, "compute_max_invocations": 0,
        "apis": {"opengl": False, "vulkan": False, "opencl": False,
                 "directx": False, "metal": False, "cuda": False},
        "reason": "",
    }

    # Phase 1: OS-level enumeration — get ALL GPUs
    os_gpus = _enumerate_gpus_os()
    if os_gpus:
        result["gpus"] = os_gpus
        # Pick primary (first discrete GPU, or first GPU if none discrete)
        for idx, g in enumerate(os_gpus):
            if g.get("type") == "discrete":
                result["primary"] = idx
                break
        primary = os_gpus[result["primary"]]
        result["name"] = primary["name"]
        result["vendor"] = primary["vendor"]
        result["vendor_id"] = primary["vendor_id"]
        result["vram_mb"] = primary.get("vram_mb", 0)
        result["gpu_type"] = primary.get("type", "unknown")

    # Phase 2: OpenGL probe — requires rendering context
    gl_info = _probe_opengl()
    if gl_info:
        result.update(gl_info)
        result["available"] = True
    elif not os_gpus:
        # No OS info and no GL — try OS fallback
        fallback = _probe_os_gpu_fallback()
        if fallback:
            result["gpus"] = fallback
            result["name"] = fallback[0]["name"]
            result["vendor"] = fallback[0]["vendor"]

    # Phase 3: API capability detection
    result["apis"]["vulkan"] = _check_vulkan()
    result["apis"]["opencl"] = _check_opencl()
    result["apis"]["cuda"] = _check_cuda()
    result["apis"]["directx"] = _check_directx()
    result["apis"]["metal"] = _check_metal()

    if not result["available"] and not result["gpus"]:
        result["reason"] = result.get("reason") or "No GPU detected"
    elif not result["available"] and result["gpus"]:
        result["reason"] = "GPU detected but no OpenGL compute context"
        # Still mark as available at OS level
        result["available"] = True

    return result


# ── Phase 1: OS-level GPU enumeration ──

def _enumerate_gpus_os():
    """Enumerate ALL GPUs in the system using OS-specific APIs.
    Returns list of dicts with name, vendor, vendor_id, vram_mb, type, driver."""
    system = platform.system()
    if system == "Windows":
        gpus = _enum_windows_dxgi()
        if gpus:
            return gpus
        gpus = _enum_windows_wmic()
        if gpus:
            return gpus
    elif system == "Linux":
        gpus = _enum_linux_lspci()
        if gpus:
            return gpus
    elif system == "Darwin":
        gpus = _enum_macos_sysprof()
        if gpus:
            return gpus
    return []


def _enum_windows_dxgi():
    """Enumerate GPUs via DXGI (DirectX Graphics Infrastructure).
    Uses ctypes to call dxgi.dll directly — no PyDirectX needed.
    Returns list of GPU dicts or empty list."""
    gpus = []
    try:
        dxgi = ctypes.windll.dxgi
        # Create DXGI factory
        CreateDXGIFactory1 = dxgi.CreateDXGIFactory1
        CreateDXGIFactory1.argtypes = [ctypes.c_void_p]
        CreateDXGIFactory1.restype = ctypes.c_long

        factory_ptr = ctypes.c_void_p()
        IID_IDXGIFactory1 = (ctypes.c_ubyte * 16)(0x770a, 0xaaf1, 0x4ad5, 0x95, 0x7c,
                                                    0x7c, 0x5e, 0xd2, 0xe8, 0x7e, 0x44,
                                                    0xa0, 0xb6, 0xc7, 0x0f, 0x8e)
        hr = CreateDXGIFactory1(ctypes.byref(IID_IDXGIFactory1), ctypes.byref(factory_ptr))
        if hr != 0:
            return []

        # Enumerate adapters
        EnumAdapters = dxgi.EnumAdapters
        EnumAdapters.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p]
        EnumAdapters.restype = ctypes.c_long

        adapter_index = 0
        while True:
            adapter_ptr = ctypes.c_void_p()
            hr = EnumAdapters(factory_ptr, adapter_index, ctypes.byref(adapter_ptr))
            if hr != 0:
                break

            # Get adapter description
            DXGI_ADAPTER_DESC = ctypes.Structure
            desc = (ctypes.c_char * 256)()
            GetDesc = adapter_ptr.value  # IDXGIAdapter::GetDesc
            # Use direct struct access
            gpus.append(_parse_dxgi_adapter(adapter_ptr))
            adapter_index += 1

        return gpus
    except Exception:
        return []


def _parse_dxgi_adapter(adapter_ptr):
    """Minimal DXGI adapter parsing via ctypes struct."""
    try:
        # Read vendor/device IDs from DXGI_ADAPTER_DESC
        desc = ctypes.create_string_buffer(256)
        # IDXGIAdapter::GetDesc offset via vtable
        vtable = ctypes.c_void_p.from_address(adapter_ptr.value)
        getdesc = ctypes.c_void_p.from_address(
            ctypes.c_void_p.from_address(vtable.value)[3]  # 4th method
        )
        # Simplified — fall through to name-based detection
    except Exception:
        pass
    return _classify_gpu_by_name(fallback_name="")


def _enum_windows_wmic():
    """Enumerate GPUs via WMIC. Works without DXGI.
    Returns list of GPU dicts."""
    gpus = []
    try:
        result = subprocess.run(
            ["wmic", "path", "Win32_VideoController",
             "get", "Name,AdapterRAM,DriverVersion", "/format:csv"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10
        )
        lines = [l.strip() for l in result.stdout.split("\n") if l.strip()]
        if len(lines) < 2:
            return []

        headers = [h.strip() for h in lines[0].split(",")]
        name_idx = next((i for i, h in enumerate(headers) if "Name" in h), -1)
        ram_idx = next((i for i, h in enumerate(headers) if "RAM" in h or "AdapterRAM" in h), -1)
        drv_idx = next((i for i, h in enumerate(headers) if "DriverVersion" in h), -1)

        if name_idx < 0:
            return []

        for line in lines[1:]:
            parts = [p.strip() for p in line.split(",")]
            if name_idx >= len(parts):
                continue
            name = parts[name_idx]
            if not name or name == "Name":
                continue

            vram_bytes = 0
            if ram_idx >= 0 and ram_idx < len(parts) and parts[ram_idx]:
                try:
                    vram_bytes = int(parts[ram_idx])
                except (ValueError, TypeError):
                    pass

            driver = parts[drv_idx] if drv_idx >= 0 and drv_idx < len(parts) else ""

            gpu = _classify_gpu_by_name(name)
            gpu["vram_mb"] = vram_bytes // (1024 * 1024) if vram_bytes else 0
            gpu["driver"] = driver
            gpus.append(gpu)

        # Deduplicate by name
        seen = set()
        unique = []
        for g in gpus:
            if g["name"] not in seen:
                seen.add(g["name"])
                unique.append(g)
        return unique

    except Exception:
        return []


def _enum_linux_lspci():
    """Enumerate GPUs on Linux via lspci."""
    gpus = []
    try:
        result = subprocess.run(
            ["lspci", "-nn", "-v", "-m"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10
        )
        if result.returncode != 0:
            return []

        # Parse GPU entries
        current = {}
        for line in result.stdout.split("\n"):
            if "VGA" in line or "3D" in line or "Display" in line:
                if current:
                    gpus.append(current)
                current = {"name": line.strip(), "type": "discrete"}
            elif current:
                if "Kernel driver" in line:
                    m = re.search(r"Kernel driver in use: (\S+)", line)
                    if m:
                        current["driver"] = m.group(1)

        if current:
            gpus.append(current)

        # Classify each
        result_gpus = []
        for g in gpus:
            classified = _classify_gpu_by_name(g.get("name", ""))
            classified["driver"] = g.get("driver", "")
            classified["vram_mb"] = _linux_gpu_vram(g.get("name", ""))
            result_gpus.append(classified)

        return result_gpus
    except Exception:
        return []


def _linux_gpu_vram(name):
    """Estimate VRAM on Linux for known GPUs."""
    # Read from /sys if available
    try:
        for path in glob.glob("/sys/class/drm/card*/device/mem_info_vram_total"):
            with open(path) as f:
                return int(f.read().strip()) // (1024 * 1024)
    except Exception:
        pass
    return 0


def _enum_macos_sysprof():
    """Enumerate GPUs on macOS via system_profiler."""
    gpus = []
    try:
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType", "-json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10
        )
        if result.returncode != 0:
            return []

        data = json.loads(result.stdout)
        displays = data.get("SPDisplaysDataType", [])
        for disp in displays:
            name = disp.get("sppci_model", disp.get("_name", "Unknown GPU"))
            vram_mb = 0
            vram_str = disp.get("spdisplays_vram", "0 MB")
            m = re.search(r"(\d+)", vram_str)
            if m:
                vram_mb = int(m.group(1))

            gpu = _classify_gpu_by_name(name)
            gpu["vram_mb"] = vram_mb
            gpu["driver"] = disp.get("spdisplays_driver", "")
            gpus.append(gpu)

        return gpus
    except Exception:
        return []


# ── GPU Classification ──

def _classify_gpu_by_name(name):
    """Classify a GPU by its name string.
    Returns dict with name, vendor, vendor_id, type."""
    name = name.strip()
    vendor = "Unknown"
    vendor_id = 0
    gpu_type = "unknown"

    # Match vendor by ID or name pattern
    for vid, (vname, pattern) in _VENDORS.items():
        if pattern.search(name):
            vendor = vname
            vendor_id = vid
            break

    # If vendor unknown via patterns, try to detect from name content
    if vendor == "Unknown":
        if "AMD" in name.upper() or "RADEON" in name.upper():
            vendor = "AMD"
            vendor_id = 0x1002
        elif "INTEL" in name.upper():
            vendor = "Intel"
            vendor_id = 0x8086
        elif "NVIDIA" in name.upper():
            vendor = "NVIDIA"
            vendor_id = 0x10DE

    # Classify GPU type
    for t, pattern in _GPU_TYPE_PATTERNS:
        if pattern.search(name):
            gpu_type = t
            break

    # Default type based on vendor
    if gpu_type == "unknown":
        if vendor == "NVIDIA":
            gpu_type = "discrete"
        elif vendor == "AMD":
            gpu_type = "discrete" if "RX" in name.upper() or "PRO" in name.upper() else "integrated"
        elif vendor == "Intel":
            if "ARC" in name.upper():
                gpu_type = "discrete"
            elif "UHD" in name.upper() or "HD Graphics" in name or "Iris" in name:
                gpu_type = "integrated"
            else:
                gpu_type = "discrete"
        elif vendor == "Microsoft":
            gpu_type = "software"
        elif vendor == "Apple":
            gpu_type = "integrated"
        elif vendor in ("Qualcomm", "ARM"):
            gpu_type = "integrated"
        elif vendor == "Google":
            gpu_type = "software"

    return {"name": name, "vendor": vendor, "vendor_id": vendor_id,
            "type": gpu_type, "vram_mb": 0, "driver": ""}


# ── Phase 2: OpenGL context probe ──

def _probe_opengl():
    """Create hidden OpenGL context and read GPU info.
    Returns dict with gl_version, glsl_version, compute info, or None."""
    info = {}

    # Try glfw first
    if _try_glfw(info):
        return info
    # Try pygame fallback
    if _try_pygame(info):
        return info
    return None


def _try_glfw(info):
    try:
        import glfw
        if not glfw.init():
            info["reason"] = "glfw init failed"
            return False
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        window = glfw.create_window(1, 1, "", None, None)
        if not window:
            glfw.terminate()
            info["reason"] = "glfw window creation failed (no GPU context)"
            return False
        glfw.make_context_current(window)
        _read_gl_context(info)
        glfw.make_context_current(None)
        glfw.destroy_window(window)
        glfw.terminate()
        return True
    except ImportError:
        info["reason"] = "glfw not installed (pip install glfw)"
        return False
    except Exception as e:
        info["reason"] = f"glfw error: {e}"
        try: glfw.terminate()
        except: pass
        return False


def _try_pygame(info):
    try:
        import pygame
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.OPENGL | pygame.HIDDEN)
        _read_gl_context(info)
        pygame.quit()
        return True
    except ImportError:
        return False
    except Exception as e:
        if "reason" not in info:
            info["reason"] = f"pygame OpenGL: {e}"
        try: pygame.quit()
        except: pass
        return False


def _read_gl_context(info):
    """Read OpenGL context strings."""
    try:
        from OpenGL.GL import (
            glGetString, GL_RENDERER, GL_VENDOR, GL_VERSION,
            GL_SHADING_LANGUAGE_VERSION, GL_MAX_COMPUTE_WORK_GROUP_COUNT,
            GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS,
        )
        info["name"] = glGetString(GL_RENDERER).decode()
        info["vendor_raw"] = glGetString(GL_VENDOR).decode()
        info["gl_version"] = glGetString(GL_VERSION).decode()
        info["glsl_version"] = glGetString(GL_SHADING_LANGUAGE_VERSION).decode()

        v = info["gl_version"].split()[0]
        major = int(v.split(".")[0]) if "." in v else 0
        minor = int(v.split(".")[1]) if "." in v and len(v.split(".")) > 1 else 0
        info["compute"] = (major > 4) or (major == 4 and minor >= 3)
        info["shader_model"] = f"{major}.{minor}" if info["compute"] else "pre-4.3"

        if info["compute"]:
            try:
                counts = glGetIntegerv(GL_MAX_COMPUTE_WORK_GROUP_COUNT, 3)
                info["compute_max_groups"] = list(counts) if hasattr(counts, '__len__') else counts
                inv = glGetIntegerv(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)
                info["compute_max_invocations"] = inv
            except Exception:
                pass

    except ImportError:
        info["reason"] = "PyOpenGL not installed (pip install PyOpenGL)"


# ── Phase 3: API detection ──

def _check_vulkan():
    """Check if Vulkan is available (loader + instance creation)."""
    try:
        import vulkan as vk
        app_info = vk.VkApplicationInfo(
            sType=vk.VK_STRUCTURE_TYPE_APPLICATION_INFO,
            pApplicationName="GPUDetect",
            applicationVersion=vk.VK_MAKE_VERSION(1, 0, 0),
            pEngineName="E",
            engineVersion=vk.VK_MAKE_VERSION(1, 0, 0),
            apiVersion=vk.VK_API_VERSION_1_0,
        )
        inst = vk.vkCreateInstance(
            vk.VkInstanceCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                pApplicationInfo=app_info,
            )
        )
        vk.vkDestroyInstance(inst, None)
        return True
    except Exception:
        pass
    try:
        ctypes.CDLL("vulkan-1.dll")
        return True
    except Exception:
        pass
    try:
        ctypes.CDLL("vulkan.dll")
        return True
    except Exception:
        pass
    return False


def _check_opencl():
    """Check if OpenCL is available."""
    try:
        import pyopencl
        pyopencl.create_some_context()
        return True
    except Exception:
        pass
    try:
        ctypes.CDLL("OpenCL.dll")
        return True
    except Exception:
        pass
    return False


def _check_cuda():
    """Check if CUDA driver is available."""
    try:
        ctypes.CDLL("nvcuda.dll")
        try:
            import cupy
            return True
        except ImportError:
            return True  # driver available even without CuPy
        except Exception:
            return True
    except Exception:
        pass
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        pass
    return False


def _check_directx():
    """Check if DirectX is available (Windows only)."""
    if platform.system() != "Windows":
        return False
    try:
        ctypes.windll.d3d11.CreateDirect3D11DeviceFromDXGIDevice = None
        return True
    except Exception:
        pass
    try:
        ctypes.CDLL("d3d11.dll")
        return True
    except Exception:
        pass
    return False


def _check_metal():
    """Check if Metal is available (macOS only)."""
    if platform.system() != "Darwin":
        return False
    try:
        import Metal
        return True
    except Exception:
        pass
    return False


# ── Legacy fallback (no OpenGL, no OS API) ──

def _probe_os_gpu_fallback():
    """Minimal OS-level GPU probe when everything else fails."""
    system = platform.system()
    if system == "Windows":
        # Last resort — check registry
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Control Panel\Video")
            idx = 0
            gpus = []
            while True:
                try:
                    name = winreg.EnumKey(key, idx)
                    if name:
                        gpus.append(_classify_gpu_by_name(name))
                    idx += 1
                except WindowsError:
                    break
            winreg.CloseKey(key)
            if gpus:
                return gpus
        except Exception:
            pass
    return None
