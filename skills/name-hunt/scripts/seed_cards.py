#!/usr/bin/env python3
"""Turn a round of candidate cards into ArtifactData batch writes for the swipe page.

Usage:
  python3 seed_cards.py ROUND cards.tsv [com.out] [au.out] [--out DIR]

cards.tsv  one card per line, tab-separated:
           slug  Name  Style  say-it  how-it's-made  why-it-fits
com.out    optional: output of rdap.py for the .com names (sets "com")
au.out     optional: output of rdap.py for the ccTLD names (sets "comau")

Writes one JSON file per card into DIR (default: seed<ROUND>/), then prints
the batch `writes` arrays (max 50 each, separated by a line "SPLIT") to pass
to ArtifactData action "batch". Styles are interleaved so the deck mixes.
A domain that wasn't checked is "unchecked", never assumed.
"""
import json, os, sys


def statuses(path):
    out = {}
    if not path or not os.path.exists(path):
        return out
    for line in open(path):
        p = line.split()
        if len(p) < 2:
            continue
        slug = p[0].split(".")[0]
        out[slug] = "available" if p[1] == "AVAILABLE" else "taken" if p[1] == "TAKEN" else "unchecked"
    return out


def main(argv):
    out_dir = None
    if "--out" in argv:
        i = argv.index("--out"); out_dir = argv[i + 1]; argv = argv[:i] + argv[i + 2:]
    if len(argv) < 2:
        sys.exit(__doc__)
    rnd, cards = int(argv[0]), argv[1]
    com = statuses(argv[2] if len(argv) > 2 else None)
    au = statuses(argv[3] if len(argv) > 3 else None)
    rows = [l.rstrip("\n").split("\t") for l in open(cards) if l.strip()]
    for r in rows:
        if len(r) != 6:
            sys.exit(f"expected 6 tab-separated fields, got {len(r)}: {r[:2]}")
    by = {}
    for r in rows:
        by.setdefault(r[2], []).append(r)
    order = []
    while any(by.values()):
        for k in list(by):
            if by[k]:
                order.append(by[k].pop(0))
    out_dir = os.path.abspath(out_dir or f"seed{rnd}")
    os.makedirs(out_dir, exist_ok=True)
    writes = []
    for n, (slug, name, style, say, made, why) in enumerate(order):
        d = dict(name=name, slug=slug, style=style, say=say, made=made, why=why,
                 com=com.get(slug, "unchecked"), comau=au.get(slug, "unchecked"),
                 round=rnd, order=rnd * 100 + n)
        p = os.path.join(out_dir, f"{slug}.json")
        json.dump(d, open(p, "w"))
        writes.append({"op": "set", "collection": "names", "doc_id": slug, "file_path": p})
    for i in range(0, len(writes), 50):
        if i:
            print("SPLIT")
        print(json.dumps(writes[i:i + 50]))


if __name__ == "__main__":
    main(sys.argv[1:])
