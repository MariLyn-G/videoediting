#!/usr/bin/env python3
"""Check the CapCut setup on this computer and drop a test draft into CapCut.

    python3 capcut/selftest.py

Prints what it checks. At the end, open CapCut: a project called
"reel_editor_test" should be on the home screen.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))


def step(msg):
    print(f"- {msg}", flush=True)


def fail(msg):
    print(f"\nFAILED: {msg}")
    sys.exit(1)


step(f"python {sys.version.split()[0]} at {sys.executable}")
if sys.version_info < (3, 9):
    fail("Python 3.9 or newer is needed")

for tool in ("ffmpeg", "ffprobe"):
    if not shutil.which(tool):
        fail(f"{tool} not found. Install it with: brew install ffmpeg")
step("ffmpeg found")

try:
    import pyJianYingDraft  # noqa: F401
    import mcp  # noqa: F401
except ImportError as e:
    fail(f"{e.name} is not installed. Run: pip install -r capcut/requirements.txt "
         "(with the .venv activated)")
step("python packages installed")

from capcut.draft import Draft, default_drafts_dir  # noqa: E402

drafts = default_drafts_dir()
if not drafts:
    fail("CapCut's drafts folder was not found. Open CapCut once, or set "
         "CAPCUT_DRAFTS_DIR to the folder shown in CapCut > Settings > Drafts")
step(f"CapCut drafts folder: {drafts}")

tmp = tempfile.mkdtemp()
clip = os.path.join(tmp, "test_clip.mp4")
r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc2=s=1080x1920:r=30:d=5", "-f", "lavfi", "-i", "sine=f=330:d=5",
                    "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", clip])
if r.returncode:
    fail("ffmpeg could not make the test clip")
step("made a 5-second test clip")

d = Draft("reel_editor_test")
d.add_video(clip, start=0, end=5)
d.add_text("It works", 0.5, 3.0, y=0.25, size_px=110, color="#f3d46a", bold=True, shadow=True)
out = d.save(drafts)
step(f"saved draft: {out}")
print("\nDONE. Now open CapCut (or go back to its home screen) and look for "
      "\"reel_editor_test\". Tell Claude whether it opens and shows the clip and the "
      "yellow text \"It works\", and your CapCut version (CapCut > About CapCut).")
