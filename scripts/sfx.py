#!/usr/bin/env python3
"""Synthesized sound effects and the sound-effect track for a reel.

    python3 sfx.py --export assets/sfx     # write the built-in sounds as .wav files

Built-in sounds: whoosh, pop, ding, boom, click, riser. They are simple
synthesized stand-ins. A library sound (Epidemic Sound, CapCut, Pixabay)
always sounds better; pass a file path instead of a name to use one.
"""
import argparse
import os
import subprocess
import wave

import numpy as np

SR = 48000


def _env(n, attack, release):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    r = np.exp(-t / max(release, 1e-4))
    return a * r


def _lowpass_sweep(x, f0, f1):
    """One-pole lowpass whose cutoff moves from f0 to f1 over the clip."""
    n = len(x)
    fc = np.geomspace(f0, f1, n)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty(n)
    acc = 0.0
    for i in range(n):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def _stereo(m, pan_from=0.0, pan_to=0.0):
    p = np.linspace(pan_from, pan_to, len(m))
    left = m * np.cos((p + 1) * np.pi / 4)
    right = m * np.sin((p + 1) * np.pi / 4)
    return np.stack([left, right], 1)


def whoosh(dur=0.45, seed=0):
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    t = np.linspace(0, 1, n)
    body = _lowpass_sweep(noise, 400, 5000) - 0.6 * _lowpass_sweep(noise, 150, 300)
    shape = np.sin(np.pi * t) ** 1.6 * (0.4 + 0.6 * t)
    m = body * shape
    return _stereo(m / (np.abs(m).max() + 1e-9) * 0.8, -0.6, 0.6)


def pop(dur=0.12):
    t = np.arange(int(dur * SR)) / SR
    m = np.sin(2 * np.pi * (700 * t - 2200 * t * t)) * np.exp(-38 * t)
    return _stereo(m * 0.9)


def ding(dur=1.1):
    t = np.arange(int(dur * SR)) / SR
    m = (0.55 * np.sin(2 * np.pi * 1568 * t) * np.exp(-5 * t)
         + 0.25 * np.sin(2 * np.pi * 3136 * t) * np.exp(-8 * t)
         + 0.12 * np.sin(2 * np.pi * 4704 * t) * np.exp(-12 * t))
    m *= np.clip(t / 0.003, 0, 1)
    return _stereo(m)


def boom(dur=1.3, seed=1):
    t = np.arange(int(dur * SR)) / SR
    f = 62 * np.exp(-1.2 * t) + 30
    m = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-3.2 * t)
    hit = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-60 * t) * 0.3
    return _stereo((m + hit) * 0.9)


def click(seed=0):
    rng = np.random.default_rng(seed)
    n = int(0.03 * SR)
    x = rng.standard_normal(n) * _env(n, 0.0005, 0.004)
    x = x - _lowpass_sweep(x, 1500, 1500)  # keep the bright part
    return _stereo(x / (np.abs(x).max() + 1e-9) * (0.5 + 0.3 * rng.random()))


def riser(dur=1.2, seed=2):
    n = int(dur * SR)
    noise = np.random.default_rng(seed).standard_normal(n)
    t = np.linspace(0, 1, n)
    m = _lowpass_sweep(noise, 300, 9000) * t ** 2
    return _stereo(m / (np.abs(m).max() + 1e-9) * 0.7)


BUILTIN = {"whoosh": whoosh, "pop": pop, "ding": ding, "boom": boom, "click": click,
           "riser": riser}


def load(name_or_path, seed=0):
    if name_or_path in BUILTIN:
        fn = BUILTIN[name_or_path]
        return fn(seed=seed) if "seed" in fn.__code__.co_varnames else fn()
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", name_or_path, "-ac", "2",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True,
                         check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def build_track(events, duration, path):
    """events: [{"sound": name-or-path, "at": seconds, "volume": 0-1}] -> stereo wav."""
    out = np.zeros((int(duration * SR) + SR, 2))
    for i, e in enumerate(events):
        x = load(e["sound"], seed=i) * e.get("volume", 0.5)
        if "end" in e:  # trim long library sounds to their slot
            x = x[:max(1, int((e["end"] - e["at"]) * SR))]
        s = int(max(0.0, e["at"]) * SR)
        x = x[:max(0, len(out) - s)]
        out[s:s + len(x)] += x
    write_wav(path, out[:int(duration * SR)])
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True, help="folder to write the built-in sounds")
    a = ap.parse_args()
    os.makedirs(a.export, exist_ok=True)
    for name in BUILTIN:
        write_wav(os.path.join(a.export, name + ".wav"), load(name))
    print(f"wrote {len(BUILTIN)} sounds to {a.export}")


if __name__ == "__main__":
    main()
