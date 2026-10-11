#!/usr/bin/env python3
"""Person matte for a video: white = person, black = background.

    python3 matte.py presenter.mov -o work/matte.mp4 [--model multiclass|fast]

The matte has the same size, frame rate and frame count as the input, so it
lines up frame-for-frame with it in ffmpeg (alphamerge). Used for text behind
the head and for putting the presenter in front of graphics.

Needs `pip install mediapipe numpy`. The model downloads once from
storage.googleapis.com into ~/.cache/reel-editor.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

MODELS = {
    # Separates hair, skin and clothes; cleaner edges, ~4x slower.
    "multiclass": "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
                  "selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite",
    "fast": "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
            "selfie_segmenter/float16/latest/selfie_segmenter.tflite",
}
WORK_W = 540  # inference/processing width; the matte is upscaled after


def model_path(name):
    cache = os.path.expanduser("~/.cache/reel-editor")
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, os.path.basename(MODELS[name]))
    if not os.path.exists(path):
        print(f"downloading {name} segmentation model ...")
        urllib.request.urlretrieve(MODELS[name], path + ".part")
        os.replace(path + ".part", path)
    return path


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"], s["r_frame_rate"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--model", choices=list(MODELS), default="multiclass")
    ap.add_argument("--smooth", type=float, default=0.5,
                    help="temporal smoothing 0-0.9; higher = steadier edges, more lag")
    a = ap.parse_args()

    try:
        import numpy as np
        import mediapipe as mp
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import ImageSegmenter, ImageSegmenterOptions
    except ImportError:
        sys.exit("needs: pip install mediapipe numpy")

    W, H, rate = probe(a.video)
    w = WORK_W
    h = int(round(H * w / W / 2)) * 2
    seg = ImageSegmenter.create_from_options(ImageSegmenterOptions(
        base_options=BaseOptions(model_asset_path=model_path(a.model)),
        output_confidence_masks=True))

    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.video, "-vf", f"scale={w}:{h}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    # Upscale, then a light blur so the edge is soft rather than stair-stepped.
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
                            "-s", f"{w}x{h}", "-r", rate, "-i", "-",
                            "-vf", f"scale={W}:{H}:flags=bicubic,gblur=sigma=2,format=gray",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "12",
                            "-pix_fmt", "yuv420p", a.out], stdin=subprocess.PIPE)
    prev, n = None, 0
    frame_bytes = w * h * 3
    while True:
        buf = dec.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        img = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        res = seg.segment(mp.Image(image_format=mp.ImageFormat.SRGB, data=img))
        masks = res.confidence_masks
        # multiclass: index 0 is background; fast: single person mask.
        person = 1.0 - masks[0].numpy_view() if len(masks) > 1 else masks[0].numpy_view()
        person = np.squeeze(person).astype(np.float32)
        if prev is not None:
            person = a.smooth * prev + (1 - a.smooth) * person
        prev = person
        # Steepen the soft edge so hair keeps detail without a halo.
        m = np.clip((person - 0.35) / 0.3, 0, 1)
        enc.stdin.write((m * 255).astype(np.uint8).tobytes())
        n += 1
    seg.close()
    enc.stdin.close()
    enc.wait()
    dec.wait()
    print(f"{n} frames -> {a.out}")


if __name__ == "__main__":
    main()
