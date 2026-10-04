#!/usr/bin/env python3
"""Cut dead air and dropped takes, and remap word timings to output time.

    python3 autocut.py work/words.json -o work/cut.json [--max-gap 0.3] [--pad 0.06]
                       [--drop 12-30 --drop 55-58] [--start 3] [--end 140]

--drop takes word indices (inclusive, as printed by this script) to remove,
e.g. a fumbled first take. --start/--end are word indices that bound the reel.

Writes {"keep": [[s, e], ...] (source seconds), "words": [...] (output seconds)}
and prints the transcript with output timecodes and source indices so you can
plan shots against it.
"""
import argparse
import json


def parse_range(s):
    a, _, b = s.partition("-")
    return int(a), int(b or a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--max-gap", type=float, default=0.3,
                    help="silences longer than this are cut (seconds)")
    ap.add_argument("--pad", type=float, default=0.06,
                    help="audio kept before the first and after the last word of a run")
    ap.add_argument("--drop", action="append", default=[], type=parse_range)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None)
    a = ap.parse_args()

    words = json.load(open(a.words))
    dropped = set()
    for lo, hi in a.drop:
        dropped.update(range(lo, hi + 1))
    end = len(words) - 1 if a.end is None else a.end
    kept = [(i, w) for i, w in enumerate(words)
            if a.start <= i <= end and i not in dropped]
    if not kept:
        raise SystemExit("no words left after cuts")

    # Group consecutive kept words into runs; a run breaks on a long pause or a dropped word.
    runs = [[kept[0]]]
    for prev, cur in zip(kept, kept[1:]):
        if cur[0] != prev[0] + 1 or cur[1]["start"] - prev[1]["end"] > a.max_gap:
            runs.append([cur])
        else:
            runs[-1].append(cur)

    keep = []
    for r in runs:
        s = max(0.0, r[0][1]["start"] - a.pad)
        e = r[-1][1]["end"] + a.pad
        if keep and s <= keep[-1][1]:
            keep[-1][1] = max(keep[-1][1], e)
        else:
            keep.append([round(s, 3), round(e, 3)])

    out_words, offset = [], 0.0
    ri = 0
    for i, w in kept:
        while not (keep[ri][0] <= w["start"] < keep[ri][1] + 1e-6):
            offset += keep[ri][1] - keep[ri][0]
            ri += 1
        base = offset - keep[ri][0]
        out_words.append({"i": i, "w": w["w"],
                          "start": round(w["start"] + base, 3),
                          "end": round(min(w["end"], keep[ri][1]) + base, 3)})
    total = sum(e - s for s, e in keep)

    json.dump({"keep": keep, "words": out_words, "duration": round(total, 3)},
              open(a.out, "w"), indent=1, ensure_ascii=False)

    src = words[end]["end"] - words[a.start]["start"]
    print(f"{len(keep)} ranges, {src:.1f}s -> {total:.1f}s  ({a.out})\n")
    line, t0 = [], None
    for w in out_words:
        if t0 is None:
            t0 = w["start"]
        line.append(f'{w["w"]}[{w["i"]}]')
        if w["w"][-1:] in ".?!" or len(line) >= 10:
            print(f"{t0:6.2f}  " + " ".join(line))
            line, t0 = [], None
    if line:
        print(f"{t0:6.2f}  " + " ".join(line))


if __name__ == "__main__":
    main()
