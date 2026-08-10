"""Ninja shader builder — compiles every .comp in shaders/ to .spv.

glslang search order: $HELLFORGE_GLSLANG, then glslangValidator on PATH,
then /tmp/opencode/glslang/bin/glslangValidator. Exit 1 on any failure.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHADER_DIR = ROOT / "shaders"


def find_glslang():
    """Locate glslangValidator binary."""
    candidates = []
    env_path = os.environ.get("HELLFORGE_GLSLANG")
    if env_path:
        candidates.append(Path(env_path))
    found = shutil.which("glslangValidator")
    if found:
        candidates.append(Path(found))
    candidates.append(Path("/tmp/opencode/glslang/bin/glslangValidator"))
    for cand in candidates:
        if cand and cand.is_file():
            return cand
    return None


def main():
    glslang = find_glslang()
    if glslang is None:
        print("ERROR: glslangValidator not found "
              "(set HELLFORGE_GLSLANG or install Vulkan SDK)")
        return 1

    shaders = sorted(SHADER_DIR.glob("*.comp"))
    if not shaders:
        print(f"ERROR: no .comp shaders found in {SHADER_DIR}")
        return 1

    failed = 0
    for shader in shaders:
        spv = shader.with_suffix(".spv")
        cmd = [str(glslang), "-V", str(shader), "-o", str(spv)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True)
        except OSError as e:
            print(f"FAIL  {shader.name}: cannot run glslangValidator ({e})")
            failed += 1
            continue
        if r.returncode == 0:
            size = spv.stat().st_size if spv.exists() else 0
            print(f"SUCCESS {shader.name} -> {spv.name} ({size} bytes)")
        else:
            print(f"FAIL  {shader.name}")
            print(r.stdout)
            print(r.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
