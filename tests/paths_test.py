#!/usr/bin/env python3
"""HELLFORGE tests — smart path resolution, generate index/doc, eshell --project."""
import sys
import os
import tempfile
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

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


TMP = tempfile.mkdtemp(prefix="hf_paths_")


def make_tree():
    os.makedirs(os.path.join(TMP, "sub"), exist_ok=True)
    for fn in ("a.e", "b.e", "sub", "c.ei", "d.enx", "notes.txt"):
        if fn == "sub":
            with open(os.path.join(TMP, "sub", "deep.e"), "w") as f:
                f.write("@bpm 120\n")
        elif fn.endswith((".e", ".ei", ".enx")):
            with open(os.path.join(TMP, fn), "w") as f:
                f.write("@bpm 120\nT0 N60 D500 V80\n")


make_tree()


# === resolve_inputs ===

def test_relative_file():
    from ep_compiler.paths import resolve_inputs
    r = resolve_inputs(["a.e"], cwd=TMP)
    assert len(r) == 1 and r[0].endswith("a.e")
test("Paths: relative file", test_relative_file)


def test_absolute_file():
    from ep_compiler.paths import resolve_inputs
    abs_path = os.path.join(TMP, "b.e")
    r = resolve_inputs([abs_path])
    assert len(r) == 1 and r[0] == abs_path
test("Paths: absolute file", test_absolute_file)


def test_drive_letter_detection():
    from ep_compiler.paths import is_absolute
    assert is_absolute("D:/abc.e")
    assert is_absolute("C:\\abc.e")
    assert not is_absolute("abc.e")
    assert not is_absolute("samples/abc.e")
test("Paths: Windows drive-letter detection", test_drive_letter_detection)


def test_directory():
    from ep_compiler.paths import resolve_inputs
    r = resolve_inputs([TMP], recursive=False)
    names = sorted(os.path.basename(p) for p in r)
    assert names == ["a.e", "b.e", "c.ei", "d.enx"], names
test("Paths: directory (non-recursive)", test_directory)


def test_directory_recursive():
    from ep_compiler.paths import resolve_inputs
    r = resolve_inputs([TMP], recursive=True)
    names = sorted(os.path.basename(p) for p in r)
    assert "deep.e" in names, names
test("Paths: directory (recursive)", test_directory_recursive)


def test_slash_wildcard():
    from ep_compiler.paths import resolve_inputs
    r = resolve_inputs(["/"], cwd=TMP)
    assert len(r) >= 4
test("Paths: '/' wildcard (cwd)", test_slash_wildcard)


def test_glob():
    from ep_compiler.paths import resolve_inputs
    r = resolve_inputs(["**/*.e"], cwd=TMP, recursive=True)
    assert len(r) >= 3, r
test("Paths: glob pattern", test_glob)


def test_multiple_specs():
    from ep_compiler.paths import resolve_inputs
    r = resolve_inputs(["a.e", os.path.join(TMP, "sub")], cwd=TMP)
    names = sorted(os.path.basename(p) for p in r)
    assert names == ["a.e", "deep.e"], names
test("Paths: multiple specs, dedup", test_multiple_specs)


def test_batch_suffix():
    from ep_compiler.paths import batch_suffix
    assert batch_suffix("song.e", "v3") == os.path.join("song_v3.e")
    assert batch_suffix(os.path.join("x", "a.eic"), "v4") == os.path.join("x", "a_v4.eic")
test("Paths: batch_suffix naming", test_batch_suffix)


# === generate index ===

def test_generate_index_v4():
    from eshell import _generate_index
    cwd = os.getcwd()
    work = os.path.join(TMP, "idxv4")
    os.makedirs(work, exist_ok=True)
    for fn in ("01_intro.e", "02_main.e"):
        with open(os.path.join(work, fn), "w") as f:
            f.write("@bpm 120\nT0 N60 D500 V80\n")
    try:
        os.chdir(work)
        _generate_index([])
        assert os.path.exists("index.ei")
        with open("index.ei") as f:
            content = f.read()
        assert 'inherit "01_intro.e"' in content
        assert 'inherit "02_main.e"' in content
        assert "v4" in content
    finally:
        os.chdir(cwd)
test("Generate: index.ei (v4 default)", test_generate_index_v4)


# === generate doc ===

def test_generate_doc():
    from eshell import _generate_doc
    cwd = os.getcwd()
    out_dir = os.path.join(TMP, "hdoc_out")
    try:
        os.chdir(TMP)
        _generate_doc(["-o", out_dir])
        assert os.path.isdir(out_dir)
        assert os.path.isdir(os.path.join(out_dir, "doc"))
        assert os.path.isdir(os.path.join(out_dir, "samples"))
        assert os.path.isdir(os.path.join(out_dir, "examples"))
        assert os.path.isfile(os.path.join(out_dir, "SYNTAX.md"))
    finally:
        os.chdir(cwd)
test("Generate: hdoc/ with doc+samples+examples+SYNTAX.md", test_generate_doc)


# === eshell --project ===

def test_eshell_project_flag():
    import eshell as es  # noqa: F401  (module must import cleanly)
    # Pipe "exit" so the REPL terminates; give plugin boot time
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "eshell.py"), "--project", TMP],
        input="exit\n", capture_output=True, text=True, timeout=120,
        encoding="utf-8", errors="replace",
    )
    # Boot may log warnings; exit code 0 means it started and exited cleanly
    assert r.returncode == 0, r.stderr[-400:]
test("eshell: --project flag starts without error", test_eshell_project_flag)


def test_paths_module_importable():
    import ep_compiler.paths as p
    assert hasattr(p, "resolve_inputs") and hasattr(p, "batch_suffix")
test("Paths: module importable", test_paths_module_importable)


print(f"\n{'='*50}")
print(f"PATHS/GENERATE TESTS: {passed}/{passed+failed} passed")
shutil.rmtree(TMP, ignore_errors=True)
if failed == 0:
    print("ALL PATH & GENERATE TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
